# Databricks Notebooks - Voice Feedback ML Pipeline

Comprehensive Databricks notebooks for the voice feedback platform ML pipeline.

## Overview

This collection of notebooks implements an end-to-end ML pipeline for processing voice feedback, including:

- Unity Catalog setup and data governance
- Data ingestion from PostgreSQL
- Audio processing and speech-to-text
- Sentiment analysis using Claude API
- ML model training and AutoML
- Batch inference and predictions
- Analytics and business intelligence

## Notebook Structure

### 00_unity_catalog_setup.py
**Purpose**: Set up Unity Catalog infrastructure

**Creates**:
- Catalog: `voice_feedback_prod`
- Schemas: `raw_data`, `processed_data`, `ml_models`, `analytics`
- Tables matching PostgreSQL schema
- Volumes for audio file storage
- Optimized indexes and partitioning

**Run Once**: Yes (initial setup)

**Dependencies**: None

---

### 01_data_ingestion.py
**Purpose**: Sync data from PostgreSQL to Databricks Delta tables

**Features**:
- JDBC connection to PostgreSQL
- Full and incremental sync
- Data quality validation
- Delta merge operations
- Change data capture (CDC)
- Cost tracking

**Schedule**: Every 15 minutes (incremental) or Daily (full sync)

**Dependencies**:
- PostgreSQL connection configured
- Databricks secrets for credentials

**Secrets Required**:
```
voice-feedback/postgres-host
voice-feedback/postgres-port
voice-feedback/postgres-database
voice-feedback/postgres-user
voice-feedback/postgres-password
```

---

### 02_voice_processing.py
**Purpose**: Process audio files and generate transcriptions

**Features**:
- Audio feature extraction (MFCC, spectral features)
- Speech-to-text using OpenAI Whisper
- Audio normalization
- Batch processing
- Cost optimization

**Libraries**:
- `openai-whisper`: Speech-to-text
- `librosa`: Audio feature extraction
- `soundfile`: Audio I/O
- `pydub`: Audio manipulation

**Schedule**: Continuous or every hour

**Dependencies**:
- Audio files in Unity Catalog volumes
- 01_data_ingestion.py completed

**Configuration**:
- `WHISPER_MODEL_SIZE`: tiny, base, small, medium, large
- `BATCH_SIZE`: Number of files to process per batch
- `WHISPER_DEVICE`: cpu or cuda (GPU)

---

### 03_sentiment_analysis.py
**Purpose**: Analyze sentiment using AI models

**Features**:
- Claude API for sentiment analysis
- Text embeddings for semantic search
- Topic and key phrase extraction
- Emotion detection
- Auto-tagging
- Vector Search setup (optional)

**Libraries**:
- `anthropic`: Claude API
- `openai`: OpenAI API (alternative)
- `sentence-transformers`: Text embeddings

**Schedule**: Every hour or after 02_voice_processing.py

**Dependencies**:
- 02_voice_processing.py completed
- Databricks secrets for API keys

**Secrets Required**:
```
voice-feedback/anthropic-api-key
voice-feedback/openai-api-key
```

**Configuration**:
- `BATCH_SIZE`: Number of transcriptions per batch
- Use Claude or OpenAI for sentiment

---

### 04_analytics_queries.sql
**Purpose**: Business intelligence and analytics

**Queries Include**:
- Daily feedback summaries
- Sentiment trends over time
- Top topics and trending topics
- User engagement metrics
- Organization metrics
- Cost analysis
- Processing performance
- Action items tracking

**Schedule**: Daily for aggregations

**Dependencies**: All previous notebooks

**Output Tables**:
- `analytics.daily_feedback_summary`
- `analytics.organization_metrics`
- `analytics.cost_tracking`

---

### 05_model_training.py
**Purpose**: Train ML models for sentiment classification

**Features**:
- Feature engineering
- Multiple model training (LR, RF, XGBoost, LightGBM)
- MLflow experiment tracking
- Model evaluation and comparison
- Model registration
- AutoML integration (optional)

