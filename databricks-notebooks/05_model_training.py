# Databricks notebook source
# MAGIC %md
# MAGIC # ML Model Training Pipeline
# MAGIC
# MAGIC This notebook handles:
# MAGIC - AutoML for sentiment classification
# MAGIC - Custom model training with MLflow
# MAGIC - Model evaluation and comparison
# MAGIC - Model registration and deployment
# MAGIC - Feature engineering

# COMMAND ----------

# MAGIC %md
# MAGIC ## Install Required Libraries

# COMMAND ----------

# MAGIC %pip install scikit-learn xgboost lightgbm databricks-automl mlflow

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration and Imports

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable

# ML libraries
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
import xgboost as xgb
import lightgbm as lgb

import pandas as pd
import numpy as np
import json
from datetime import datetime
import uuid

# COMMAND ----------

# Configuration
CATALOG_NAME = "voice_feedback_prod"
RAW_DATA_SCHEMA = "raw_data"
PROCESSED_SCHEMA = "processed_data"
ML_SCHEMA = "ml_models"

# MLflow experiment
EXPERIMENT_NAME = f"/Users/{spark.sql('SELECT current_user()').collect()[0][0]}/voice_feedback_sentiment"
mlflow.set_experiment(EXPERIMENT_NAME)

print(f"Catalog: {CATALOG_NAME}")
print(f"MLflow Experiment: {EXPERIMENT_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare Training Dataset

# COMMAND ----------

# Load enhanced transcriptions with features
training_data_df = spark.sql(f"""
    SELECT
        et.id,
        et.voice_feedback_id,
        et.organization_id,
        et.transcription_text,
        et.cleaned_text,
        et.language,
        et.word_count,
        et.sentence_count,
        et.avg_word_length,
        et.unique_word_count,
        et.sentiment_label,
        et.sentiment_score,
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
    WHERE et.sentiment_label IS NOT NULL
        AND et.transcription_text IS NOT NULL
""")

# Convert to Pandas for ML
training_data_pd = training_data_df.toPandas()

print(f"Total records: {len(training_data_pd)}")
print(f"\nSentiment distribution:")
print(training_data_pd['sentiment_label'].value_counts())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Engineering

# COMMAND ----------

def prepare_features(df):
    """Prepare features for ML model"""

    # Text-based features
    df['text_length'] = df['transcription_text'].str.len()
    df['unique_word_ratio'] = df['unique_word_count'] / df['word_count'].replace(0, 1)

    # Topic features (count of topics)
    df['topic_count'] = df['topics'].apply(lambda x: len(x) if x else 0)

    # Key phrase features
    df['key_phrase_count'] = df['key_phrases'].apply(lambda x: len(x) if x else 0)

    # Audio features - flatten MFCC and spectral features
    if 'mfcc_features' in df.columns:
        mfcc_df = pd.DataFrame(
            df['mfcc_features'].tolist(),
            columns=[f'mfcc_{i}' for i in range(13)]
        )
        df = pd.concat([df, mfcc_df], axis=1)

    if 'spectral_features' in df.columns:
        spectral_df = pd.DataFrame(
            df['spectral_features'].tolist(),
            columns=['spectral_centroid_mean', 'spectral_centroid_std',
                    'spectral_rolloff_mean', 'spectral_rolloff_std',
                    'spectral_bandwidth_mean', 'spectral_bandwidth_std']
        )
        df = pd.concat([df, spectral_df], axis=1)

    # Select feature columns
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

    # Fill NaN values
    df[feature_columns] = df[feature_columns].fillna(0)

    return df, feature_columns

# Prepare features
training_data_pd, feature_columns = prepare_features(training_data_pd)

print(f"\nTotal features: {len(feature_columns)}")
print(f"Feature columns: {feature_columns[:10]}... (showing first 10)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Split Dataset

# COMMAND ----------

# Encode labels
label_encoder = LabelEncoder()
training_data_pd['sentiment_label_encoded'] = label_encoder.fit_transform(training_data_pd['sentiment_label'])

# Features and labels
X = training_data_pd[feature_columns].values
y = training_data_pd['sentiment_label_encoded'].values

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set: {len(X_train)} samples")
print(f"Test set: {len(X_test)} samples")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# COMMAND ----------

# Save train/test split to Delta for reproducibility
train_indices = training_data_pd.iloc[X_train.index] if hasattr(X_train, 'index') else None

# Create training dataset table
train_df = training_data_pd.copy()
train_df['split'] = 'train'
train_df.loc[X_test.index if hasattr(X_test, 'index') else [], 'split'] = 'test'

# Convert to Spark DataFrame and save
spark_train_df = spark.createDataFrame(train_df[['id', 'voice_feedback_id', 'organization_id', 'sentiment_label', 'split']])

spark_train_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.{PROCESSED_SCHEMA}.training_dataset")

print("✓ Saved training dataset split")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Train Models with MLflow

# COMMAND ----------

def evaluate_model(y_true, y_pred, model_name):
    """Evaluate model and return metrics"""

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')

    metrics = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1
    }

    print(f"\n{model_name} Performance:")
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")

    return metrics

# COMMAND ----------

# MAGIC %md
# MAGIC ### Model 1: Logistic Regression

# COMMAND ----------

with mlflow.start_run(run_name="logistic_regression") as run:
    # Train model
    lr_model = LogisticRegression(max_iter=1000, random_state=42)
    lr_model.fit(X_train_scaled, y_train)

    # Predictions
    y_pred_train = lr_model.predict(X_train_scaled)
    y_pred_test = lr_model.predict(X_test_scaled)

    # Evaluate
    train_metrics = evaluate_model(y_train, y_pred_train, "Logistic Regression (Train)")
    test_metrics = evaluate_model(y_test, y_pred_test, "Logistic Regression (Test)")

    # Log parameters
    mlflow.log_param("model_type", "logistic_regression")
    mlflow.log_param("max_iter", 1000)
    mlflow.log_param("feature_count", len(feature_columns))

    # Log metrics
    for metric_name, value in test_metrics.items():
        mlflow.log_metric(f"test_{metric_name}", value)

    for metric_name, value in train_metrics.items():
        mlflow.log_metric(f"train_{metric_name}", value)

    # Log model
    mlflow.sklearn.log_model(
        lr_model,
        "model",
        registered_model_name=f"{CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_lr"
    )

    lr_run_id = run.info.run_id
    print(f"\n✓ Logged Logistic Regression model (Run ID: {lr_run_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Model 2: Random Forest

# COMMAND ----------

with mlflow.start_run(run_name="random_forest") as run:
    # Train model
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)

    # Predictions
    y_pred_train = rf_model.predict(X_train)
    y_pred_test = rf_model.predict(X_test)

    # Evaluate
    train_metrics = evaluate_model(y_train, y_pred_train, "Random Forest (Train)")
    test_metrics = evaluate_model(y_test, y_pred_test, "Random Forest (Test)")

    # Log parameters
    mlflow.log_param("model_type", "random_forest")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("feature_count", len(feature_columns))

    # Log metrics
    for metric_name, value in test_metrics.items():
        mlflow.log_metric(f"test_{metric_name}", value)

    for metric_name, value in train_metrics.items():
        mlflow.log_metric(f"train_{metric_name}", value)

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop 10 Important Features:")
    print(feature_importance.head(10))

    # Log model
    mlflow.sklearn.log_model(
        rf_model,
        "model",
        registered_model_name=f"{CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_rf"
    )

    rf_run_id = run.info.run_id
    print(f"\n✓ Logged Random Forest model (Run ID: {rf_run_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Model 3: XGBoost

# COMMAND ----------

with mlflow.start_run(run_name="xgboost") as run:
    # Train model
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss'
    )
    xgb_model.fit(X_train, y_train)

    # Predictions
    y_pred_train = xgb_model.predict(X_train)
    y_pred_test = xgb_model.predict(X_test)

    # Evaluate
    train_metrics = evaluate_model(y_train, y_pred_train, "XGBoost (Train)")
    test_metrics = evaluate_model(y_test, y_pred_test, "XGBoost (Test)")

    # Log parameters
    mlflow.log_param("model_type", "xgboost")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("learning_rate", 0.1)
    mlflow.log_param("feature_count", len(feature_columns))

    # Log metrics
    for metric_name, value in test_metrics.items():
        mlflow.log_metric(f"test_{metric_name}", value)

    for metric_name, value in train_metrics.items():
        mlflow.log_metric(f"train_{metric_name}", value)

    # Log model
    mlflow.xgboost.log_model(
        xgb_model,
        "model",
        registered_model_name=f"{CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_xgb"
    )

    xgb_run_id = run.info.run_id
    print(f"\n✓ Logged XGBoost model (Run ID: {xgb_run_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Model 4: LightGBM

# COMMAND ----------

with mlflow.start_run(run_name="lightgbm") as run:
    # Train model
    lgb_model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        verbose=-1
    )
    lgb_model.fit(X_train, y_train)

    # Predictions
    y_pred_train = lgb_model.predict(X_train)
    y_pred_test = lgb_model.predict(X_test)

    # Evaluate
    train_metrics = evaluate_model(y_train, y_pred_train, "LightGBM (Train)")
    test_metrics = evaluate_model(y_test, y_pred_test, "LightGBM (Test)")

    # Log parameters
    mlflow.log_param("model_type", "lightgbm")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("learning_rate", 0.1)
    mlflow.log_param("feature_count", len(feature_columns))

    # Log metrics
    for metric_name, value in test_metrics.items():
        mlflow.log_metric(f"test_{metric_name}", value)

    for metric_name, value in train_metrics.items():
        mlflow.log_metric(f"train_{metric_name}", value)

    # Log model
    mlflow.lightgbm.log_model(
        lgb_model,
        "model",
        registered_model_name=f"{CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_lgb"
    )

    lgb_run_id = run.info.run_id
    print(f"\n✓ Logged LightGBM model (Run ID: {lgb_run_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compare Models

# COMMAND ----------

# Get all runs from the experiment
experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

# Display model comparison
comparison_df = runs[['run_id', 'params.model_type', 'metrics.test_accuracy',
                      'metrics.test_precision', 'metrics.test_recall', 'metrics.test_f1_score']]

comparison_df = comparison_df.sort_values('metrics.test_f1_score', ascending=False)

print("\nMODEL COMPARISON")
print("="*80)
display(comparison_df)

# Get best model
best_model_run = comparison_df.iloc[0]
print(f"\n✓ Best Model: {best_model_run['params.model_type']}")
print(f"  F1 Score: {best_model_run['metrics.test_f1_score']:.4f}")
print(f"  Run ID: {best_model_run['run_id']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Model Metadata

# COMMAND ----------

# Save model registry information
model_registry_data = []

for _, run in comparison_df.iterrows():
    model_registry_data.append({
        "model_id": str(uuid.uuid4()),
        "model_name": f"sentiment_classifier_{run['params.model_type']}",
        "model_version": "1.0.0",
        "model_type": run['params.model_type'],
        "framework": "sklearn" if run['params.model_type'] in ['logistic_regression', 'random_forest'] else run['params.model_type'],
        "mlflow_run_id": run['run_id'],
        "mlflow_model_uri": f"runs:/{run['run_id']}/model",
        "metrics": json.dumps({
            "test_accuracy": run['metrics.test_accuracy'],
            "test_precision": run['metrics.test_precision'],
            "test_recall": run['metrics.test_recall'],
            "test_f1_score": run['metrics.test_f1_score']
        }),
        "parameters": json.dumps({
            "feature_count": len(feature_columns),
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }),
        "tags": json.dumps({"training_date": datetime.now().strftime("%Y-%m-%d")}),
        "stage": "Production" if run['run_id'] == best_model_run['run_id'] else "Staging",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })

# Save to Delta table
model_registry_df = spark.createDataFrame(model_registry_data)
model_registry_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(f"{CATALOG_NAME}.{ML_SCHEMA}.model_registry")

print("✓ Saved model registry metadata")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Predictions on Test Set

# COMMAND ----------

# Load best model
best_model = mlflow.sklearn.load_model(f"runs:/{best_model_run['run_id']}/model")

# Generate predictions
test_predictions = best_model.predict(X_test_scaled if 'logistic' in best_model_run['params.model_type'] else X_test)
test_probabilities = best_model.predict_proba(X_test_scaled if 'logistic' in best_model_run['params.model_type'] else X_test)

# Decode labels
predicted_labels = label_encoder.inverse_transform(test_predictions)
true_labels = label_encoder.inverse_transform(y_test)

# Create predictions DataFrame
predictions_data = []
test_indices = training_data_pd.iloc[len(X_train):].index if len(training_data_pd) > len(X_train) else range(len(X_test))

for i, (true_label, pred_label, probs) in enumerate(zip(true_labels, predicted_labels, test_probabilities)):
    row_idx = test_indices[i] if i < len(test_indices) else i
    row = training_data_pd.iloc[row_idx]

    predictions_data.append({
        "prediction_id": str(uuid.uuid4()),
        "voice_feedback_id": row['voice_feedback_id'],
        "model_id": model_registry_data[0]['model_id'],  # Best model
        "model_version": "1.0.0",
        "predicted_label": pred_label,
        "prediction_confidence": float(max(probs)),
        "prediction_probabilities": json.dumps({
            label: float(prob)
            for label, prob in zip(label_encoder.classes_, probs)
        }),
        "features_used": json.dumps(feature_columns),
        "prediction_timestamp": datetime.now(),
        "inference_time_ms": 10  # Placeholder
    })

# Save predictions
predictions_df = spark.createDataFrame(predictions_data)
predictions_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(f"{CATALOG_NAME}.{ML_SCHEMA}.predictions")

print(f"✓ Saved {len(predictions_data)} predictions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Model Performance Visualization

# COMMAND ----------

# Confusion matrix for best model
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

cm = confusion_matrix(true_labels, predicted_labels)

plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_)
plt.title(f'Confusion Matrix - {best_model_run["params.model_type"]}')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()

# Log to MLflow
mlflow.log_figure(plt.gcf(), "confusion_matrix.png")
plt.show()

# COMMAND ----------

# Classification report
print("\nDETAILED CLASSIFICATION REPORT")
print("="*80)
print(classification_report(true_labels, predicted_labels))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Databricks AutoML (Optional)

# COMMAND ----------

# Note: Uncomment to run AutoML (requires Databricks ML Runtime)

# from databricks import automl

# # Prepare data for AutoML
# automl_df = training_data_pd[feature_columns + ['sentiment_label']].copy()
# automl_spark_df = spark.createDataFrame(automl_df)

# # Run AutoML
# summary = automl.classify(
#     dataset=automl_spark_df,
#     target_col="sentiment_label",
#     timeout_minutes=30,
#     max_trials=10
# )

# print("✓ AutoML completed")
# print(f"Best model: {summary.best_trial}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Track Training Costs

# COMMAND ----------

# Estimate training costs
training_duration = 300  # seconds (estimate)
compute_cost = (training_duration / 3600) * 0.50  # $0.50/hour for ML compute

cost_record = spark.createDataFrame([{
    "id": f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "organization_id": None,
    "resource_type": "model_training",
    "resource_id": "sentiment_classifier",
    "operation": "train_multiple_models",
    "quantity": 4.0,  # 4 models trained
    "unit_cost": compute_cost / 4,
    "total_cost": compute_cost,
    "currency": "USD",
    "cost_date": datetime.now().date(),
    "metadata": json.dumps({
        "training_duration_seconds": training_duration,
        "models_trained": 4,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_count": len(feature_columns),
        "best_model": best_model_run['params.model_type'],
        "best_f1_score": best_model_run['metrics.test_f1_score']
    }),
    "created_at": datetime.now()
}])

cost_record.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(f"{CATALOG_NAME}.analytics.cost_tracking")

print(f"\n✓ Tracked training costs: ${compute_cost:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"""
Model Training Complete!

Summary:
--------
✓ Trained 4 models: Logistic Regression, Random Forest, XGBoost, LightGBM
✓ Best Model: {best_model_run['params.model_type']}
✓ Best F1 Score: {best_model_run['metrics.test_f1_score']:.4f}

Training Data:
--------------
• Total samples: {len(training_data_pd)}
• Training samples: {len(X_train)}
• Test samples: {len(X_test)}
• Features: {len(feature_columns)}
• Classes: {len(label_encoder.classes_)} ({', '.join(label_encoder.classes_)})

Model Performance (Test Set):
------------------------------
• Accuracy:  {best_model_run['metrics.test_accuracy']:.4f}
• Precision: {best_model_run['metrics.test_precision']:.4f}
• Recall:    {best_model_run['metrics.test_recall']:.4f}
• F1 Score:  {best_model_run['metrics.test_f1_score']:.4f}

Registered Models:
------------------
• {CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_lr
• {CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_rf
• {CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_xgb
• {CATALOG_NAME}.{ML_SCHEMA}.sentiment_classifier_lgb

MLflow Experiment:
------------------
{EXPERIMENT_NAME}

Next Steps:
-----------
1. Review model performance and confusion matrix
2. Run 06_batch_inference.py for production inference
3. Monitor model performance over time
4. Retrain models with new data periodically
5. Consider model deployment to REST endpoint
6. Set up model monitoring and drift detection

Model Deployment:
-----------------
To deploy the best model:

# Load model
model = mlflow.sklearn.load_model("runs:/{best_model_run['run_id']}/model")

# Make predictions
predictions = model.predict(features)

Cost Optimization:
------------------
• Train models during off-peak hours
• Use AutoML for automatic hyperparameter tuning
• Monitor model performance vs. cost
• Consider model complexity vs. accuracy tradeoff
• Implement incremental learning for updates
""")

# COMMAND ----------
