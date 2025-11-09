# Troubleshooting Guide

Common issues and solutions for the Voyce Voice Feedback Platform.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Issues](#database-issues)
- [API Issues](#api-issues)
- [Databricks Issues](#databricks-issues)
- [File Upload Issues](#file-upload-issues)
- [Authentication Issues](#authentication-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)
- [Logging and Debugging](#logging-and-debugging)

## Installation Issues

### Python Version Mismatch

**Problem:** `ERROR: Python version not supported`

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.9+
brew install python@3.9  # macOS
sudo apt install python3.9  # Ubuntu

# Use pyenv for version management
pyenv install 3.9.18
pyenv local 3.9.18
```

### Dependency Installation Fails

**Problem:** `pip install` fails with compilation errors

**Solution:**
```bash
# Install system dependencies first
# macOS
brew install postgresql

# Ubuntu
sudo apt-get install python3-dev libpq-dev

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Retry installation
pip install -r requirements.txt
```

### Virtual Environment Issues

**Problem:** `ModuleNotFoundError` even after installing packages

**Solution:**
```bash
# Deactivate current environment
deactivate

# Remove old environment
rm -rf venv

# Create fresh environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

## Database Issues

### Connection Refused

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Verify connection
psql -h localhost -U postgres -c "SELECT 1"
```

### Authentication Failed

**Problem:** `FATAL: password authentication failed for user`

**Solution:**
```bash
# Reset password
psql postgres
ALTER USER voyce_user WITH PASSWORD 'new_password';
\q

# Update .env file
DB_PASSWORD=new_password

# Or use peer authentication (Linux only)
sudo -u postgres psql
CREATE USER $USER WITH SUPERUSER;
```

### Database Does Not Exist

**Problem:** `FATAL: database "voyce_db" does not exist`

**Solution:**
```bash
# Create database
createdb voyce_db

# Or using psql
psql postgres
CREATE DATABASE voyce_db OWNER voyce_user;
\q
```

### Migration Errors

**Problem:** `alembic.util.exc.CommandError: Target database is not up to date`

**Solution:**
```bash
# Check current revision
alembic current

# Show all revisions
alembic history

# Stamp current state
alembic stamp head

# Run migrations
alembic upgrade head

# If still failing, reset migrations
dropdb voyce_db
createdb voyce_db
alembic upgrade head
```

### Connection Pool Exhausted

**Problem:** `QueuePool limit exceeded`

**Solution:**
```python
# Increase pool size in database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase from default 5
    max_overflow=40,  # Increase overflow
    pool_pre_ping=True,  # Check connections
    pool_recycle=3600  # Recycle after 1 hour
)
```

## API Issues

### Port Already in Use

**Problem:** `Address already in use: port 8000`

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn backend.app.main:app --port 8001
```

### CORS Errors

**Problem:** `Access to fetch at ... has been blocked by CORS policy`

**Solution:**
```python
# Update allowed origins in backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "chrome-extension://*"  # For Chrome extension
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Or in .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 422 Validation Errors

**Problem:** `422 Unprocessable Entity`

**Solution:**
```bash
# Check request payload matches Pydantic model
# Enable detailed error messages
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com"}' \
  -v

# Response will show missing required fields
```

### 500 Internal Server Error

**Problem:** Generic 500 error with no details

**Solution:**
```bash
# Enable debug mode in .env
DEBUG=True

# Check logs
tail -f logs/app.log

# Or run with verbose logging
uvicorn backend.app.main:app --log-level debug

# Add exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
```

## Databricks Issues

### Authentication Failed

**Problem:** `databricks.sdk.errors.Unauthenticated`

**Solution:**
```bash
# Verify Databricks configuration
cat ~/.databrickscfg

# Should contain:
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = dapi...

# Test connection
databricks workspace ls /

# Regenerate token in Databricks UI if needed
# User Settings > Developer > Access Tokens > Generate New Token
```

### Bundle Deployment Fails

**Problem:** `databricks bundle deploy` fails

**Solution:**
```bash
# Validate bundle first
databricks bundle validate -t dev

# Check for syntax errors in databricks.yml
# Ensure proper YAML indentation

# Verify workspace access
databricks workspace ls /Workspace/voyce

# Deploy with verbose output
databricks bundle deploy -t dev --verbose

# Check for permission issues
# Ensure user has CREATE, MANAGE permissions
```

### Notebook Not Found

**Problem:** `Notebook /Workspace/voyce/01_data_ingestion not found`

**Solution:**
```bash
# Upload notebook manually
databricks workspace import \
  ./databricks-notebooks/01_data_ingestion.py \
  /Workspace/voyce/01_data_ingestion \
  --language PYTHON

# Or use bundle sync
databricks bundle deploy -t dev
```

### Unity Catalog Errors

**Problem:** `catalog 'voyce_catalog' does not exist`

**Solution:**
```bash
# Run Unity Catalog setup notebook
# In Databricks UI, execute:
# /Workspace/voyce/00_unity_catalog_setup

# Or create manually
CREATE CATALOG IF NOT EXISTS voyce_catalog;
CREATE SCHEMA IF NOT EXISTS voyce_catalog.bronze;
CREATE SCHEMA IF NOT EXISTS voyce_catalog.silver;
CREATE SCHEMA IF NOT EXISTS voyce_catalog.gold;
```

## File Upload Issues

### File Size Limit Exceeded

**Problem:** `413 Request Entity Too Large`

**Solution:**
```nginx
# Update nginx configuration
client_max_body_size 100M;

# Reload nginx
sudo nginx -s reload
```

```python
# Update FastAPI limit
from fastapi import UploadFile, File

@app.post("/upload")
async def upload(file: UploadFile = File(..., max_length=52428800)):  # 50MB
    pass
```

### Invalid File Type

**Problem:** `400 Bad Request: Invalid file type`

**Solution:**
```python
# Verify MIME type checking
ALLOWED_MIME_TYPES = [
    'audio/wav',
    'audio/mpeg',
    'audio/mp4',
    'audio/x-m4a',
    'audio/ogg',
    'audio/flac'
]

# Check file extension validation
ALLOWED_EXTENSIONS = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
```

### Upload Timeout

**Problem:** Upload times out for large files

**Solution:**
```python
# Increase timeout in uvicorn
uvicorn backend.app.main:app --timeout-keep-alive 120

# Use chunked upload for large files
@app.post("/api/submissions/upload-chunked")
async def upload_chunked(
    chunk: UploadFile,
    chunk_number: int,
    total_chunks: int,
    file_id: str
):
    # Save chunk
    # Merge when all chunks received
    pass
```

### Storage Service Errors

**Problem:** `Failed to upload to S3/Azure/GCS`

**Solution:**
```bash
# Verify credentials
aws s3 ls  # AWS
az storage account list  # Azure
gcloud storage buckets list  # GCS

# Check bucket permissions
aws s3api get-bucket-policy --bucket voyce-audio

# Test upload manually
aws s3 cp test.wav s3://voyce-audio/test.wav

# Verify environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

## Authentication Issues

### Invalid Token

**Problem:** `401 Unauthorized: Invalid token`

**Solution:**
```bash
# Check token expiry
import jwt
token = "your_token_here"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded['exp'])

# Generate new token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Verify JWT_SECRET_KEY matches between environments
echo $JWT_SECRET_KEY
```

### Token Expired

**Problem:** `401 Unauthorized: Token has expired`

**Solution:**
```bash
# Use refresh token to get new access token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'

# Increase token expiration in .env (not recommended for production)
JWT_EXPIRATION_MINUTES=120
```

### Password Hash Mismatch

**Problem:** Login fails with correct password

**Solution:**
```python
# Verify password hashing
from backend.utils.security import hash_password, verify_password

# Test hash and verify
password = "TestPassword123!"
hashed = hash_password(password)
print(verify_password(password, hashed))  # Should be True

# Reset user password
psql voyce_db
UPDATE users SET hashed_password = '$2b$12$...' WHERE email = 'user@example.com';
```

## Performance Issues

### Slow API Response

**Problem:** API responses taking > 5 seconds

**Solution:**
```bash
# Enable SQL query logging
LOG_LEVEL=DEBUG

# Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Add database indexes
CREATE INDEX idx_submissions_user_created
ON voice_submissions(user_id, created_at);

# Enable query result caching
pip install fastapi-cache2[redis]

# Add caching decorator
from fastapi_cache.decorator import cache

@app.get("/api/analytics/dashboard")
@cache(expire=300)  # Cache for 5 minutes
async def dashboard():
    pass
```

### High Memory Usage

**Problem:** Application consuming > 2GB RAM

**Solution:**
```bash
# Monitor memory usage
ps aux | grep python

# Profile memory
pip install memory_profiler
python -m memory_profiler backend/app/main.py

# Reduce worker processes
uvicorn backend.app.main:app --workers 2

# Implement pagination
@app.get("/api/submissions")
async def list_submissions(page: int = 1, limit: int = 20):
    # Limit results
    offset = (page - 1) * limit
    return query.limit(limit).offset(offset)
```

### Database Connection Leaks

**Problem:** `too many connections` error

**Solution:**
```python
# Enable connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Always close sessions
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    finally:
        await close_db()
```

## Deployment Issues

### Docker Build Fails

**Problem:** `ERROR: Could not build wheels for...`

**Solution:**
```dockerfile
# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Use multi-stage build to reduce image size
FROM python:3.9-slim as builder
# ... build steps

FROM python:3.9-slim
COPY --from=builder /app /app
```

### Kubernetes Pod CrashLoopBackOff

**Problem:** Pod keeps restarting

**Solution:**
```bash
# Check pod logs
kubectl logs -f pod-name -n production

# Describe pod for events
kubectl describe pod pod-name -n production

# Common issues:
# 1. Missing environment variables
kubectl get configmap -n production
kubectl get secrets -n production

# 2. Failed health checks
# Adjust probe timing in deployment.yaml
livenessProbe:
  initialDelaySeconds: 60  # Increase if app starts slowly
  periodSeconds: 30

# 3. Resource limits
# Increase resource limits
resources:
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### SSL Certificate Issues

**Problem:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution:**
```bash
# Renew certificate with certbot
sudo certbot renew

# Or manually
sudo certbot certonly --nginx -d api.voyce.ai

# Verify certificate
openssl s_client -connect api.voyce.ai:443 -servername api.voyce.ai

# Check expiration
openssl x509 -in /etc/letsencrypt/live/api.voyce.ai/cert.pem -noout -dates
```

## Logging and Debugging

### Enable Debug Logging

```python
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Or programmatically
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### View Logs

```bash
# Application logs
tail -f logs/app.log

# Uvicorn access logs
tail -f logs/access.log

# Docker logs
docker logs -f container-name

# Kubernetes logs
kubectl logs -f deployment/voyce-api -n production

# Follow multiple pods
stern voyce-api -n production
```

### Debug API Requests

```bash
# Use curl with verbose mode
curl -v http://localhost:8000/api/health

# Or httpie
http --verbose GET http://localhost:8000/api/health

# With authentication
http GET http://localhost:8000/api/submissions \
  "Authorization:Bearer token"
```

### Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint (Python 3.7+)
breakpoint()

# Commands:
# n - next line
# s - step into
# c - continue
# p variable - print variable
# q - quit
```

## Getting Help

If issues persist:

1. **Check Logs**: Always check application and system logs
2. **Search Issues**: [GitHub Issues](https://github.com/suryasai87/voyce/issues)
3. **Documentation**: Review relevant documentation sections
4. **Stack Overflow**: Search for similar issues
5. **Create Issue**: Open a new GitHub issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Relevant logs
   - What you've tried

## Support Channels

- **GitHub Issues**: https://github.com/suryasai87/voyce/issues
- **Email**: support@voyce.ai
- **Documentation**: https://docs.voyce.ai
