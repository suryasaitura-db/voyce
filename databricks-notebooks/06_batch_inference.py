# Databricks notebook source
# MAGIC %md
# MAGIC # Batch Inference Pipeline
# MAGIC
# MAGIC This notebook handles:
# MAGIC - Batch prediction using trained models
# MAGIC - Cost-optimized inference scheduling
# MAGIC - Model serving and inference
# MAGIC - Prediction monitoring and validation
# MAGIC - A/B testing between models

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration and Imports

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable

import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import uuid

# COMMAND ----------

# Configuration
CATALOG_NAME = "voice_feedback_prod"
RAW_DATA_SCHEMA = "raw_data"
PROCESSED_SCHEMA = "processed_data"
ML_SCHEMA = "ml_models"

# Batch settings
BATCH_SIZE = 1000
INFERENCE_THRESHOLD_HOURS = 24  # Only predict on records without predictions in last 24h

print(f"Catalog: {CATALOG_NAME}")
print(f"Batch size: {BATCH_SIZE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Production Model

# COMMAND ----------

# Get production model from registry
production_model_df = spark.sql(f"""
    SELECT
        model_id,
        model_name,
        model_version,
        model_type,
        mlflow_run_id,
        mlflow_model_uri,
        metrics,
        created_at
    FROM {CATALOG_NAME}.{ML_SCHEMA}.model_registry
    WHERE stage = 'Production'
    ORDER BY created_at DESC
    LIMIT 1
""")

if production_model_df.count() == 0:
    raise Exception("No production model found in registry")

production_model_info = production_model_df.collect()[0]

print(f"Production Model:")
print(f"  Name: {production_model_info['model_name']}")
print(f"  Version: {production_model_info['model_version']}")
print(f"  Type: {production_model_info['model_type']}")
print(f"  Run ID: {production_model_info['mlflow_run_id']}")

# Load model from MLflow
production_model = mlflow.sklearn.load_model(production_model_info['mlflow_model_uri'])
print(f"\n✓ Loaded production model")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare Feature Engineering Functions

# COMMAND ----------

def extract_features_from_row(row):
    """Extract features from a single row for prediction"""

    # Feature columns (must match training features)
    feature_columns = [
        'word_count', 'sentence_count', 'avg_word_length', 'unique_word_count',
        'text_length', 'unique_word_ratio', 'topic_count', 'key_phrase_count',
        'duration_seconds', 'avg_volume', 'max_volume', 'silence_ratio',
        'speech_rate', 'pitch_mean', 'pitch_std', 'energy_mean', 'energy_std'
    ]

    # Add MFCC features
    feature_columns.extend([f'mfcc_{i}' for i in range(13)])

    # Add spectral features
    feature_columns.extend([
        'spectral_centroid_mean', 'spectral_centroid_std',
        'spectral_rolloff_mean', 'spectral_rolloff_std',
        'spectral_bandwidth_mean', 'spectral_bandwidth_std'
    ])

    features = {}

    # Text features
    features['word_count'] = row['word_count'] or 0
    features['sentence_count'] = row['sentence_count'] or 0
    features['avg_word_length'] = row['avg_word_length'] or 0
    features['unique_word_count'] = row['unique_word_count'] or 0
    features['text_length'] = len(row['transcription_text']) if row['transcription_text'] else 0
    features['unique_word_ratio'] = features['unique_word_count'] / max(features['word_count'], 1)
    features['topic_count'] = len(row['topics']) if row['topics'] else 0
    features['key_phrase_count'] = len(row['key_phrases']) if row['key_phrases'] else 0

    # Audio features
    features['duration_seconds'] = row['duration_seconds'] or 0
    features['avg_volume'] = row['avg_volume'] or 0
    features['max_volume'] = row['max_volume'] or 0
    features['silence_ratio'] = row['silence_ratio'] or 0
    features['speech_rate'] = row['speech_rate'] or 0
    features['pitch_mean'] = row['pitch_mean'] or 0
    features['pitch_std'] = row['pitch_std'] or 0
    features['energy_mean'] = row['energy_mean'] or 0
    features['energy_std'] = row['energy_std'] or 0

    # MFCC features
    mfcc_features = row['mfcc_features'] if row['mfcc_features'] else [0] * 13
    for i, mfcc in enumerate(mfcc_features):
        features[f'mfcc_{i}'] = mfcc

    # Spectral features
    spectral_features = row['spectral_features'] if row['spectral_features'] else [0] * 6
    spectral_names = [
        'spectral_centroid_mean', 'spectral_centroid_std',
        'spectral_rolloff_mean', 'spectral_rolloff_std',
        'spectral_bandwidth_mean', 'spectral_bandwidth_std'
    ]
    for name, value in zip(spectral_names, spectral_features):
        features[name] = value

    return [features.get(col, 0) for col in feature_columns]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get Records for Batch Inference

# COMMAND ----------

# Get enhanced transcriptions without recent predictions
inference_data_df = spark.sql(f"""
    SELECT
        et.id,
        et.voice_feedback_id,
        et.organization_id,
        et.transcription_text,
        et.word_count,
        et.sentence_count,
        et.avg_word_length,
        et.unique_word_count,
        et.key_phrases,
        et.topics,
        af.duration_seconds,
        af.avg_volume,
        af.max_volume,
        af.silence_ratio,
        af.speech_rate,
        af.pitch_mean,
        af.pitch_std,
        af.energy_mean,
        af.energy_std,
        af.mfcc_features,
        af.spectral_features
    FROM {CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions et
    JOIN {CATALOG_NAME}.{PROCESSED_SCHEMA}.audio_features af
        ON et.voice_feedback_id = af.voice_feedback_id
    LEFT JOIN {CATALOG_NAME}.{ML_SCHEMA}.predictions p
        ON et.voice_feedback_id = p.voice_feedback_id
        AND p.model_id = '{production_model_info['model_id']}'
        AND p.prediction_timestamp >= current_timestamp() - INTERVAL {INFERENCE_THRESHOLD_HOURS} HOURS
    WHERE et.transcription_text IS NOT NULL
        AND p.prediction_id IS NULL
    LIMIT {BATCH_SIZE}
""")

inference_count = inference_data_df.count()
print(f"Found {inference_count} records for batch inference")

if inference_count == 0:
    print("No records to process")
    dbutils.notebook.exit("No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Batch Inference

# COMMAND ----------

def run_batch_inference(data_df, model, model_id):
    """Run batch inference on a DataFrame"""

    inference_start = datetime.now()
    predictions_data = []

    # Convert to Pandas for processing
    data_pd = data_df.toPandas()

    print(f"Processing {len(data_pd)} records...")

    # Extract features for all rows
    features_list = []
    for idx, row in data_pd.iterrows():
        features = extract_features_from_row(row)
        features_list.append(features)

    # Convert to numpy array
    X = np.array(features_list)

    # Make predictions
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)

    # Label mapping (must match training)
    label_mapping = {0: 'negative', 1: 'neutral', 2: 'positive'}

    # Create prediction records
    for idx, (row, pred, probs) in enumerate(zip(data_pd.itertuples(), predictions, probabilities)):
        predicted_label = label_mapping.get(pred, 'unknown')
        confidence = float(max(probs))

        probability_dict = {
            label_mapping[i]: float(prob)
            for i, prob in enumerate(probs)
        }

        predictions_data.append({
            "prediction_id": str(uuid.uuid4()),
            "voice_feedback_id": row.voice_feedback_id,
            "model_id": model_id,
            "model_version": production_model_info['model_version'],
            "predicted_label": predicted_label,
            "prediction_confidence": confidence,
            "prediction_probabilities": json.dumps(probability_dict),
            "features_used": json.dumps(['feature_list']),  # Simplified
            "prediction_timestamp": datetime.now(),
            "inference_time_ms": 0  # Will calculate later
        })

    inference_end = datetime.now()
    inference_duration = (inference_end - inference_start).total_seconds()

    # Update inference time
    for pred in predictions_data:
        pred['inference_time_ms'] = int((inference_duration / len(predictions_data)) * 1000)

    print(f"\n✓ Batch inference complete")
    print(f"  Total time: {inference_duration:.2f} seconds")
    print(f"  Average time per prediction: {inference_duration/len(predictions_data)*1000:.2f} ms")

    return predictions_data, inference_duration

# COMMAND ----------

# Run inference
predictions_data, inference_duration = run_batch_inference(
    inference_data_df,
    production_model,
    production_model_info['model_id']
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Predictions

# COMMAND ----------

# Save predictions to Delta table
if predictions_data:
    predictions_df = spark.createDataFrame(predictions_data)

    predictions_df.write \
        .format("delta") \
        .mode("append") \
        .saveAsTable(f"{CATALOG_NAME}.{ML_SCHEMA}.predictions")

    print(f"✓ Saved {len(predictions_data)} predictions to Delta table")

    # Update enhanced_transcriptions with predictions
    for pred in predictions_data:
        spark.sql(f"""
            UPDATE {CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions
            SET
                sentiment_label = '{pred['predicted_label']}',
                sentiment_score = {json.loads(pred['prediction_probabilities'])[pred['predicted_label']]}
            WHERE voice_feedback_id = '{pred['voice_feedback_id']}'
                AND sentiment_label IS NULL
        """)

    print(f"✓ Updated enhanced_transcriptions with predictions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prediction Distribution Analysis

# COMMAND ----------

# Analyze prediction distribution
predictions_pd = pd.DataFrame(predictions_data)

print("\nPREDICTION DISTRIBUTION")
print("="*60)
print(predictions_pd['predicted_label'].value_counts())

print("\nCONFIDENCE STATISTICS")
print("="*60)
print(predictions_pd['prediction_confidence'].describe())

# Low confidence predictions
low_confidence_threshold = 0.6
low_confidence_count = len(predictions_pd[predictions_pd['prediction_confidence'] < low_confidence_threshold])

print(f"\nLow confidence predictions (<{low_confidence_threshold}): {low_confidence_count}")
print(f"Percentage: {low_confidence_count/len(predictions_pd)*100:.2f}%")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prediction Validation (if ground truth available)

# COMMAND ----------

# Compare predictions with existing sentiment labels (for validation)
validation_df = spark.sql(f"""
    SELECT
        p.predicted_label,
        sa.sentiment_label as actual_label,
        p.prediction_confidence,
        COUNT(*) as count
    FROM {CATALOG_NAME}.{ML_SCHEMA}.predictions p
    JOIN {CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis sa
        ON p.voice_feedback_id = sa.voice_feedback_id
    WHERE p.model_id = '{production_model_info['model_id']}'
        AND p.prediction_timestamp >= current_timestamp() - INTERVAL 1 HOUR
    GROUP BY p.predicted_label, sa.sentiment_label, p.prediction_confidence
""")

if validation_df.count() > 0:
    print("\nPREDICTION VALIDATION (vs Existing Labels)")
    print("="*60)
    display(validation_df)

    # Calculate accuracy
    accuracy_df = spark.sql(f"""
        SELECT
            SUM(CASE WHEN p.predicted_label = sa.sentiment_label THEN 1 ELSE 0 END) / COUNT(*) as accuracy
        FROM {CATALOG_NAME}.{ML_SCHEMA}.predictions p
        JOIN {CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis sa
            ON p.voice_feedback_id = sa.voice_feedback_id
        WHERE p.model_id = '{production_model_info['model_id']}'
            AND p.prediction_timestamp >= current_timestamp() - INTERVAL 1 HOUR
    """)

    accuracy = accuracy_df.collect()[0]['accuracy']
    print(f"\nPrediction Accuracy: {accuracy:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## A/B Testing (Optional)

# COMMAND ----------

def ab_test_models(data_df, model_a, model_b, model_a_id, model_b_id, split_ratio=0.5):
    """Run A/B test between two models"""

    data_pd = data_df.toPandas()

    # Split data for A/B test
    split_idx = int(len(data_pd) * split_ratio)
    data_a = data_pd.iloc[:split_idx]
    data_b = data_pd.iloc[split_idx:]

    print(f"A/B Test:")
    print(f"  Model A: {split_idx} samples")
    print(f"  Model B: {len(data_pd) - split_idx} samples")

    # Run inference on both groups
    predictions_a, duration_a = run_batch_inference(
        spark.createDataFrame(data_a),
        model_a,
        model_a_id
    )

    predictions_b, duration_b = run_batch_inference(
        spark.createDataFrame(data_b),
        model_b,
        model_b_id
    )

    # Compare results
    print("\nA/B Test Results:")
    print(f"  Model A avg confidence: {np.mean([p['prediction_confidence'] for p in predictions_a]):.4f}")
    print(f"  Model B avg confidence: {np.mean([p['prediction_confidence'] for p in predictions_b]):.4f}")
    print(f"  Model A avg inference time: {duration_a/len(predictions_a)*1000:.2f} ms")
    print(f"  Model B avg inference time: {duration_b/len(predictions_b)*1000:.2f} ms")

    return predictions_a + predictions_b

# Example: Uncomment to run A/B test
# model_b_info = spark.sql(f"""
#     SELECT * FROM {CATALOG_NAME}.{ML_SCHEMA}.model_registry
#     WHERE stage = 'Staging' LIMIT 1
# """).collect()[0]
# model_b = mlflow.sklearn.load_model(model_b_info['mlflow_model_uri'])
# ab_predictions = ab_test_models(
#     inference_data_df,
#     production_model,
#     model_b,
#     production_model_info['model_id'],
#     model_b_info['model_id']
# )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Track Inference Costs

# COMMAND ----------

# Calculate inference costs
# Cost estimation: $0.10 per hour compute + model serving costs
compute_cost = (inference_duration / 3600) * 0.10
model_serving_cost = len(predictions_data) * 0.0001  # $0.0001 per prediction
total_cost = compute_cost + model_serving_cost

cost_record = spark.createDataFrame([{
    "id": f"inf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "organization_id": None,
    "resource_type": "batch_inference",
    "resource_id": production_model_info['model_id'],
    "operation": f"predict_{production_model_info['model_type']}",
    "quantity": float(len(predictions_data)),
    "unit_cost": total_cost / len(predictions_data),
    "total_cost": total_cost,
    "currency": "USD",
    "cost_date": datetime.now().date(),
    "metadata": json.dumps({
        "inference_duration_seconds": inference_duration,
        "predictions_count": len(predictions_data),
        "avg_inference_time_ms": inference_duration / len(predictions_data) * 1000,
        "model_name": production_model_info['model_name'],
        "model_version": production_model_info['model_version'],
        "compute_cost": compute_cost,
        "model_serving_cost": model_serving_cost
    }),
    "created_at": datetime.now()
}])

cost_record.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(f"{CATALOG_NAME}.analytics.cost_tracking")

print(f"\n✓ Tracked inference costs:")
print(f"  Compute cost: ${compute_cost:.4f}")
print(f"  Model serving cost: ${model_serving_cost:.4f}")
print(f"  Total cost: ${total_cost:.4f}")
print(f"  Cost per prediction: ${total_cost/len(predictions_data):.6f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Tables

# COMMAND ----------

# Optimize predictions table
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{ML_SCHEMA}.predictions")
print("✓ Optimized predictions table")

# Z-ORDER for better query performance
spark.sql(f"""
    OPTIMIZE {CATALOG_NAME}.{ML_SCHEMA}.predictions
    ZORDER BY (model_id, prediction_timestamp)
""")
print("✓ Applied Z-ORDER optimization")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prediction Monitoring Dashboard

# COMMAND ----------

# Daily prediction metrics
prediction_metrics_df = spark.sql(f"""
    SELECT
        DATE(prediction_timestamp) as date,
        model_id,
        predicted_label,
        COUNT(*) as prediction_count,
        AVG(prediction_confidence) as avg_confidence,
        PERCENTILE(prediction_confidence, 0.5) as median_confidence,
        AVG(inference_time_ms) as avg_inference_time_ms
    FROM {CATALOG_NAME}.{ML_SCHEMA}.predictions
    WHERE prediction_timestamp >= current_date() - INTERVAL 7 DAYS
    GROUP BY DATE(prediction_timestamp), model_id, predicted_label
    ORDER BY date DESC, prediction_count DESC
""")

print("\nPREDICTION METRICS (Last 7 Days)")
print("="*80)
display(prediction_metrics_df)

# COMMAND ----------

# Model drift detection (compare prediction distribution over time)
drift_detection_df = spark.sql(f"""
    WITH daily_distribution AS (
        SELECT
            DATE(prediction_timestamp) as date,
            predicted_label,
            COUNT(*) as count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATE(prediction_timestamp)) as percentage
        FROM {CATALOG_NAME}.{ML_SCHEMA}.predictions
        WHERE prediction_timestamp >= current_date() - INTERVAL 30 DAYS
            AND model_id = '{production_model_info['model_id']}'
        GROUP BY DATE(prediction_timestamp), predicted_label
    )
    SELECT
        date,
        predicted_label,
        percentage,
        LAG(percentage, 7) OVER (PARTITION BY predicted_label ORDER BY date) as percentage_week_ago,
        percentage - LAG(percentage, 7) OVER (PARTITION BY predicted_label ORDER BY date) as percentage_change
    FROM daily_distribution
    ORDER BY date DESC, predicted_label
""")

print("\nMODEL DRIFT DETECTION (Prediction Distribution Changes)")
print("="*80)
display(drift_detection_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"""
Batch Inference Complete!

Summary:
--------
✓ Processed {len(predictions_data)} records
✓ Total inference time: {inference_duration:.2f} seconds
✓ Average inference time: {inference_duration/len(predictions_data)*1000:.2f} ms per prediction

Model Information:
------------------
• Name: {production_model_info['model_name']}
• Version: {production_model_info['model_version']}
• Type: {production_model_info['model_type']}
• Stage: Production

Prediction Distribution:
------------------------
{predictions_pd['predicted_label'].value_counts().to_string()}

Confidence Statistics:
----------------------
• Mean: {predictions_pd['prediction_confidence'].mean():.4f}
• Median: {predictions_pd['prediction_confidence'].median():.4f}
• Min: {predictions_pd['prediction_confidence'].min():.4f}
• Max: {predictions_pd['prediction_confidence'].max():.4f}

Low Confidence Predictions:
---------------------------
• Count: {low_confidence_count}
• Percentage: {low_confidence_count/len(predictions_pd)*100:.2f}%

Cost Analysis:
--------------
• Total cost: ${total_cost:.4f}
• Cost per prediction: ${total_cost/len(predictions_data):.6f}
• Compute cost: ${compute_cost:.4f}
• Model serving cost: ${model_serving_cost:.4f}

Next Steps:
-----------
1. Schedule this notebook to run periodically (e.g., hourly)
2. Monitor prediction distribution for model drift
3. Review low-confidence predictions for quality
4. Compare with ground truth when available
5. Retrain model if drift detected
6. Consider A/B testing new models

Cost Optimization:
------------------
• Run during off-peak hours for lower compute costs
• Batch predictions to reduce overhead
• Use appropriate batch sizes (current: {BATCH_SIZE})
• Monitor inference time and optimize features
• Consider model quantization for faster inference

Monitoring Recommendations:
---------------------------
• Set up alerts for low confidence predictions
• Track prediction distribution changes
• Monitor average confidence trends
• Compare with validation labels when available
• Track inference latency and costs

Production Deployment:
----------------------
To deploy for real-time inference:
1. Register model to Model Serving
2. Create REST endpoint
3. Set up monitoring and alerts
4. Implement fallback strategies
5. Configure auto-scaling
""")

# COMMAND ----------
