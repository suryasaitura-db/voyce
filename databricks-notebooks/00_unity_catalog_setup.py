# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Setup for Voice Feedback Platform
# MAGIC
# MAGIC This notebook sets up the Unity Catalog structure for the voice feedback ML pipeline:
# MAGIC - Catalog: voice_feedback_prod
# MAGIC - Schemas: raw_data, processed_data, ml_models, analytics
# MAGIC - Tables matching PostgreSQL schema
# MAGIC - Volumes for audio file storage

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration parameters
CATALOG_NAME = "voice_feedback_prod"
SCHEMAS = ["raw_data", "processed_data", "ml_models", "analytics"]
CHECKPOINT_LOCATION = "/checkpoints/voice_feedback"

# Print configuration
print(f"Catalog: {CATALOG_NAME}")
print(f"Schemas: {', '.join(SCHEMAS)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Catalog

# COMMAND ----------

# Create catalog if not exists
spark.sql(f"""
CREATE CATALOG IF NOT EXISTS {CATALOG_NAME}
COMMENT 'Voice feedback platform data and ML models'
""")

print(f"✓ Catalog '{CATALOG_NAME}' created/verified")

# Set as default catalog
spark.sql(f"USE CATALOG {CATALOG_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Schemas

# COMMAND ----------

# Create schemas
for schema in SCHEMAS:
    spark.sql(f"""
    CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.{schema}
    COMMENT 'Schema for {schema.replace("_", " ")}'
    """)
    print(f"✓ Schema '{schema}' created/verified")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Raw Data Tables (synced from PostgreSQL)

# COMMAND ----------

# Organizations table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.organizations (
    id STRING NOT NULL,
    name STRING NOT NULL,
    industry STRING,
    company_size STRING,
    subscription_tier STRING,
    settings STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
)
USING DELTA
COMMENT 'Organizations/companies using the platform'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'organizations' created/verified")

# COMMAND ----------

# Users table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.users (
    id STRING NOT NULL,
    organization_id STRING NOT NULL,
    email STRING NOT NULL,
    full_name STRING,
    role STRING,
    department STRING,
    phone_number STRING,
    preferences STRING,
    last_login TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
)
USING DELTA
COMMENT 'Platform users'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'users' created/verified")

# COMMAND ----------

# Voice feedback table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.voice_feedback (
    id STRING NOT NULL,
    organization_id STRING NOT NULL,
    user_id STRING,
    audio_file_path STRING NOT NULL,
    audio_duration_seconds DOUBLE,
    audio_format STRING,
    file_size_bytes BIGINT,
    upload_source STRING,
    metadata STRING,
    status STRING DEFAULT 'pending',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
USING DELTA
COMMENT 'Raw voice feedback recordings'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'voice_feedback' created/verified")

# COMMAND ----------

# Transcriptions table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.transcriptions (
    id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    transcription_text STRING,
    transcription_engine STRING,
    confidence_score DOUBLE,
    language_detected STRING,
    word_count INT,
    processing_time_ms BIGINT,
    error_message STRING,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Speech-to-text transcriptions'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'transcriptions' created/verified")

# COMMAND ----------

# Sentiment analysis table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.sentiment_analysis (
    id STRING NOT NULL,
    transcription_id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    sentiment_label STRING,
    sentiment_score DOUBLE,
    sentiment_confidence DOUBLE,
    emotions STRING,
    key_phrases STRING,
    topics STRING,
    model_used STRING,
    model_version STRING,
    processing_time_ms BIGINT,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Sentiment analysis results'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'sentiment_analysis' created/verified")

# COMMAND ----------

# Tags table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.tags (
    id STRING NOT NULL,
    name STRING NOT NULL,
    category STRING,
    description STRING,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Tagging system for categorization'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'tags' created/verified")

# COMMAND ----------

# Feedback tags junction table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.feedback_tags (
    id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    tag_id STRING NOT NULL,
    assigned_by STRING,
    confidence_score DOUBLE,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Many-to-many relationship between feedback and tags'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'feedback_tags' created/verified")

# COMMAND ----------

# Action items table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.raw_data.action_items (
    id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    description STRING NOT NULL,
    priority STRING,
    assigned_to STRING,
    due_date TIMESTAMP,
    status STRING DEFAULT 'open',
    completed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
USING DELTA
COMMENT 'Action items extracted from feedback'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'action_items' created/verified")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Processed Data Tables

