# Upstash Redis Setup (5 Minutes)

## Why Upstash?

- **Free tier**: 10,000 requests/day (enough for ~300 voice submissions)
- **No credit card required** for free tier
- **Global low-latency** Redis
- **Serverless** - pay only for what you use
- **Works perfectly** with Databricks PostgreSQL setup

---

## Setup Steps

### 1. Create Upstash Account

Visit: https://upstash.com

- Click "Sign Up" (free, no credit card)
- Sign up with GitHub/Google or email

### 2. Create Redis Database

1. Click "Create Database"
2. Settings:
   - **Name**: voyce-redis
   - **Type**: Regional (faster) or Global (redundant)
   - **Region**: Choose closest to your Databricks workspace
     - If using `fe-vm-hls-amer` (US West), choose **US West**
   - **TLS**: Enabled (recommended)

3. Click "Create"

### 3. Get Connection Details

After creation, you'll see:

```
Endpoint: your-instance-12345.upstash.io
Port: 6379
Password: AXk7...your-password...xyz
```

### 4. Update Your .env File

Update these lines in `/Users/suryasai.turaga/voyce/.env`:

```bash
# Redis Configuration (Upstash)
REDIS_HOST=your-instance-12345.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=AXk7...your-password...xyz
REDIS_DB=0

# Celery (use Upstash)
CELERY_BROKER_URL=rediss://default:AXk7...your-password...xyz@your-instance-12345.upstash.io:6379
CELERY_RESULT_BACKEND=rediss://default:AXk7...your-password...xyz@your-instance-12345.upstash.io:6379/1
```

**Note**: Use `rediss://` (with double 's') for TLS-enabled connections.

### 5. Test Connection

```bash
# Test Redis connection
python -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    password=os.getenv('REDIS_PASSWORD'),
    ssl=True,
    decode_responses=True
)

# Test
r.set('test', 'Hello from Voyce!')
print(f'✅ Redis connected: {r.get(\"test\")}')
r.delete('test')
"
```

### 6. Start Backend with Redis

```bash
# Set PostgreSQL password
export PGPASSWORD="your-databricks-postgres-password"

# Start backend (with Celery workers)
python main.py

# In another terminal, start Celery worker
celery -A backend.tasks.celery_app worker --loglevel=info

# In another terminal, start Celery beat (scheduled tasks)
celery -A backend.tasks.celery_app beat --loglevel=info
```

---

## Alternative: Skip Redis for Quick Testing

If you want to test immediately without Redis:

### Option 1: Synchronous Processing

Comment out Celery in `backend/app/main.py`:

```python
# # Celery task queue
# from backend.tasks.celery_app import celery_app
# app.state.celery = celery_app
```

Jobs will process immediately in the request (slower but works).

### Option 2: Use In-Memory Queue

For quick testing, use Python's built-in queue:

```python
# In backend/app/main.py
from queue import Queue
app.state.job_queue = Queue()
```

Not recommended for production but fine for initial testing.

---

## Cost Comparison

### Development (10-50 submissions/day)

| Service | Cost |
|---------|------|
| **Upstash Free Tier** | $0 |
| **Databricks PostgreSQL** | ~$1-2/day |
| **Databricks Unity Catalog** | ~$0.10/day |
| **Total** | ~$30-60/month |

### Production (1000 submissions/day)

| Service | Cost |
|---------|------|
| **Upstash Pro** | $10/month (100K req/day) |
| **Databricks PostgreSQL** | ~$50/month |
| **Databricks Unity Catalog** | ~$5/month |
| **OpenAI Whisper** | ~$100/month |
| **Anthropic Claude** | ~$50/month |
| **Total** | ~$215/month |

---

## Monitoring Upstash Usage

View your usage at: https://console.upstash.com

- **Requests**: Current daily usage
- **Storage**: Current data size
- **Connections**: Active connections

Free tier limits:
- 10,000 requests/day
- 256 MB storage
- 100 concurrent connections

---

## Next Steps After Setup

1. ✅ Upstash Redis created and configured
2. Test Redis connection with test script above
3. Initialize Databricks PostgreSQL schema:
   ```bash
   export PGPASSWORD="your-password"
   python scripts/init_db.py
   ```
4. Start backend:
   ```bash
   python main.py  # Backend at http://localhost:8000
   ```
5. Start Celery workers:
   ```bash
   celery -A backend.tasks.celery_app worker --loglevel=info
   ```
6. Test voice submission via API docs: http://localhost:8000/api/docs

---

## Troubleshooting

### Error: "Connection refused"

**Solution**: Make sure you're using `rediss://` (with 's') for TLS connections.

### Error: "NOAUTH Authentication required"

**Solution**: Check that REDIS_PASSWORD is set correctly in .env

### Error: "Too many connections"

**Solution**: Free tier has 100 concurrent connections limit. Make sure to close connections properly.

---

## Summary

**Recommended Setup for Voyce**:

```
┌─────────────────────────────────────────────┐
│         DATABRICKS + UPSTASH STACK          │
├─────────────────────────────────────────────┤
│                                             │
│  ✅ Databricks PostgreSQL                   │
│     └─ Primary database                     │
│                                             │
│  ✅ Databricks Unity Catalog                │
│     └─ ML/Analytics (Delta Lake)            │
│                                             │
│  ✅ Databricks OAuth                        │
│     └─ Authentication/API access            │
│                                             │
│  ✅ Upstash Redis (FREE)                    │
│     └─ Celery task queue                    │
│     └─ Caching                              │
│                                             │
└─────────────────────────────────────────────┘
```

**Cost**: ~$30-60/month for development
**Setup time**: 5 minutes
**No local installations**: Everything cloud-based!

---

**Ready to deploy!** 🚀
