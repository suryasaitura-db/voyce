# System Architecture

This document describes the architecture of the Voyce Voice Feedback Platform.

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Architecture Diagram](#architecture-diagram)
- [Data Flow](#data-flow)
- [Component Details](#component-details)
- [Technology Decisions](#technology-decisions)
- [Scalability](#scalability)
- [Security Architecture](#security-architecture)

## Overview

Voyce is built as a microservices-based architecture with three main layers:

1. **Presentation Layer**: Web, mobile, and browser extension interfaces
2. **Application Layer**: FastAPI backend with REST APIs
3. **Data & ML Layer**: Databricks for processing, analysis, and ML workflows

## System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                          │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│   Web App       │   Mobile App    │   Chrome Extension              │
│   (React)       │   (React Native)│   (JavaScript)                  │
└────────┬────────┴────────┬────────┴─────────┬───────────────────────┘
         │                 │                   │
         └─────────────────┼───────────────────┘
                           │
                           │ HTTPS/REST API
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   FastAPI Backend                            │ │
│  ├──────────────┬──────────────┬──────────────┬─────────────────┤ │
│  │ Auth Router  │ Submissions  │  Analytics   │  Health/Metrics │ │
│  └──────┬───────┴──────┬───────┴──────┬───────┴─────────────────┘ │
│         │              │              │                            │
│  ┌──────▼──────────────▼──────────────▼──────────────────┐        │
│  │              Service Layer                            │        │
│  ├────────────┬──────────────┬────────────┬──────────────┤        │
│  │Auth Service│Voice Processor│Storage Svc│Sentiment Svc │        │
│  └────────────┴──────────────┴────────────┴──────────────┘        │
│                                                                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────────┐
│  PostgreSQL │  │Cloud Storage│  │  Redis Cache    │
│  Database   │  │  (S3/Azure) │  │  (Optional)     │
└─────────────┘  └─────────────┘  └─────────────────┘
                          │
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                     DATA & ML LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  Databricks Workspace                        │ │
│  ├──────────────┬──────────────┬──────────────┬─────────────────┤ │
│  │Unity Catalog │ Serverless   │ SQL Serverless│  ML Runtime    │ │
│  └──────────────┴──────────────┴──────────────┴─────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Notebooks/Jobs                            │ │
│  ├──────────────┬──────────────┬──────────────┬─────────────────┤ │
│  │Data Ingestion│Voice Process │ Sentiment    │ Model Training  │ │
│  │              │ & Transcribe │ Analysis     │ & Inference     │ │
│  └──────────────┴──────────────┴──────────────┴─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MONITORING & OBSERVABILITY                        │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│  Prometheus     │    Grafana      │    ELK/Datadog                  │
│  (Metrics)      │   (Dashboards)  │    (Logs)                       │
└─────────────────┴─────────────────┴─────────────────────────────────┘
```

## Data Flow

### 1. Voice Submission Flow

```
User Records Voice
       │
       ▼
[Client App validates format/size]
       │
       ▼
POST /api/submissions/upload
       │
       ▼
[Backend validates & stores in cloud]
       │
       ▼
[Create DB record with status='pending']
       │
       ▼
[Queue for processing]
       │
       ▼
[Databricks: Data Ingestion]
       │
       ▼
[Databricks: Voice Processing & Transcription]
       │
       ▼
[Update DB with transcription]
       │
       ▼
[Databricks: Sentiment Analysis]
       │
       ▼
[Update DB with analysis results]
       │
       ▼
[Notify user/Update status to 'completed']
```

### 2. Analytics Flow

```
User requests analytics
       │
       ▼
GET /api/analytics/...
       │
       ▼
[Backend queries PostgreSQL]
       │
       ▼
[Optional: Query Databricks SQL Warehouse for complex analytics]
       │
       ▼
[Aggregate and format results]
       │
       ▼
[Return to client]
```

## Component Details

### Frontend Applications

#### Web Application (React)
- **Purpose**: Primary user interface for desktop users
- **Features**:
  - Voice recording with Web Audio API
  - File upload interface
  - Dashboard with analytics
  - User management
- **Tech Stack**: React, Redux, Material-UI, Web Audio API

#### Mobile Application (React Native)
- **Purpose**: Native mobile experience
- **Features**:
  - Native audio recording
  - Offline support
  - Push notifications
  - Camera integration
- **Tech Stack**: React Native, Expo, AsyncStorage

#### Chrome Extension
- **Purpose**: Context-aware feedback on any website
- **Features**:
  - Quick voice recording
  - Page context capture
  - Minimal UI footprint
- **Tech Stack**: Vanilla JavaScript, Chrome Extension API

### Backend (FastAPI)

#### API Routers

**Authentication Router** (`/api/auth`)
- User registration
- Login/Logout
- Token refresh
- Password reset
- OAuth2 integration

**Submissions Router** (`/api/submissions`)
- Upload voice files
- List submissions
- Get submission details
- Update/Delete submissions
- Transcription retrieval

**Analytics Router** (`/api/analytics`)
- Dashboard metrics
- Sentiment trends
- Intent distribution
- User statistics
- Export functionality

#### Services

**Auth Service**
- JWT token generation/validation
- Password hashing (bcrypt)
- User session management
- Role-based access control

**Voice Processor**
- Audio format validation
- File size checks
- Audio metadata extraction
- Quality assessment

**Storage Service**
- Cloud storage integration (S3/Azure/GCS)
- Pre-signed URL generation
- File lifecycle management
- CDN integration

**Sentiment Analyzer**
- Text preprocessing
- Model inference
- Result formatting
- Confidence scoring

### Database Layer

#### PostgreSQL Tables

**users**
- User authentication and profile
- Indexes: email, username, created_at

**voice_submissions**
- Voice file metadata
- Processing status
- Indexes: user_id, status, created_at, category

**transcriptions**
- Transcribed text
- Language detection
- Word-level timestamps
- Indexes: submission_id, language, confidence

**analyses**
- Sentiment scores
- Emotion detection
- Intent classification
- Action items
- Indexes: submission_id, sentiment, intent, importance_score

### Databricks Layer

#### Unity Catalog Structure

```
voyce_catalog
├── bronze (raw data)
│   ├── audio_files
│   └── metadata
├── silver (cleaned/transformed)
│   ├── transcriptions
│   └── enriched_metadata
└── gold (aggregated/analytics)
    ├── sentiment_trends
    ├── user_insights
    └── model_metrics
```

#### Notebooks/Jobs

**00_unity_catalog_setup.py**
- Initialize Unity Catalog
- Create schemas and tables
- Set permissions

**01_data_ingestion.py**
- Ingest audio files from cloud storage
- Validate and catalog data
- Update metadata

**02_voice_processing.py**
- Audio preprocessing
- Transcription using Whisper
- Quality checks

**03_sentiment_analysis.py**
- Load transcriptions
- Run sentiment models
- Extract insights

**05_model_training.py**
- Train custom sentiment models
- Fine-tune on domain data
- Model versioning

**06_batch_inference.py**
- Batch processing of submissions
- Scheduled analysis jobs
- Result aggregation

## Technology Decisions

### Why FastAPI?
- High performance (async/await)
- Automatic API documentation
- Type hints and validation
- Modern Python features

### Why PostgreSQL?
- ACID compliance
- JSON support for flexible schemas
- Full-text search capabilities
- Strong ecosystem

### Why Databricks?
- Unified analytics platform
- Serverless compute (cost-effective)
- Unity Catalog for data governance
- Built-in ML capabilities

### Why React?
- Component reusability
- Large ecosystem
- Strong community
- Performance optimization

## Scalability

### Horizontal Scaling

**API Layer**
- Stateless FastAPI instances
- Load balancer distribution
- Auto-scaling based on CPU/memory

**Database**
- Read replicas for analytics
- Connection pooling
- Query optimization

**Databricks**
- Serverless auto-scaling
- Spot instances for batch jobs
- Optimized cluster sizing

### Vertical Scaling

- Increase instance sizes for specific workloads
- GPU instances for ML inference
- Memory-optimized for large datasets

### Caching Strategy

```
[Client] → [CDN (Static Assets)]
    ↓
[Load Balancer] → [API Cache (Redis)]
    ↓
[FastAPI] → [Database Query Cache]
    ↓
[PostgreSQL]
```

## Security Architecture

### Authentication Flow

```
Client Request
    │
    ▼
[Extract JWT from Authorization Header]
    │
    ▼
[Validate JWT signature]
    │
    ▼
[Check expiration]
    │
    ▼
[Verify user permissions]
    │
    ▼
[Allow/Deny request]
```

### Data Security

- **In Transit**: TLS 1.3 for all connections
- **At Rest**: AES-256 encryption for storage
- **Database**: Encrypted connections, column-level encryption for sensitive data
- **API**: Rate limiting, CORS policies, input validation

### Network Security

```
Internet
    │
    ▼
[WAF/DDoS Protection]
    │
    ▼
[Load Balancer (HTTPS only)]
    │
    ▼
[Private Network]
    │
    ├─→ [API Servers]
    ├─→ [Database (Private subnet)]
    └─→ [Databricks (VPC Peering)]
```

## Performance Optimization

### API Response Times
- Target: < 200ms for GET requests
- Target: < 1s for POST requests
- Target: < 5s for file uploads

### Database Optimization
- Indexes on frequently queried columns
- Partitioning for large tables
- Query result caching
- Connection pooling

### Databricks Optimization
- Delta Lake for ACID transactions
- Z-ordering for query performance
- Auto-optimize and auto-vacuum
- Photon acceleration

## Monitoring Architecture

```
Application Metrics
    │
    ├─→ [Prometheus] → [Grafana Dashboards]
    │
    ├─→ [Application Logs] → [ELK Stack/Datadog]
    │
    └─→ [Health Checks] → [Alerting System]
```

### Key Metrics

**Application**
- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active users

**Infrastructure**
- CPU utilization
- Memory usage
- Disk I/O
- Network throughput

**Business**
- Submissions per day
- Processing success rate
- Average sentiment scores
- User engagement

## Disaster Recovery

### Backup Strategy
- Database: Daily full backups, hourly incremental
- Storage: Cross-region replication
- Configuration: Version controlled in Git

### Recovery Time Objectives
- RTO (Recovery Time Objective): < 1 hour
- RPO (Recovery Point Objective): < 15 minutes

## Future Enhancements

1. **Real-time Processing**: WebSocket connections for live transcription
2. **Multi-tenant Support**: Organization-level isolation
3. **Advanced ML**: Custom model training per organization
4. **Global CDN**: Edge processing for lower latency
5. **Event Streaming**: Kafka/Kinesis for real-time analytics