**Models Trained**:
1. Logistic Regression
2. Random Forest
3. XGBoost
4. LightGBM

**Schedule**: Weekly or when retraining needed

**Dependencies**:
- 03_sentiment_analysis.py completed
- Sufficient training data available

**MLflow**:
- Experiment: `/Users/{user}/voice_feedback_sentiment`
- Registered models in Unity Catalog ML registry

---

### 06_batch_inference.py
**Purpose**: Run batch predictions using trained models

**Features**:
- Load production model from registry
- Batch prediction
- Prediction validation
- A/B testing between models
- Cost tracking
- Model drift detection

**Schedule**: Hourly or as needed

**Dependencies**:
- 05_model_training.py completed
- Production model registered

**Configuration**:
- `BATCH_SIZE`: Records per batch
- `INFERENCE_THRESHOLD_HOURS`: Re-prediction interval

---

### init_scripts/install_libraries.sh
**Purpose**: Cluster initialization script

**Installs**:
- Audio processing libraries
- ML and NLP libraries
- API clients
- Data processing libraries
- System dependencies

**Usage**:
1. Upload to DBFS: `/databricks/init_scripts/voice_feedback/install_libraries.sh`
2. Configure cluster to use this init script

---

## Setup Instructions

### 1. Prerequisites

- Databricks workspace with Unity Catalog enabled
- PostgreSQL database with voice feedback data
- Databricks secrets configured for:
  - PostgreSQL credentials
  - Anthropic API key
  - OpenAI API key

### 2. Configure Secrets

```bash
# PostgreSQL credentials
databricks secrets create-scope voice-feedback
databricks secrets put-secret voice-feedback postgres-host
databricks secrets put-secret voice-feedback postgres-port
databricks secrets put-secret voice-feedback postgres-database
databricks secrets put-secret voice-feedback postgres-user
databricks secrets put-secret voice-feedback postgres-password

# API keys
databricks secrets put-secret voice-feedback anthropic-api-key
databricks secrets put-secret voice-feedback openai-api-key
```

### 3. Create Cluster

**Recommended Configuration**:
- Runtime: Databricks ML Runtime 14.3 LTS or higher
- Node Type:
  - Driver: Standard_DS3_v2 (or equivalent)
  - Workers: Standard_DS3_v2 (or equivalent with GPU for Whisper)
- Workers: 2-4 (auto-scaling enabled)
- Init Script: `/databricks/init_scripts/voice_feedback/install_libraries.sh`

**Cluster Libraries** (if not using init script):
- PyPI: `openai-whisper`, `librosa`, `anthropic`, `sentence-transformers`

### 4. Upload Notebooks

1. Import all `.py` files into Databricks workspace
2. Upload `install_libraries.sh` to DBFS

### 5. Run Notebooks in Order

**Initial Setup**:
1. Run `00_unity_catalog_setup.py` (once)
2. Run `01_data_ingestion.py` (full sync)
3. Run `02_voice_processing.py` (process audio)
4. Run `03_sentiment_analysis.py` (analyze sentiment)
5. Run `04_analytics_queries.sql` (create aggregations)
6. Run `05_model_training.py` (train models)
7. Run `06_batch_inference.py` (batch predictions)

**Ongoing Operations**:
- Schedule notebooks using Databricks Jobs
- Monitor costs in `analytics.cost_tracking` table
- Review model performance regularly

---

## Scheduling Recommendations

### Databricks Jobs Configuration

**Job 1: Data Ingestion**
- Notebook: `01_data_ingestion.py`
- Schedule: Every 15 minutes
- Cluster: Existing cluster (shared)
- Retries: 3

**Job 2: Voice Processing**
- Notebook: `02_voice_processing.py`
- Schedule: Every hour
- Cluster: Job cluster (auto-terminate)
- Retries: 2

