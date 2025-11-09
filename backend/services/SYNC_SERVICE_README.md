# Data Synchronization Service

This directory contains the data synchronization service for bidirectional sync between PostgreSQL and Databricks.

## Overview

The sync service handles:
- Syncing voice submissions from PostgreSQL to Databricks Delta tables
- Syncing AI analysis results back from Databricks to PostgreSQL
- Incremental sync based on timestamps (Change Data Capture pattern)
- Error handling and automatic retry logic
- Sync monitoring, validation, and logging
- Batch processing with configurable batch size
- Cost tracking and performance optimization

## Architecture

```
PostgreSQL (OLTP)  <---->  Data Sync Service  <---->  Databricks (OLAP)
                               ↓
                          Celery Tasks
                               ↓
                          Redis (Queue)
```

## Files

### 1. `databricks_client.py`
Databricks connection utilities and operations.

**Features:**
- JDBC connection setup using [DEFAULT] profile
- Delta Lake write operations (append, overwrite, merge)
- SQL execution utilities
- Unity Catalog operations
- Volume file operations (upload, download, list)
- Table optimization (OPTIMIZE, VACUUM)
- Schema evolution support

**Key Classes:**
- `DatabricksClient`: Main client for all Databricks operations

**Usage:**
```python
from services.databricks_client import get_databricks_client

# Get client
client = get_databricks_client()

# Write to Delta table
client.write_to_delta(
    df=pandas_dataframe,
    table_name="voice_submissions",
    mode="merge",
    merge_keys=["id"]
)

# Read from Delta table
df = client.read_from_delta(
    table_name="ai_analyses",
    where="created_at > '2024-01-01'"
)

# Execute SQL
results = client.execute_query("SELECT COUNT(*) FROM voice_submissions")
```

### 2. `sync_service.py`
Main sync orchestrator service.

**Features:**
- Incremental sync based on timestamps
- Batch processing (default: 1000 records)
- Bidirectional sync (PostgreSQL ↔ Databricks)
- Conflict resolution
- Data validation
- Sync metadata tracking
- Error handling and retry logic

**Key Classes:**
- `DataSyncService`: Main sync orchestrator
- `SyncMetadata`: Tracks sync state and history

**Usage:**
```python
from services.sync_service import get_sync_service

# Get sync service
sync_service = await get_sync_service()

# Sync submissions to Databricks
result = await sync_service.sync_submissions_to_databricks(
    incremental=True  # Only sync new/updated records
)

# Sync analyses back to PostgreSQL
result = await sync_service.sync_analyses_to_postgres(
    incremental=True
)

# Full bidirectional sync
result = await sync_service.full_bidirectional_sync()

# Validate sync
validation = await sync_service.validate_sync()
```

### 3. `sync_scheduler.py`
Celery tasks for scheduled synchronization.

**Features:**
- Hourly sync tasks
- Daily full sync and validation
- Manual sync triggers
- Sync status monitoring
- Alert on failures
- Task retry with exponential backoff
- Health checks

**Scheduled Tasks:**
- `sync-submissions-hourly`: Every hour at :00
- `sync-analyses-hourly`: Every hour at :30
- `full-bidirectional-sync-daily`: Daily at 2:00 AM
- `validate-sync-daily`: Daily at 3:00 AM
- `cleanup-old-sync-metadata`: Weekly on Sunday at 4:00 AM

**Usage:**
```python
from services.sync_scheduler import (
    trigger_immediate_sync,
    get_task_status,
    get_active_tasks
)

# Trigger manual sync
task_id = trigger_immediate_sync(
    sync_type="bidirectional",
    force_full=False
)

# Check task status
status = get_task_status(task_id)

# Get active tasks
active = get_active_tasks()
```

## Setup

### 1. Install Dependencies

```bash
cd /Users/suryasai.turaga/voyce/backend
pip install -r requirements.txt
```

New dependencies added:
- `databricks-sdk==0.17.0` - Databricks SDK
- `pyspark==3.5.0` - PySpark for data processing
- `pandas==2.1.4` - DataFrame operations
- `celery==5.3.4` - Task scheduling
- `redis==5.0.1` - Celery broker/backend

### 2. Configure Environment Variables

Add to your `.env` file:

```env
# Databricks settings (uses [DEFAULT] profile from ~/.databrickscfg)
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/xxxxx
DATABRICKS_ACCESS_TOKEN=dapi...
DATABRICKS_CATALOG=main
DATABRICKS_SCHEMA=voyce

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Sync settings
SYNC_BATCH_SIZE=1000
SYNC_INTERVAL_MINUTES=60
```

### 3. Configure Databricks Profile

Create or update `~/.databrickscfg`:

```ini
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = dapi...
```

### 4. Start Redis (required for Celery)

```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Or run manually
redis-server
```

### 5. Initialize Sync Service

```python
from services.sync_service import get_sync_service

# Initialize (creates tables and metadata)
sync_service = await get_sync_service()
```

### 6. Start Celery Worker

```bash
cd /Users/suryasai.turaga/voyce/backend

# Start worker
celery -A services.sync_scheduler:celery_app worker \
    --loglevel=info \
    --queues=sync,validation,maintenance

# Start beat scheduler (for periodic tasks)
celery -A services.sync_scheduler:celery_app beat \
    --loglevel=info
```

### 7. Start Celery Flower (Optional - Web UI)

```bash
pip install flower
celery -A services.sync_scheduler:celery_app flower
# Access at http://localhost:5555
```

## Database Schema

### PostgreSQL Tables

#### sync_metadata
Tracks sync operations and state.

