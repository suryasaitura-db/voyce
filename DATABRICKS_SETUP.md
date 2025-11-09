# 🔧 Databricks-Only Setup Guide

This guide shows how to deploy Voyce using **only Databricks services** - no local PostgreSQL or Redis installation required!

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  DATABRICKS SERVICES                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │   PostgreSQL     │      │   Unity Catalog  │        │
│  │   Instance       │      │   (voyce)        │        │
│  │   (Database)     │      │   (ML/Analytics) │        │
│  └──────────────────┘      └──────────────────┘        │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │   Workspace API  │      │   SQL Warehouse  │        │
│  │   (OAuth Token)  │      │   (Queries)      │        │
│  └──────────────────┘      └──────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
                    ┌──────┴──────┐
                    │   Voyce App  │
                    │   (Backend)  │
                    └──────────────┘
```

---

## ✅ What You Have (Already Configured)

### 1. Databricks PostgreSQL Instance
```
Host: instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com
Port: 5432
Database: databricks_postgres
User: suryasai.turaga@databricks.com
SSL: Required
```

### 2. Unity Catalog
```
Catalog: voyce
Schema: databricks_postgres
```

### 3. OAuth Token (Auto-rotating)
```
Token expires: ~1 hour
Auto-refresh: Configured in backend/services/databricks_oauth.py
```

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Set PostgreSQL Password

```bash
# Set your PostgreSQL password
export PGPASSWORD="your-databricks-postgres-password"

# Verify it's set
echo $PGPASSWORD
```

### Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/suryasai87/voyce.git
cd voyce

# The .env is already configured with your Databricks services!
# Just verify it looks correct
cat .env | grep DATABRICKS
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 4: Initialize Database Schema

```bash
# Set password for psql
export PGPASSWORD="your-password"

# Initialize schema in Databricks PostgreSQL
python scripts/init_db.py
```

### Step 5: Start Backend

```bash
# Start the backend
python main.py

# ✅ Backend running at: http://localhost:8000
# ✅ API Docs: http://localhost:8000/api/docs
```

### Step 6: Start Frontend (Optional)

```bash
# In a new terminal
cd frontend
npm install
npm run dev

# ✅ Frontend running at: http://localhost:3000
```

---

## 📋 About Redis

### Do You Need Redis?

Redis is used for:
1. **Celery task queue** - Background job processing
2. **Caching** - Faster API responses

### Options:

#### Option A: Skip Redis (Simplest)
For basic testing, you can run without Redis:
- Background jobs will run synchronously
- No caching (slightly slower but works fine)

#### Option B: Use Upstash Redis (Recommended - Free)
```bash
# 1. Sign up at https://upstash.com (free tier)
# 2. Create Redis database
# 3. Get connection string

# 4. Update .env
REDIS_HOST=your-redis.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-password
CELERY_BROKER_URL=redis://default:password@host:6379
```

#### Option C: Use Databricks as Queue (Advanced)
You could use Databricks Delta tables as a job queue:
- Create a `job_queue` table in `voyce` catalog
- Poll for jobs periodically
- This is more complex but possible

**Recommendation**: Use Upstash free tier (10K requests/day, enough for development)

---

## 🔐 OAuth Token Management

### Token Info

Your OAuth token:
- **Expires**: ~1 hour from issue time
- **Issued**: 2025-01-09 (check exact time in token)
- **Scopes**: iam.current-user:read, iam.groups:read, etc.

### Auto-Rotation

The backend automatically:
1. Checks token expiry
2. Warns when token expires soon
3. Logs when token needs refresh

### Manual Token Refresh

When token expires, refresh it:

```bash
# Option 1: Databricks CLI
databricks auth login --host https://fe-vm-hls-amer.cloud.databricks.com

# Get new token
databricks auth token --host https://fe-vm-hls-amer.cloud.databricks.com

# Update .env with new token
```

---

## 📊 Unity Catalog Setup

### Verify Catalog

```python
from databricks.sdk import WorkspaceClient

# Using OAuth token
w = WorkspaceClient(
    host="https://fe-vm-hls-amer.cloud.databricks.com",
    token="your-oauth-token"
)

# List catalogs
catalogs = w.catalogs.list()
for catalog in catalogs:
    print(f"Catalog: {catalog.name}")

# Should see: voyce
```

### Create Volume for Audio Files

```sql
-- In Databricks SQL Editor
USE CATALOG voyce;
USE SCHEMA databricks_postgres;