**Job 3: Sentiment Analysis**
- Notebook: `03_sentiment_analysis.py`
- Schedule: Every hour (after Job 2)
- Cluster: Job cluster (auto-terminate)
- Retries: 2

**Job 4: Analytics Aggregation**
- Notebook: `04_analytics_queries.sql`
- Schedule: Daily at 1 AM
- Cluster: Existing cluster (shared)
- Retries: 1

**Job 5: Model Training**
- Notebook: `05_model_training.py`
- Schedule: Weekly (Sunday at 2 AM)
- Cluster: ML cluster (GPU enabled)
- Retries: 1

**Job 6: Batch Inference**
- Notebook: `06_batch_inference.py`
- Schedule: Every hour
- Cluster: Job cluster (auto-terminate)
- Retries: 2

---

## Cost Optimization

### Compute Costs
- Use job clusters (auto-terminate) for scheduled jobs
- Use spot instances for non-critical workloads
- Schedule heavy processing during off-peak hours
- Optimize batch sizes to maximize throughput

### Storage Costs
- Run `OPTIMIZE` regularly on Delta tables
- Use `VACUUM` to remove old versions (retain 7 days)
- Enable auto-optimization on tables
- Use appropriate partitioning

### API Costs
- Batch API calls to reduce overhead
- Use smaller Whisper models (base vs large)
- Cache embeddings to avoid recomputation
- Monitor API usage in cost_tracking table

### Monitoring
All costs are tracked in: `voice_feedback_prod.analytics.cost_tracking`

Query costs:
```sql
SELECT
    resource_type,
    SUM(total_cost) as total_cost_usd
FROM voice_feedback_prod.analytics.cost_tracking
WHERE cost_date >= current_date() - INTERVAL 30 DAYS
GROUP BY resource_type
ORDER BY total_cost_usd DESC;
```

---

## Unity Catalog Structure

```
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
```

---

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Data Ingestion**
   - Sync latency
   - Failed syncs
   - Data quality issues

2. **Voice Processing**
   - Processing success rate
   - Average transcription confidence
   - Processing time per file

3. **Sentiment Analysis**
   - API success rate
   - Average confidence scores
   - Distribution of sentiments

4. **Model Performance**
   - Prediction accuracy
   - Model drift
   - Inference latency

5. **Costs**
   - Daily cost trends
   - Cost per feedback item
   - Resource utilization

### Alerting

Set up alerts for:
- Processing failures > 5%
- Low confidence predictions > 20%
- API errors
- High costs
- Model drift detected

---

## Troubleshooting

### Common Issues

**1. Audio Processing Fails**
- Check audio file format (supported: WAV, MP3, M4A)
- Verify audio files exist in volume
- Check Whisper model is loaded correctly
- Try smaller batch size

**2. API Rate Limits**
- Reduce batch size
- Increase delay between requests
- Check API quota limits
- Consider caching results

**3. Model Training Fails**
- Verify sufficient training data
- Check for NaN values in features
- Increase cluster memory
- Reduce feature count

**4. High Costs**
- Review batch sizes
- Optimize processing schedules
- Use smaller models
- Enable auto-scaling limits

---

## Support and Documentation

**Databricks Documentation**:
- Unity Catalog: https://docs.databricks.com/data-governance/unity-catalog/
- Delta Lake: https://docs.databricks.com/delta/
- MLflow: https://docs.databricks.com/mlflow/

**API Documentation**:
- Anthropic Claude: https://docs.anthropic.com/
- OpenAI Whisper: https://github.com/openai/whisper
- OpenAI API: https://platform.openai.com/docs

**Libraries**:
- Librosa: https://librosa.org/
- Sentence Transformers: https://www.sbert.net/

---

## Version History

**v1.0.0** - Initial Release
- Complete ML pipeline implementation
- Unity Catalog integration
- Cost tracking and optimization
- Model training and inference

---

## License

This project is part of the Voyce voice feedback platform.

---

## Contact

For questions or support, please contact the data engineering team.
