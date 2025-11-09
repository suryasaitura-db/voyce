# Database Schema Documentation

Complete database schema and design documentation for the Voyce Voice Feedback Platform.

## Table of Contents

- [Overview](#overview)
- [Entity Relationship Diagram](#entity-relationship-diagram)
- [Tables](#tables)
- [Indexes](#indexes)
- [Relationships](#relationships)
- [Data Types](#data-types)
- [Migrations](#migrations)
- [Best Practices](#best-practices)

## Overview

### Database Technology

- **RDBMS**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Extensions**: pgcrypto, pg_stat_statements, uuid-ossp

### Design Principles

1. **Normalization**: 3NF for data integrity
2. **Indexing**: Strategic indexes for performance
3. **Scalability**: Designed for millions of records
4. **Security**: Encrypted sensitive data
5. **Audit Trail**: Timestamps on all tables

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATABASE SCHEMA                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│     USERS       │
├─────────────────┤
│ id (PK)         │
│ email (UK)      │
│ username (UK)   │
│ hashed_password │
│ full_name       │
│ avatar_url      │
│ is_active       │
│ is_verified     │
│ is_superuser    │
│ role            │
│ bio             │
│ organization    │
│ created_at      │
│ updated_at      │
│ last_login_at   │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼──────────────┐
│  VOICE_SUBMISSIONS    │
├───────────────────────┤
│ id (PK)               │
│ user_id (FK)          │
│ file_path             │
│ file_name             │
│ file_size             │
│ file_format           │
│ mime_type             │
│ duration              │
│ sample_rate           │
│ channels              │
│ title                 │
│ description           │
│ tags (JSON)           │
│ category              │
│ source                │
│ source_url            │
│ user_agent            │
│ status                │
│ is_processed          │
│ is_transcribed        │
│ is_analyzed           │
│ is_public             │
│ created_at            │
│ updated_at            │
│ processed_at          │
│ error_message         │
│ retry_count           │
└────────┬──────────────┘
         │
         │ 1:1
         │
┌────────▼──────────────┐
│   TRANSCRIPTIONS      │
├───────────────────────┤
│ id (PK)               │
│ submission_id (FK,UK) │
│ text                  │
│ language              │
│ confidence            │
│ words (JSON)          │
│ segments (JSON)       │
│ model                 │
│ model_version         │
│ provider              │
│ processing_time       │
│ audio_duration        │
│ word_count            │
│ speaking_rate         │
│ silence_duration      │
│ detected_language     │
│ language_confidence   │
│ is_multilingual       │
│ entities (JSON)       │
│ topics (JSON)         │
│ created_at            │
│ updated_at            │
│ error_message         │
└────────┬──────────────┘
         │
         │ 1:1
         │
┌────────▼──────────────┐
│      ANALYSES         │
├───────────────────────┤
│ id (PK)               │
│ submission_id (FK,UK) │
│ transcription_id (FK) │
│ sentiment             │
│ sentiment_score       │
│ sentiment_confidence  │
│ sentiment_breakdown   │
│ emotions (JSON)       │
│ dominant_emotion      │
│ emotion_confidence    │
│ intent                │
│ intent_confidence     │
│ sub_intents (JSON)    │
│ summary               │
│ key_points (JSON)     │
│ action_items (JSON)   │
│ topics (JSON)         │
│ categories (JSON)     │
│ tags (JSON)           │
│ entities (JSON)       │
│ keywords (JSON)       │
│ clarity_score         │
│ urgency_score         │
│ importance_score      │
│ is_actionable         │
│ requires_follow_up    │
│ is_complaint          │
│ is_positive_feedback  │
│ model                 │
│ model_version         │
│ provider              │
│ processing_time       │
│ prompt_tokens         │
│ completion_tokens     │
│ total_tokens          │
│ created_at            │
│ updated_at            │
│ error_message         │
└───────────────────────┘
```

## Tables

### users

Stores user account information and authentication credentials.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_login_at TIMESTAMP WITH TIME ZONE,
    bio TEXT,
    organization VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user' NOT NULL
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = TRUE;

-- Constraints
ALTER TABLE users ADD CONSTRAINT chk_email_format
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');

ALTER TABLE users ADD CONSTRAINT chk_username_format
    CHECK (username ~* '^[a-zA-Z0-9_]{3,50}$');
```

**Columns:**

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| id | UUID | Primary key | No |
| email | VARCHAR(255) | User email (unique) | No |
| username | VARCHAR(100) | Username (unique) | No |
| hashed_password | VARCHAR(255) | Bcrypt hashed password | No |
| full_name | VARCHAR(255) | User's full name | Yes |
| avatar_url | VARCHAR(500) | Profile picture URL | Yes |
| is_active | BOOLEAN | Account active status | No |
| is_verified | BOOLEAN | Email verified | No |
| is_superuser | BOOLEAN | Admin privileges | No |
| role | VARCHAR(50) | User role (user, admin, analyst) | No |
| bio | TEXT | User biography | Yes |
| organization | VARCHAR(255) | Organization name | Yes |
| created_at | TIMESTAMP | Account creation time | No |
| updated_at | TIMESTAMP | Last update time | No |
| last_login_at | TIMESTAMP | Last successful login | Yes |

### voice_submissions

Stores metadata about uploaded voice recordings.

```sql
CREATE TABLE voice_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    file_format VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    duration FLOAT,
    sample_rate INTEGER,
    channels INTEGER,
    title VARCHAR(255),
    description TEXT,
    tags JSON,
    category VARCHAR(100),
    source VARCHAR(50),
    source_url VARCHAR(500),
    user_agent VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    is_processed BOOLEAN DEFAULT FALSE NOT NULL,
    is_transcribed BOOLEAN DEFAULT FALSE NOT NULL,
    is_analyzed BOOLEAN DEFAULT FALSE NOT NULL,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 NOT NULL
);

-- Indexes
CREATE INDEX idx_submissions_user_id ON voice_submissions(user_id);
CREATE INDEX idx_submissions_status ON voice_submissions(status);
CREATE INDEX idx_submissions_created_at ON voice_submissions(created_at DESC);
CREATE INDEX idx_submissions_category ON voice_submissions(category);
CREATE INDEX idx_submissions_user_created ON voice_submissions(user_id, created_at DESC);
CREATE INDEX idx_submissions_processing ON voice_submissions(status, retry_count)
    WHERE status IN ('pending', 'failed');

-- Constraints
ALTER TABLE voice_submissions ADD CONSTRAINT chk_file_size
    CHECK (file_size > 0 AND file_size <= 52428800);  -- Max 50MB

ALTER TABLE voice_submissions ADD CONSTRAINT chk_duration
    CHECK (duration IS NULL OR (duration > 0 AND duration <= 600));  -- Max 10min

ALTER TABLE voice_submissions ADD CONSTRAINT chk_status
    CHECK (status IN ('pending', 'processing', 'completed', 'failed'));
```

**Columns:**

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| id | UUID | Primary key | No |
| user_id | UUID | Foreign key to users | No |
| file_path | VARCHAR(500) | S3/cloud storage path | No |
| file_name | VARCHAR(255) | Original filename | No |
| file_size | INTEGER | File size in bytes | No |
| file_format | VARCHAR(50) | Audio format (wav, mp3, etc.) | No |
| mime_type | VARCHAR(100) | MIME type | No |
| duration | FLOAT | Audio duration in seconds | Yes |
| sample_rate | INTEGER | Sample rate in Hz | Yes |
| channels | INTEGER | Number of channels (1=mono, 2=stereo) | Yes |
| title | VARCHAR(255) | Submission title | Yes |
| description | TEXT | Submission description | Yes |
| tags | JSON | Array of tags | Yes |
| category | VARCHAR(100) | Submission category | Yes |
| source | VARCHAR(50) | Source platform (web, mobile, extension) | Yes |
| source_url | VARCHAR(500) | URL where feedback was given | Yes |
| user_agent | VARCHAR(500) | User agent string | Yes |
| status | VARCHAR(50) | Processing status | No |
| is_processed | BOOLEAN | Processing complete flag | No |
| is_transcribed | BOOLEAN | Transcription complete flag | No |
| is_analyzed | BOOLEAN | Analysis complete flag | No |
| is_public | BOOLEAN | Public visibility flag | No |
| created_at | TIMESTAMP | Upload time | No |
| updated_at | TIMESTAMP | Last update time | No |
| processed_at | TIMESTAMP | Processing completion time | Yes |
| error_message | TEXT | Error details if failed | Yes |
| retry_count | INTEGER | Number of retry attempts | No |

### transcriptions

Stores speech-to-text transcription results.

```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID UNIQUE NOT NULL REFERENCES voice_submissions(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    language VARCHAR(10),
    confidence FLOAT,
    words JSON,
    segments JSON,
    model VARCHAR(100),
    model_version VARCHAR(50),
    provider VARCHAR(50),
    processing_time FLOAT,
    audio_duration FLOAT,
    word_count INTEGER,
    speaking_rate FLOAT,
    silence_duration FLOAT,
    detected_language VARCHAR(10),
    language_confidence FLOAT,
    is_multilingual BOOLEAN DEFAULT FALSE NOT NULL,
    entities JSON,
    topics JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    error_message TEXT
);

-- Indexes
CREATE INDEX idx_transcriptions_submission_id ON transcriptions(submission_id);
CREATE INDEX idx_transcriptions_language ON transcriptions(language);
CREATE INDEX idx_transcriptions_created_at ON transcriptions(created_at DESC);
CREATE INDEX idx_transcriptions_confidence ON transcriptions(confidence DESC);
CREATE INDEX idx_transcriptions_text_search ON transcriptions USING gin(to_tsvector('english', text));

-- Full-text search
CREATE INDEX idx_transcriptions_fts ON transcriptions
    USING gin(to_tsvector('english', text));
```

**Columns:**

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| id | UUID | Primary key | No |
| submission_id | UUID | Foreign key to voice_submissions (unique) | No |
| text | TEXT | Transcribed text | No |
| language | VARCHAR(10) | ISO 639-1 language code | Yes |
| confidence | FLOAT | Overall confidence score (0-1) | Yes |
| words | JSON | Word-level timestamps and confidence | Yes |
| segments | JSON | Segment-level data | Yes |
| model | VARCHAR(100) | Model used (e.g., whisper-large-v3) | Yes |
| model_version | VARCHAR(50) | Model version | Yes |
| provider | VARCHAR(50) | Service provider (openai, assemblyai) | Yes |
| processing_time | FLOAT | Processing time in seconds | Yes |
| audio_duration | FLOAT | Audio duration in seconds | Yes |
| word_count | INTEGER | Number of words | Yes |
| speaking_rate | FLOAT | Words per minute | Yes |
| silence_duration | FLOAT | Total silence duration | Yes |
| detected_language | VARCHAR(10) | Auto-detected language | Yes |
| language_confidence | FLOAT | Language detection confidence | Yes |
| is_multilingual | BOOLEAN | Multiple languages detected | No |
| entities | JSON | Named entities, keywords | Yes |
| topics | JSON | Detected topics/themes | Yes |
| created_at | TIMESTAMP | Creation time | No |
| updated_at | TIMESTAMP | Last update time | No |
| error_message | TEXT | Error details if failed | Yes |

### analyses

Stores AI-powered sentiment and intent analysis results.

```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID UNIQUE NOT NULL REFERENCES voice_submissions(id) ON DELETE CASCADE,
    transcription_id UUID NOT NULL REFERENCES transcriptions(id) ON DELETE CASCADE,
    sentiment VARCHAR(50),
    sentiment_score FLOAT,
    sentiment_confidence FLOAT,
    sentiment_breakdown JSON,
    emotions JSON,
    dominant_emotion VARCHAR(50),
    emotion_confidence FLOAT,
    intent VARCHAR(100),
    intent_confidence FLOAT,
    sub_intents JSON,
    summary TEXT,
    key_points JSON,
    action_items JSON,
    topics JSON,
    categories JSON,
    tags JSON,
    entities JSON,
    keywords JSON,
    clarity_score FLOAT,
    urgency_score FLOAT,
    importance_score FLOAT,
    is_actionable BOOLEAN DEFAULT FALSE NOT NULL,
    requires_follow_up BOOLEAN DEFAULT FALSE NOT NULL,
    is_complaint BOOLEAN DEFAULT FALSE NOT NULL,
    is_positive_feedback BOOLEAN DEFAULT FALSE NOT NULL,
    model VARCHAR(100),
    model_version VARCHAR(50),
    provider VARCHAR(50),
    processing_time FLOAT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    error_message TEXT
);

-- Indexes
CREATE INDEX idx_analyses_submission_id ON analyses(submission_id);
CREATE INDEX idx_analyses_transcription_id ON analyses(transcription_id);
CREATE INDEX idx_analyses_sentiment ON analyses(sentiment);
CREATE INDEX idx_analyses_intent ON analyses(intent);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX idx_analyses_importance_score ON analyses(importance_score DESC);
CREATE INDEX idx_analyses_actionable ON analyses(is_actionable) WHERE is_actionable = TRUE;
CREATE INDEX idx_analyses_complaints ON analyses(is_complaint) WHERE is_complaint = TRUE;

-- Constraints
ALTER TABLE analyses ADD CONSTRAINT chk_sentiment
    CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed'));

ALTER TABLE analyses ADD CONSTRAINT chk_sentiment_score
    CHECK (sentiment_score >= -1 AND sentiment_score <= 1);

ALTER TABLE analyses ADD CONSTRAINT chk_scores
    CHECK (
        (clarity_score IS NULL OR (clarity_score >= 0 AND clarity_score <= 1)) AND
        (urgency_score IS NULL OR (urgency_score >= 0 AND urgency_score <= 1)) AND
        (importance_score IS NULL OR (importance_score >= 0 AND importance_score <= 1))
    );
```

## Indexes

### Index Strategy

**Primary Indexes:**
- All primary keys (automatic)
- Foreign keys for joins
- Unique constraints for data integrity

**Query Optimization Indexes:**
- Composite indexes for common query patterns
- Partial indexes for filtered queries
- GIN indexes for JSON and full-text search

**Index Maintenance:**
```sql
-- Reindex periodically
REINDEX TABLE voice_submissions;

-- Analyze for query planning
ANALYZE voice_submissions;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Remove unused indexes
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

## Relationships

```sql
-- One-to-Many: User to Submissions
users (1) ----< (N) voice_submissions

-- One-to-One: Submission to Transcription
voice_submissions (1) ---- (1) transcriptions

-- One-to-One: Submission to Analysis
voice_submissions (1) ---- (1) analyses

-- One-to-One: Transcription to Analysis
transcriptions (1) ---- (1) analyses
```

## Data Types

### UUID vs Integer

**Using UUID for primary keys:**
- Globally unique (distributed systems)
- Security (non-sequential)
- Merge-friendly (no conflicts)

### JSON Columns

**When to use JSON:**
- Flexible schema (tags, metadata)
- Nested structures (word timestamps)
- Frequently changing structure

**Example JSON structures:**

```json
// tags (voice_submissions)
["checkout", "payment", "ux"]

// words (transcriptions)
[
  {"word": "hello", "start": 0.0, "end": 0.5, "confidence": 0.99},
  {"word": "world", "start": 0.6, "end": 1.0, "confidence": 0.98}
]

// sentiment_breakdown (analyses)
{
  "positive": 0.75,
  "neutral": 0.20,
  "negative": 0.05
}
```

## Migrations

### Using Alembic

**Create Migration:**
```bash
alembic revision --autogenerate -m "Add new column"
```

**Apply Migration:**
```bash
alembic upgrade head
```

**Rollback Migration:**
```bash
alembic downgrade -1
```

### Sample Migration

```python
# migrations/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

## Best Practices

1. **Always use transactions** for data integrity
2. **Index frequently queried columns**
3. **Use appropriate data types** (don't use VARCHAR when TEXT is better)
4. **Add constraints** to enforce data integrity
5. **Use cascading deletes** carefully
6. **Regular VACUUM and ANALYZE** for performance
7. **Monitor query performance** with pg_stat_statements
8. **Use connection pooling** to reduce overhead
9. **Backup regularly** before migrations
10. **Test migrations** on staging first
