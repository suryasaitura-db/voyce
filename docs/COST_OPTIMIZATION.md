# Cost Optimization Guide

Strategies and best practices for optimizing costs in the Voyce Voice Feedback Platform.

## Table of Contents

- [Cost Overview](#cost-overview)
- [Infrastructure Costs](#infrastructure-costs)
- [Databricks Optimization](#databricks-optimization)
- [Storage Optimization](#storage-optimization)
- [Database Optimization](#database-optimization)
- [API Optimization](#api-optimization)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Cost Estimation](#cost-estimation)

## Cost Overview

### Major Cost Components

```
Monthly Cost Breakdown (Estimated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Databricks (40%)           $800 - $2,000
├── Serverless Compute     $500 - $1,200
├── SQL Warehouses         $200 - $600
└── Storage (Delta Lake)   $100 - $200

Cloud Storage (25%)        $500 - $1,250
├── Object Storage (S3)    $300 - $800
├── Data Transfer          $150 - $350
└── Request Costs          $50 - $100

Compute (20%)              $400 - $1,000
├── API Servers            $250 - $650
├── Load Balancer          $100 - $250
└── Auto-scaling           $50 - $100

Database (10%)             $200 - $500
└── RDS PostgreSQL         $200 - $500

Other (5%)                 $100 - $250
├── CloudFront/CDN         $50 - $150
├── Monitoring             $30 - $60
└── Misc Services          $20 - $40
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                     $2,000 - $5,000/month
```

## Infrastructure Costs

### Right-Sizing Compute Resources

**Development Environment:**
```yaml
# Use minimal resources for dev
api:
  instance_type: t3.small
  count: 1
  auto_scaling: disabled

database:
  instance_type: db.t3.micro
  storage: 20GB
```

**Production Environment:**
```yaml
# Optimized production setup
api:
  instance_type: t3.medium
  min_count: 2
  max_count: 10
  target_cpu: 70%  # Scale at 70% CPU

database:
  instance_type: db.t3.large
  storage: 100GB
  read_replicas: 1  # Only if needed
```

### Auto-Scaling Configuration

**Cost-Effective Auto-Scaling:**

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: voyce-api-hpa
spec:
  minReplicas: 2      # Minimum for availability
  maxReplicas: 10     # Cap maximum to control costs
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # Scale before performance degrades
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5min before scaling down
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100  # Scale up quickly
        periodSeconds: 30
```

### Spot/Preemptible Instances

**AWS Spot Instances:**
```python
# Use Spot instances for non-critical workloads
# Save up to 90% on compute costs

# In Terraform/CloudFormation
mixed_instances_policy {
  instances_distribution {
    on_demand_base_capacity = 2  # Always have 2 on-demand
    on_demand_percentage_above_base_capacity = 20  # 20% on-demand, 80% spot
    spot_allocation_strategy = "capacity-optimized"
  }
}
```

**Cost Savings:**
- Development: 70-90% savings (100% spot)
- Staging: 50-70% savings (mix of spot/on-demand)
- Production: 30-50% savings (mostly on-demand with spot for batch)

### Reserved Instances / Savings Plans

**For Stable Workloads:**
```
Reserved Instances (1-year commitment):
- t3.medium: ~40% savings
- db.t3.large: ~35% savings
- Total annual savings: $6,000 - $12,000

Compute Savings Plans (1-year commitment):
- Additional 10-15% on top of RI savings
```

## Databricks Optimization

### Serverless Compute

**Recommended Configuration:**
```yaml
# Use serverless for variable workloads
# Pay only for what you use

job_clusters:
  - job_cluster_key: main
    new_cluster:
      spark_version: 15.4.x-scala2.12
      autoscale:
        min_workers: 1    # Start small
        max_workers: 8    # Cap for cost control
      spark_conf:
        "spark.databricks.cluster.profile": "serverless"
        "spark.databricks.delta.optimizeWrite.enabled": "true"
        "spark.databricks.delta.autoCompact.enabled": "true"
```

**Cost Savings:**
- No idle cluster costs
- Instant start/stop
- 30-50% cheaper than classic compute

### Cluster Optimization

**Use Cluster Policies:**
```json
{
  "autotermination_minutes": {
    "type": "fixed",
    "value": 30
  },
  "cluster_type": {
    "type": "fixed",
    "value": "job"
  },
  "spark_conf.spark.databricks.cluster.profile": {
    "type": "fixed",
    "value": "serverless"
  },
  "node_type_id": {
    "type": "allowlist",
    "values": ["i3.xlarge", "i3.2xlarge"]
  }
}
```

**Photon Acceleration:**
```python
# Enable Photon for 2-3x performance improvement
# Cost: 20% premium, but 2-3x faster = net savings

spark_conf = {
    "spark.databricks.photon.enabled": "true"
}
```

### SQL Warehouse Optimization

**Serverless SQL Warehouse:**
```yaml
sql_warehouse:
  name: voyce-analytics
  cluster_size: Small        # Start small (2X-Small to 4X-Large)
  enable_serverless: true    # Serverless = auto-scaling
  auto_stop_mins: 10         # Stop after 10min idle
  min_num_clusters: 0        # Scale to zero
  max_num_clusters: 2        # Cap concurrent queries
```

**Cost Optimization:**
```python
# Schedule warehouse usage
# Stop during off-hours

import requests

def stop_warehouse_off_hours():
    # Stop warehouse outside business hours
    if current_hour < 8 or current_hour > 18:
        databricks_api.stop_warehouse(warehouse_id)
```

### Delta Lake Optimization

**Enable Auto-Optimize:**
```python
# Automatic file compaction
spark.sql("""
    ALTER TABLE voyce_catalog.bronze.audio_metadata
    SET TBLPROPERTIES (
        delta.autoOptimize.optimizeWrite = true,
        delta.autoOptimize.autoCompact = true
    )
""")

# Vacuum old files (reduces storage)
spark.sql("""
    VACUUM voyce_catalog.bronze.audio_metadata
    RETAIN 7 HOURS
""")
```

**Z-Ordering:**
```python
# Improve query performance = faster queries = lower costs
spark.sql("""
    OPTIMIZE voyce_catalog.silver.transcriptions
    ZORDER BY (user_id, created_at)
""")
```

### Data Lifecycle Management

**Tiered Storage:**
```python
# Move old data to cheaper storage

# Hot tier (0-30 days): Delta Lake
# Warm tier (31-180 days): Parquet on S3
# Cold tier (180+ days): S3 Glacier

def archive_old_data():
    # Archive data older than 180 days
    old_data = spark.sql("""
        SELECT * FROM voyce_catalog.silver.transcriptions
        WHERE created_at < current_date() - INTERVAL 180 DAYS
    """)

    # Write to S3 Glacier
    old_data.write.parquet("s3://voyce-archive/transcriptions/")

    # Delete from Delta
    spark.sql("""
        DELETE FROM voyce_catalog.silver.transcriptions
        WHERE created_at < current_date() - INTERVAL 180 DAYS
    """)
```

## Storage Optimization

### Object Storage (S3/Azure/GCS)

**Lifecycle Policies:**
```json
{
  "Rules": [
    {
      "Id": "Move to IA after 30 days",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "Delete after 1 year",
      "Status": "Enabled",
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

**Cost Savings:**
- Standard to IA: 50% savings
- IA to Glacier: Additional 75% savings
- Total: Up to 87.5% on old data

### Compression

**Audio File Compression:**
```python
# Convert high-quality WAV to compressed formats
# Reduce storage by 80-90%

from pydub import AudioSegment

def compress_audio(input_path, output_path):
    audio = AudioSegment.from_wav(input_path)

    # Export as compressed MP3
    audio.export(
        output_path,
        format="mp3",
        bitrate="64k",  # Good for voice
        parameters=["-ac", "1"]  # Mono
    )

    # Delete original if successful
    os.remove(input_path)
```

**Data Compression:**
```python
# Use compression for data storage
spark.sql("""
    CREATE TABLE voyce_catalog.silver.transcriptions
    USING DELTA
    TBLPROPERTIES (
        'delta.compression' = 'zstd'  # Better compression than snappy
    )
""")
```

### Deduplication

**Remove Duplicate Files:**
```python
import hashlib

def deduplicate_files():
    """Remove duplicate audio files"""
    file_hashes = {}

    for file in storage_service.list_files():
        file_hash = hashlib.md5(file.read()).hexdigest()

        if file_hash in file_hashes:
            # Duplicate found, delete
            storage_service.delete_file(file.path)
            # Update DB to point to original
            update_submission_file_path(file.id, file_hashes[file_hash])
        else:
            file_hashes[file_hash] = file.path
```

## Database Optimization

### Query Optimization

**Add Indexes:**
```sql
-- Analyze slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time * calls DESC
LIMIT 20;

-- Add appropriate indexes
CREATE INDEX CONCURRENTLY idx_submissions_user_created
ON voice_submissions(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_submissions_status
ON voice_submissions(status)
WHERE status IN ('pending', 'processing');

-- Partial index for active records
CREATE INDEX CONCURRENTLY idx_active_users
ON users(id)
WHERE is_active = true;
```

**Connection Pooling:**
```python
# Reduce connection overhead
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,         # Connections to maintain
    max_overflow=5,       # Additional connections allowed
    pool_recycle=3600,    # Recycle connections after 1 hour
    pool_pre_ping=True    # Test connections before use
)
```

### Read Replicas

**Use Replicas for Analytics:**
```python
# Separate read and write operations
# Reduces load on primary = smaller instance needed

# Write operations (primary)
write_engine = create_engine(PRIMARY_DB_URL)

# Read operations (replica)
read_engine = create_engine(REPLICA_DB_URL)

@app.get("/api/analytics/dashboard")
async def dashboard():
    # Use read replica for analytics
    with read_engine.connect() as conn:
        return conn.execute(analytics_query)
```

### Data Retention

**Automated Cleanup:**
```sql
-- Delete old records
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete submissions older than 2 years
    DELETE FROM voice_submissions
    WHERE created_at < CURRENT_DATE - INTERVAL '2 years';

    -- Delete orphaned transcriptions
    DELETE FROM transcriptions
    WHERE submission_id NOT IN (SELECT id FROM voice_submissions);

    -- Vacuum to reclaim space
    VACUUM ANALYZE;
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron
SELECT cron.schedule('cleanup-old-data', '0 2 * * 0', 'SELECT cleanup_old_data()');
```

## API Optimization

### Caching

**Redis Caching:**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Initialize cache
@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="voyce-cache")

# Cache expensive operations
@app.get("/api/analytics/dashboard")
@cache(expire=300)  # Cache for 5 minutes
async def dashboard():
    # Expensive query
    return expensive_analytics_query()

# Cache static data
@app.get("/api/categories")
@cache(expire=3600)  # Cache for 1 hour
async def get_categories():
    return {"categories": ["bug", "feature", "feedback"]}
```

**Cost Savings:**
- Reduce database queries by 60-80%
- Lower compute costs
- Faster response times

### Response Compression

**Enable GZIP:**
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Cost Savings:**
- Reduce bandwidth by 70-90%
- Lower data transfer costs

### Pagination

**Limit Response Sizes:**
```python
@app.get("/api/submissions")
async def list_submissions(
    page: int = 1,
    limit: int = 20,  # Default to 20, max 100
    max_limit: int = 100
):
    limit = min(limit, max_limit)  # Enforce maximum
    offset = (page - 1) * limit

    return query.limit(limit).offset(offset)
```

## Monitoring and Alerts

### Cost Anomaly Detection

**AWS Cost Explorer API:**
```python
import boto3

def check_cost_anomalies():
    ce = boto3.client('ce')

    response = ce.get_anomalies(
        DateInterval={
            'StartDate': '2025-01-01',
            'EndDate': '2025-01-31'
        }
    )

    for anomaly in response['Anomalies']:
        if anomaly['Impact']['TotalImpact'] > 100:  # $100 increase
            send_alert(f"Cost anomaly detected: {anomaly}")
```

### Budget Alerts

**Set Up Budgets:**
```yaml
# AWS Budget
Budget:
  Name: Voyce-Monthly-Budget
  BudgetLimit:
    Amount: 3000
    Unit: USD
  TimeUnit: MONTHLY
  Notifications:
    - ComparisonOperator: GREATER_THAN
      Threshold: 80
      ThresholdType: PERCENTAGE
      NotificationType: ACTUAL
```

### Resource Tagging

**Tag All Resources:**
```python
# Consistent tagging for cost allocation
tags = {
    "Project": "voyce",
    "Environment": "production",
    "Component": "api",
    "CostCenter": "engineering",
    "ManagedBy": "terraform"
}

# Track costs by tag
# View costs per component, environment, etc.
```

## Cost Estimation

### Monthly Cost Calculator

**Small Scale (< 1000 users):**
```
API Servers:        2 x t3.small       = $30
Database:           db.t3.micro        = $15
Storage (S3):       100 GB             = $2
Databricks:         Serverless         = $200
Load Balancer:                         = $20
CDN:                1 TB transfer      = $10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                                 ~$280/month
```

**Medium Scale (1,000 - 10,000 users):**
```
API Servers:        5 x t3.medium      = $180
Database:           db.t3.large        = $130
Storage (S3):       1 TB               = $25
Databricks:         Serverless         = $800
Load Balancer:                         = $25
CDN:                10 TB transfer     = $100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                                 ~$1,260/month
```

**Large Scale (10,000+ users):**
```
API Servers:        20 x t3.large      = $1,200
Database:           db.r5.xlarge       = $350
Storage (S3):       10 TB              = $240
Databricks:         Serverless         = $2,000
Load Balancer:                         = $50
CDN:                100 TB transfer    = $1,000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                                 ~$4,840/month
```

## Cost Optimization Checklist

- [ ] Use serverless/auto-scaling for variable workloads
- [ ] Implement auto-stop for idle resources
- [ ] Enable data lifecycle policies
- [ ] Use spot/preemptible instances for batch jobs
- [ ] Implement caching (Redis, CDN)
- [ ] Optimize database queries and indexes
- [ ] Use read replicas for analytics
- [ ] Enable compression (GZIP, data compression)
- [ ] Set up cost alerts and budgets
- [ ] Regular cost review meetings
- [ ] Archive old data to cheaper storage
- [ ] Remove unused resources
- [ ] Right-size instances based on metrics
- [ ] Use reserved instances for stable workloads
- [ ] Implement request rate limiting
- [ ] Optimize images and static assets
- [ ] Monitor and eliminate data transfer costs
- [ ] Use multi-region only when necessary

## Cost Optimization Tools

- **AWS Cost Explorer**: Analyze spending patterns
- **AWS Trusted Advisor**: Get cost optimization recommendations
- **Databricks Cost Analysis**: Monitor Databricks spending
- **Grafana Dashboards**: Visualize cost metrics
- **CloudHealth**: Multi-cloud cost management
- **Spot.io**: Automated spot instance management

## Best Practices

1. **Review costs weekly**: Catch anomalies early
2. **Tag everything**: Enable detailed cost allocation
3. **Automate cleanup**: Remove unused resources automatically
4. **Use cost budgets**: Set alerts before overspending
5. **Optimize continuously**: Cost optimization is ongoing
6. **Test cost impact**: Measure before/after optimization
7. **Document decisions**: Track why resources exist
8. **Educate team**: Everyone should be cost-aware