# COMMAND ----------

# Enhanced transcriptions with features
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.processed_data.enhanced_transcriptions (
    id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    organization_id STRING NOT NULL,
    transcription_text STRING,
    cleaned_text STRING,
    language STRING,
    word_count INT,
    sentence_count INT,
    avg_word_length DOUBLE,
    unique_word_count INT,
    sentiment_label STRING,
    sentiment_score DOUBLE,
    key_phrases ARRAY<STRING>,
    topics ARRAY<STRING>,
    named_entities ARRAY<STRING>,
    text_embedding ARRAY<DOUBLE>,
    processing_timestamp TIMESTAMP,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Enhanced transcriptions with ML features'
PARTITIONED BY (organization_id)
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'enhanced_transcriptions' created/verified")

# COMMAND ----------

# Audio features table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.processed_data.audio_features (
    id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    organization_id STRING NOT NULL,
    duration_seconds DOUBLE,
    sample_rate INT,
    bit_rate INT,
    channels INT,
    avg_volume DOUBLE,
    max_volume DOUBLE,
    silence_ratio DOUBLE,
    speech_rate DOUBLE,
    pitch_mean DOUBLE,
    pitch_std DOUBLE,
    energy_mean DOUBLE,
    energy_std DOUBLE,
    mfcc_features ARRAY<DOUBLE>,
    spectral_features ARRAY<DOUBLE>,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Extracted audio features for ML'
PARTITIONED BY (organization_id)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'audio_features' created/verified")

# COMMAND ----------

# Training dataset
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.processed_data.training_dataset (
    id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    organization_id STRING NOT NULL,
    features STRING,
    label STRING,
    label_confidence DOUBLE,
    split STRING,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Prepared training dataset for ML models'
PARTITIONED BY (split)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'training_dataset' created/verified")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create ML Models Schema Tables

# COMMAND ----------

# Model registry table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.ml_models.model_registry (
    model_id STRING NOT NULL,
    model_name STRING NOT NULL,
    model_version STRING NOT NULL,
    model_type STRING,
    framework STRING,
    mlflow_run_id STRING,
    mlflow_model_uri STRING,
    metrics STRING,
    parameters STRING,
    tags STRING,
    stage STRING DEFAULT 'None',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
USING DELTA
COMMENT 'ML model registry and metadata'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'model_registry' created/verified")

# COMMAND ----------

# Model predictions
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.ml_models.predictions (
    prediction_id STRING NOT NULL,
    voice_feedback_id STRING NOT NULL,
    model_id STRING NOT NULL,
    model_version STRING NOT NULL,
    predicted_label STRING,
    prediction_confidence DOUBLE,
    prediction_probabilities STRING,
    features_used STRING,
    prediction_timestamp TIMESTAMP,
    inference_time_ms BIGINT
)
USING DELTA
COMMENT 'ML model predictions'
PARTITIONED BY (model_id)
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'predictions' created/verified")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Analytics Schema Tables

# COMMAND ----------

# Daily aggregations
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.analytics.daily_feedback_summary (
    date DATE NOT NULL,
    organization_id STRING NOT NULL,
    total_feedback_count BIGINT,
    avg_duration_seconds DOUBLE,
    sentiment_positive_count BIGINT,
    sentiment_neutral_count BIGINT,
    sentiment_negative_count BIGINT,
    avg_sentiment_score DOUBLE,
    top_topics ARRAY<STRING>,
    top_tags ARRAY<STRING>,
    processing_success_rate DOUBLE,
    avg_processing_time_ms DOUBLE,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Daily aggregated feedback metrics'
PARTITIONED BY (date)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'daily_feedback_summary' created/verified")

# COMMAND ----------

# Organization metrics
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.analytics.organization_metrics (
    organization_id STRING NOT NULL,
    metric_date DATE NOT NULL,
    total_users BIGINT,
    active_users BIGINT,
    total_feedback_count BIGINT,
    avg_feedback_per_user DOUBLE,
    total_audio_minutes DOUBLE,
    storage_used_gb DOUBLE,
    api_calls_count BIGINT,
    processing_cost_usd DOUBLE,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Organization-level metrics for billing and analytics'
PARTITIONED BY (metric_date)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'organization_metrics' created/verified")

# COMMAND ----------

# Cost tracking
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.analytics.cost_tracking (
    id STRING NOT NULL,
    organization_id STRING,
    resource_type STRING NOT NULL,
    resource_id STRING,
    operation STRING NOT NULL,
    quantity DOUBLE,
    unit_cost DOUBLE,
    total_cost DOUBLE,
    currency STRING DEFAULT 'USD',
    cost_date DATE,
    metadata STRING,
    created_at TIMESTAMP
)
USING DELTA
COMMENT 'Cost tracking for compute, storage, and API calls'
PARTITIONED BY (cost_date)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")
print("✓ Table 'cost_tracking' created/verified")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Volumes for Audio Storage

# COMMAND ----------

# Create volume for audio files
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {CATALOG_NAME}.raw_data.audio_files
COMMENT 'Volume for storing raw audio files'
""")
print("✓ Volume 'audio_files' created/verified")

# COMMAND ----------

# Create volume for processed audio
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {CATALOG_NAME}.processed_data.processed_audio
COMMENT 'Volume for storing processed/normalized audio files'
""")
print("✓ Volume 'processed_audio' created/verified")

# COMMAND ----------

# Create volume for ML artifacts
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {CATALOG_NAME}.ml_models.artifacts
COMMENT 'Volume for storing ML model artifacts and exports'
""")
print("✓ Volume 'artifacts' created/verified")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Indexes and Optimize Tables

# COMMAND ----------

# Optimize raw data tables
for table in ['organizations', 'users', 'voice_feedback', 'transcriptions', 'sentiment_analysis', 'feedback_tags', 'action_items']:
    spark.sql(f"OPTIMIZE {CATALOG_NAME}.raw_data.{table}")
    print(f"✓ Optimized table 'raw_data.{table}'")

# COMMAND ----------

# Z-ORDER optimization for frequently queried columns
spark.sql(f"OPTIMIZE {CATALOG_NAME}.raw_data.voice_feedback ZORDER BY (organization_id, created_at, status)")
spark.sql(f"OPTIMIZE {CATALOG_NAME}.raw_data.transcriptions ZORDER BY (voice_feedback_id, created_at)")
spark.sql(f"OPTIMIZE {CATALOG_NAME}.raw_data.sentiment_analysis ZORDER BY (voice_feedback_id, sentiment_label)")

print("✓ Applied Z-ORDER optimization to key tables")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Setup

# COMMAND ----------

# List all tables in catalog
print(f"\n{'='*60}")
print(f"CATALOG: {CATALOG_NAME}")
print(f"{'='*60}\n")

for schema in SCHEMAS:
    tables = spark.sql(f"SHOW TABLES IN {CATALOG_NAME}.{schema}").collect()
    print(f"\nSchema: {schema}")
    print(f"{'-'*60}")
    for table in tables:
        print(f"  ✓ {table.tableName}")

    # Show volumes
    volumes = spark.sql(f"SHOW VOLUMES IN {CATALOG_NAME}.{schema}").collect()
    if volumes:
        print(f"\n  Volumes:")
        for volume in volumes:
            print(f"    ✓ {volume.volume_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("""
Unity Catalog Setup Complete!

Catalog Structure:
------------------
voice_feedback_prod/
├── raw_data/
│   ├── organizations
│   ├── users
│   ├── voice_feedback
│   ├── transcriptions
│   ├── sentiment_analysis
│   ├── tags
│   ├── feedback_tags
│   ├── action_items
│   └── audio_files (volume)
├── processed_data/
│   ├── enhanced_transcriptions
│   ├── audio_features
│   ├── training_dataset
│   └── processed_audio (volume)
├── ml_models/
│   ├── model_registry
│   ├── predictions
│   └── artifacts (volume)
└── analytics/
    ├── daily_feedback_summary
    ├── organization_metrics
    └── cost_tracking

Next Steps:
-----------
1. Run 01_data_ingestion.py to sync data from PostgreSQL
2. Run 02_voice_processing.py to process audio files
3. Run 03_sentiment_analysis.py for ML inference
4. Run 04_analytics_queries.sql for analytics
5. Run 05_model_training.py to train custom models
6. Run 06_batch_inference.py for batch processing

Features Enabled:
-----------------
✓ Change Data Feed (CDC)
✓ Auto Optimize Write
✓ Auto Compaction
✓ Z-ORDER indexing
✓ Partitioning for performance
✓ Unity Catalog governance
""")

# COMMAND ----------
