# 🚀 Local Deployment Guide

## Prerequisites Status

Based on your system, here are the deployment options:

### ✅ Option 1: Docker Deployment (Recommended)
**Status**: Docker not currently installed

**Install Docker Desktop**:
1. Download from: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Run: `docker-compose up -d`

**Advantages**:
- All services included (PostgreSQL, Redis, Backend, Frontend)
- No manual configuration needed
- Clean isolation
- Easy to stop/start

### ✅ Option 2: Manual Installation
**Status**: PostgreSQL and Redis not currently installed

**Install Required Services** (macOS):
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL and Redis
brew install postgresql@15 redis

# Start services
brew services start postgresql@15
brew services start redis

# Continue with setup below
```

### ✅ Option 3: Cloud/Hosted Services (Recommended for Immediate Testing)
**Status**: Ready to use

Use managed cloud services:
- **Database**: Neon.tech (free tier) - PostgreSQL
- **Redis**: Upstash (free tier) - Redis
- **Backend**: Run locally
- **Frontend**: Run locally

---

## Quick Start (Recommended Path)

Since local services aren't installed, here's the fastest way to test:

### Step 1: Use Docker (Easiest)

```bash
# 1. Install Docker Desktop from https://www.docker.com/products/docker-desktop
# 2. Once Docker is running:

cd /Users/suryasai.turaga/voyce
docker-compose up -d

# 3. Initialize database
docker-compose exec backend python scripts/init_db.py

# 4. Access services
# - Backend: http://localhost:8000/api/docs
# - Frontend: http://localhost:3000
# - Flower: http://localhost:5555
```

### Step 2: Use Cloud Services (No Installation Required)

**A. Set up Neon PostgreSQL** (2 minutes):
```bash
# 1. Go to https://neon.tech
# 2. Sign up (free)
# 3. Create project "voyce"
# 4. Copy connection string

# 5. Update .env
DATABASE_URL=postgresql+asyncpg://user:pass@host.neon.tech/voyce_db
POSTGRES_HOST=host.neon.tech
POSTGRES_PORT=5432
POSTGRES_DB=voyce_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
```

**B. Set up Upstash Redis** (2 minutes):
```bash
# 1. Go to https://upstash.com
# 2. Sign up (free)
# 3. Create Redis database
# 4. Copy connection details

# 5. Update .env
REDIS_HOST=your-redis.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-password
CELERY_BROKER_URL=redis://default:password@host:6379
```

**C. Run Backend Locally**:
```bash
cd /Users/suryasai.turaga/voyce

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Initialize database (one time)
python scripts/init_db.py

# Start backend
python main.py
```

**D. Run Frontend Locally** (new terminal):
```bash
cd /Users/suryasai.turaga/voyce/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Current Deployment Status

### ✅ Ready
- [x] Code complete
- [x] Docker configuration
- [x] Environment configuration
- [x] Database schema
- [x] Documentation

### ⏳ Pending (Requires Installation)
- [ ] Docker Desktop installation
- [ ] OR PostgreSQL installation
- [ ] OR Cloud service setup (Neon/Upstash)

---

## Testing Without Full Setup

You can test the API documentation without starting services:

```bash
cd /Users/suryasai.turaga/voyce

# Install minimal dependencies
pip3 install fastapi uvicorn

# Run in demo mode (no database)
python3 -c "
from fastapi import FastAPI
app = FastAPI(title='Voyce API - Demo Mode')

@app.get('/')
def root():
    return {'message': 'Voyce API - Install Docker or PostgreSQL for full functionality'}

import uvicorn
uvicorn.run(app, host='localhost', port=8000)
"
```

Access: http://localhost:8000

---

## Recommended Next Steps

### For Immediate Testing (Fastest):
1. **Install Docker Desktop** (15 minutes)
   - Download: https://www.docker.com/products/docker-desktop
   - Install and start
   - Run: `docker-compose up -d`
   - Done! ✅

### For Production/Team Development:
1. **Use Cloud Services** (10 minutes)
   - Neon PostgreSQL (free tier)
   - Upstash Redis (free tier)
   - Share credentials with team
   - Everyone can develop locally

### For Full Local Setup:
1. **Install PostgreSQL and Redis** (20 minutes)
   ```bash
   brew install postgresql@15 redis
   brew services start postgresql@15
   brew services start redis
   ```

---

## URLs After Deployment

Once services are running:

| Service | URL | Status |
|---------|-----|--------|
| Backend API | http://localhost:8000 | ⏳ Waiting for deployment |
| API Docs | http://localhost:8000/api/docs | ⏳ Waiting for deployment |
| Frontend | http://localhost:3000 | ⏳ Waiting for deployment |
| Celery Flower | http://localhost:5555 | ⏳ Waiting for deployment |
| Prometheus | http://localhost:9090 | ⏳ Waiting for deployment |
| Grafana | http://localhost:3001 | ⏳ Waiting for deployment |

---

## Troubleshooting

### Issue: "docker: command not found"
**Solution**: Install Docker Desktop from https://www.docker.com/products/docker-desktop

### Issue: "psql: command not found"
**Solution**:
```bash
brew install postgresql@15
# OR use Docker
# OR use Neon.tech cloud database
```

### Issue: "redis-server: command not found"
**Solution**:
```bash
brew install redis
# OR use Docker
# OR use Upstash cloud Redis
```

---

## Summary

**Current Status**: Code is complete and ready. Infrastructure needs to be set up.

**Fastest Path to Testing**:
1. Install Docker Desktop (15 min)
2. Run `docker-compose up -d`
3. Access http://localhost:8000/api/docs

**Alternative**: Use cloud services (Neon + Upstash) - no local installation needed!

All code is committed and ready to push to GitHub for collaborator access.