-- Create volume for audio storage
CREATE VOLUME IF NOT EXISTS audio_files;

-- Verify
SHOW VOLUMES IN databricks_postgres;
```

---

## 🧪 Testing the Setup

### 1. Test Database Connection

```bash
# Using psql
PGPASSWORD=your-password psql \
  "postgresql://suryasai.turaga%40databricks.com@instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require" \
  -c "SELECT version();"

# Should return PostgreSQL version
```

### 2. Test OAuth Token

```bash
# Test token validity
python -c "
from backend.services.databricks_oauth import get_oauth_manager

manager = get_oauth_manager()
info = manager.get_token_info()

print('Token Info:')
for key, value in info.items():
    print(f'  {key}: {value}')
"
```

### 3. Test Backend API

```bash
# Start backend
python main.py

# In another terminal, test health
curl http://localhost:8000/health

# Test API docs (open in browser)
open http://localhost:8000/api/docs
```

---

## 📁 Database Schema

The schema is created in your Databricks PostgreSQL instance:

```
databricks_postgres (database)
├── public (schema)
    ├── users
    ├── voice_submissions
    ├── transcriptions
    ├── ai_analysis
    ├── sync_metadata
    ├── processing_costs
    └── audit_log
```

All tables are created by `scripts/init_db.py`.

---

## 🔄 Data Sync

### PostgreSQL ↔ Unity Catalog

Data flows:
1. **Voice submissions** → PostgreSQL (real-time)
2. **Sync job** (hourly) → Unity Catalog Delta tables
3. **ML processing** → Unity Catalog
4. **Results** → Back to PostgreSQL

This is handled by `backend/services/sync_service.py`.

---

## 💰 Cost Estimate

### Databricks Services

| Service | Usage | Cost |
|---------|-------|------|
| PostgreSQL | Always-on instance | ~$0.50-2/hour |
| Unity Catalog | Storage + queries | ~$5-20/month |
| SQL Warehouse | Serverless | Pay per query |
| Workspace API | OAuth tokens | Free |

**Estimated**: $50-100/month for development

### Optional: Upstash Redis
- **Free tier**: 10K requests/day
- **Pro tier**: $10/month (100K requests/day)

---

## 🎯 Environment Variables Reference

```bash
# Databricks PostgreSQL
POSTGRES_HOST=instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com
POSTGRES_PORT=5432
POSTGRES_DB=databricks_postgres
POSTGRES_USER=suryasai.turaga@databricks.com
POSTGRES_PASSWORD=${PGPASSWORD}
DATABASE_URL=postgresql+asyncpg://...?sslmode=require

# Databricks Workspace
DATABRICKS_HOST=https://fe-vm-hls-amer.cloud.databricks.com
DATABRICKS_OAUTH_TOKEN=eyJraWQiOiI2NDZi...
DATABRICKS_CATALOG=voyce
DATABRICKS_SCHEMA=databricks_postgres

# Optional: Redis (Upstash)
REDIS_HOST=your-redis.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-password
```

---

## 🚨 Troubleshooting

### Issue: "connection refused"
**Solution**: Check PGPASSWORD is set correctly

### Issue: "SSL required"
**Solution**: Make sure `sslmode=require` is in DATABASE_URL

### Issue: "OAuth token expired"
**Solution**: Refresh token using Databricks CLI
```bash
databricks auth token
```

### Issue: "Catalog not found"
**Solution**: Create catalog in Databricks SQL Editor
```sql
CREATE CATALOG IF NOT EXISTS voyce;
CREATE SCHEMA IF NOT EXISTS databricks_postgres;
```

---

## ✅ Summary

### What's Configured:
- ✅ Databricks PostgreSQL as primary database
- ✅ OAuth token with auto-rotation checking
- ✅ Unity Catalog (`voyce` catalog)
- ✅ All services pointing to Databricks
- ✅ No local PostgreSQL needed

### What You Need:
- ✅ Set `PGPASSWORD` environment variable
- ✅ (Optional) Sign up for Upstash Redis free tier
- ✅ Run `python scripts/init_db.py`
- ✅ Start backend: `python main.py`

### URLs After Start:
- **Backend**: http://localhost:8000/api/docs
- **Frontend**: http://localhost:3000 (if running)
- **Database**: Databricks PostgreSQL (cloud)
- **ML/Analytics**: Unity Catalog (cloud)

---

**Ready to deploy with 100% Databricks services!** 🚀

Just set your `PGPASSWORD` and run `python main.py`!