```sql
CREATE TABLE sync_metadata (
    id UUID PRIMARY KEY,
    sync_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    last_sync_timestamp TIMESTAMP WITH TIME ZONE,
    last_sync_id VARCHAR(36),
    records_synced INTEGER,
    sync_status VARCHAR(50),
    error_message TEXT,
    sync_duration_seconds FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(sync_type, table_name)
);
```

### Databricks Delta Tables

#### voice_submissions
Synced from PostgreSQL.

```sql
CREATE TABLE main.voyce.voice_submissions (
    id STRING NOT NULL,
    user_id STRING NOT NULL,
    file_path STRING,
    file_name STRING,
    -- ... all fields from PostgreSQL ...
    synced_at TIMESTAMP
) USING DELTA;
```

#### ai_analyses
Synced to PostgreSQL.

```sql
CREATE TABLE main.voyce.ai_analyses (
    id STRING NOT NULL,
    submission_id STRING NOT NULL,
    sentiment STRING,
    sentiment_score DOUBLE,
    -- ... all analysis fields ...
    synced_at TIMESTAMP
) USING DELTA;
```

## Usage Examples

### Manual Sync via Python

```python
import asyncio
from services.sync_service import get_sync_service

async def sync_data():
    # Get service
    sync_service = await get_sync_service(
        batch_size=1000,
        sync_interval_minutes=60
    )

    # Incremental sync (only new/updated records)
    result = await sync_service.sync_submissions_to_databricks(
        incremental=True
    )
    print(f"Synced {result['records_synced']} submissions")

    # Force full sync
    result = await sync_service.sync_submissions_to_databricks(
        force_full_sync=True
    )

    # Get sync status
    status = await sync_service.get_sync_status()
    print(status)

# Run
asyncio.run(sync_data())
```

### Manual Sync via Celery

```python
from services.sync_scheduler import manual_sync_trigger, get_task_status

# Trigger sync
task_id = manual_sync_trigger(
    sync_type="bidirectional",
    force_full=False
)

# Check status
status = get_task_status(task_id)
print(status)
```

### API Integration (FastAPI)

```python
from fastapi import APIRouter, BackgroundTasks
from services.sync_scheduler import trigger_immediate_sync

router = APIRouter()

@router.post("/admin/sync")
async def trigger_sync(sync_type: str = "bidirectional"):
    """Trigger manual data sync."""
    task_id = trigger_immediate_sync(sync_type=sync_type)
    return {"task_id": task_id, "status": "triggered"}

@router.get("/admin/sync/status")
async def get_sync_status():
    """Get sync status."""
    from services.sync_service import get_sync_service
    sync_service = await get_sync_service()
    return await sync_service.get_sync_status()
```

## Monitoring

### Sync Metadata Queries

```sql
-- Recent sync history
SELECT
    sync_type,
    table_name,
    last_sync_timestamp,
    records_synced,
    sync_status,
    sync_duration_seconds
FROM sync_metadata
ORDER BY updated_at DESC;

-- Failed syncs
SELECT *
FROM sync_metadata
WHERE sync_status = 'failed'
ORDER BY updated_at DESC;

-- Sync performance
SELECT
    table_name,
    AVG(sync_duration_seconds) as avg_duration,
    AVG(records_synced) as avg_records,
    COUNT(*) as sync_count
FROM sync_metadata
WHERE sync_status = 'completed'
GROUP BY table_name;
```

### Celery Monitoring

```bash
# Check active tasks
celery -A services.sync_scheduler:celery_app inspect active

# Check scheduled tasks
celery -A services.sync_scheduler:celery_app inspect scheduled

# Check registered tasks
celery -A services.sync_scheduler:celery_app inspect registered
```

## Error Handling

### Automatic Retry
- Tasks automatically retry on failure (max 3 retries)
- Exponential backoff between retries (5-10 minutes)
- Failed tasks logged with full traceback

### Conflict Resolution
- Merge operations use `id` as primary key
- Last-write-wins for conflicts
- All sync operations are tracked in metadata

### Data Validation
- Validates record counts between systems
- Alerts on sync discrepancies
- Daily validation task runs at 3 AM

## Performance Optimization

### Batch Processing
- Default batch size: 1000 records
- Configurable via `SYNC_BATCH_SIZE`
- Reduces memory usage and improves throughput

### Delta Lake Optimization
- Regular `OPTIMIZE` operations
- Z-ordering on frequently queried columns
- `VACUUM` to clean up old files

### Cost Tracking
- Sync duration tracked in metadata
- Token usage logged for API calls
- Resource utilization monitored

## Best Practices

1. **Incremental Sync**: Always use incremental sync for scheduled tasks
2. **Full Sync**: Run full sync weekly or monthly for validation
3. **Monitoring**: Set up alerts for failed syncs
4. **Validation**: Run validation tasks regularly
5. **Optimization**: Optimize Delta tables monthly
6. **Cleanup**: Clean old metadata records (90+ days)

## Troubleshooting

### Common Issues

**Issue: Sync fails with "Table not found"**
```python
# Solution: Initialize tables
client = get_databricks_client()
client.create_table_if_not_exists("voice_submissions", schema_ddl)
```

**Issue: Celery tasks not running**
```bash
# Check Redis connection
redis-cli ping

# Check Celery workers
celery -A services.sync_scheduler:celery_app inspect active
```

**Issue: Sync performance slow**
```python
# Increase batch size
sync_service = await get_sync_service(batch_size=5000)

# Optimize Delta table
client.optimize_table("voice_submissions", z_order_by=["created_at"])
```

## Security

- Uses Databricks authentication via token or profile
- Row-level security supported via Unity Catalog
- All connections encrypted (TLS/SSL)
- Sensitive data masked in logs

## Support

For issues or questions:
1. Check logs: `/var/log/celery/`
2. Review sync metadata table
3. Check Celery Flower dashboard
4. Contact data engineering team

## License

Internal use only - Voyce Platform
