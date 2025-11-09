# Setup Guide

Complete guide for setting up the Voyce Voice Feedback Platform development environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Databricks Setup](#databricks-setup)
- [Running Locally](#running-locally)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python**: 3.9 or higher
- **Node.js**: 16.x or higher (for frontend)
- **PostgreSQL**: 13 or higher
- **Git**: Latest version
- **Docker**: Latest version (optional, for containerized development)
- **Databricks CLI**: Latest version

### Required Accounts

- **Databricks**: Workspace access with Unity Catalog enabled
- **Cloud Storage**: AWS S3, Azure Blob Storage, or Google Cloud Storage
- **Email Service**: For user notifications (optional)

## System Requirements

### Minimum Requirements

- **OS**: macOS, Linux, or Windows (WSL2 recommended)
- **RAM**: 8GB
- **Disk Space**: 10GB free
- **CPU**: 4 cores

### Recommended Requirements

- **RAM**: 16GB or more
- **Disk Space**: 20GB free
- **CPU**: 8 cores or more
- **SSD**: For better performance

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/suryasai87/voyce.git
cd voyce
```

### 2. Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Development Dependencies

```bash
pip install -r requirements-dev.txt  # If available
```

Or install individual development tools:

```bash
pip install pytest pytest-asyncio black flake8 mypy
```

### 5. Install Frontend Dependencies (Optional)

If you're working with the frontend:

```bash
cd frontend
npm install
cd ..
```

### 6. Install Databricks CLI

**macOS:**
```bash
brew tap databricks/tap
brew install databricks
```

**Linux/Windows:**
```bash
pip install databricks-cli
```

## Configuration

### 1. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Application Settings
HOST=localhost
PORT=8000
DEBUG=True
ENVIRONMENT=development
APP_NAME=voyce

# Database Configuration
DB_BACKEND=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voyce_db
DB_USER=voyce_user
DB_PASSWORD=your_secure_password

# Databricks Configuration
DATABRICKS_PROFILE=DEFAULT
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_databricks_token

# Cloud Storage (choose one)
# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=voyce-audio-files

# Azure Blob Storage
# AZURE_STORAGE_CONNECTION_STRING=your_connection_string
# AZURE_CONTAINER_NAME=voyce-audio-files

# Google Cloud Storage
# GCS_CREDENTIALS_PATH=/path/to/credentials.json
# GCS_BUCKET_NAME=voyce-audio-files

# Security
SECRET_KEY=your_super_secret_key_change_this_in_production
JWT_SECRET_KEY=your_jwt_secret_key_change_this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
REFRESH_TOKEN_EXPIRATION_DAYS=7

# API Configuration
API_VERSION=v1
API_PREFIX=/api
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# CORS Settings
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

# File Upload Settings
MAX_FILE_SIZE_MB=50
ALLOWED_AUDIO_FORMATS=wav,mp3,m4a,ogg,flac
MAX_AUDIO_DURATION_SECONDS=600

# ML/AI Configuration
WHISPER_MODEL=whisper-large-v3
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@voyce.ai

# Redis (optional, for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Monitoring
PROMETHEUS_ENABLED=True
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2. Generate Secret Keys

Generate secure secret keys:

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and update your `.env` file.

### 3. Configure Databricks

Create `~/.databrickscfg`:

```bash
mkdir -p ~/.databricks
cat > ~/.databrickscfg << EOF
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = your_databricks_token
EOF
```

Set appropriate permissions:

```bash
chmod 600 ~/.databrickscfg
```

## Database Setup

### 1. Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download installer from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database and User

```bash
# Connect to PostgreSQL
psql postgres

# Create user
CREATE USER voyce_user WITH PASSWORD 'your_secure_password';

# Create database
CREATE DATABASE voyce_db OWNER voyce_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE voyce_db TO voyce_user;

# Exit
\q
```

### 3. Verify Database Connection

```bash
psql -h localhost -U voyce_user -d voyce_db -c "SELECT version();"
```

### 4. Initialize Database Schema

Run migrations to create tables:

```bash
# Using Alembic (if configured)
alembic upgrade head

# Or run the initialization script
python -c "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. Verify Tables

```bash
psql -h localhost -U voyce_user -d voyce_db

# List tables
\dt

# Expected tables:
# - users
# - voice_submissions
# - transcriptions
# - analyses

\q
```

## Databricks Setup

### 1. Configure Unity Catalog

Run the Unity Catalog setup notebook:

```bash
databricks workspace import \
  ./databricks-notebooks/00_unity_catalog_setup.py \
  /Workspace/voyce/00_unity_catalog_setup \
  --language PYTHON
```

Execute the notebook in your Databricks workspace to create:
- Catalog: `voyce_catalog`
- Schemas: `bronze`, `silver`, `gold`
- Tables and permissions

### 2. Upload Notebooks

Upload all processing notebooks:

```bash
# Data Ingestion
databricks workspace import \
  ./databricks-notebooks/01_data_ingestion.py \
  /Workspace/voyce/01_data_ingestion \
  --language PYTHON

# Voice Processing
databricks workspace import \
  ./databricks-notebooks/02_voice_processing.py \
  /Workspace/voyce/02_voice_processing \
  --language PYTHON

# Sentiment Analysis
databricks workspace import \
  ./databricks-notebooks/03_sentiment_analysis.py \
  /Workspace/voyce/03_sentiment_analysis \
  --language PYTHON

# Model Training
databricks workspace import \
  ./databricks-notebooks/05_model_training.py \
  /Workspace/voyce/05_model_training \
  --language PYTHON

# Batch Inference
databricks workspace import \
  ./databricks-notebooks/06_batch_inference.py \
  /Workspace/voyce/06_batch_inference \
  --language PYTHON
```

### 3. Configure Bundle

Deploy Databricks Asset Bundle:

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

### 4. Create SQL Warehouse

In Databricks UI:
1. Go to SQL Warehouses
2. Create new warehouse named `voyce-sql-warehouse`
3. Enable Serverless
4. Set Auto-stop to 10 minutes

## Running Locally

### 1. Start Database

Ensure PostgreSQL is running:

```bash
# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql

# Check status
pg_isready
```

### 2. Start Redis (Optional)

If using caching:

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Verify
redis-cli ping  # Should return PONG
```

### 3. Start Backend

**Option 1: Using Python directly**

```bash
source venv/bin/activate  # Activate virtual environment
python main.py
```

**Option 2: Using the run script**

```bash
chmod +x run_local.sh
./run_local.sh
```

**Option 3: Using uvicorn directly**

```bash
uvicorn backend.app.main:app --reload --host localhost --port 8000
```

The backend will be available at: `http://localhost:8000`

### 4. Start Frontend (Optional)

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at: `http://localhost:3000`

### 5. Load Chrome Extension (Optional)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `chrome-extension` directory

## Verification

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development",
  "database": "postgresql",
  "version": "1.0.0"
}
```

### 2. Check API Documentation

Open browser: `http://localhost:8000/api/docs`

You should see the Swagger UI with all API endpoints.

### 3. Test Database Connection

```bash
python -c "
from backend.app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful!')
"
```

### 4. Test Databricks Connection

```bash
databricks workspace ls /Workspace/voyce
```

Should list uploaded notebooks.

### 5. Test File Upload

```bash
# Create a test audio file
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123!"
  }'

# Login and get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!"
  }'
```

## Development Tools Setup

### 1. Configure IDE

**VS Code:**

Install recommended extensions:
- Python
- Pylance
- Black Formatter
- autoDocstring
- GitLens

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

### 2. Configure Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

### 3. Setup Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Troubleshooting

### Database Connection Issues

**Error: `FATAL: password authentication failed`**

Solution:
```bash
# Reset password
psql postgres
ALTER USER voyce_user WITH PASSWORD 'new_password';
\q

# Update .env file with new password
```

**Error: `could not connect to server`**

Solution:
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql     # Linux
```

### Databricks Connection Issues

**Error: `Invalid token`**

Solution:
```bash
# Generate new token in Databricks UI
# Update ~/.databrickscfg and .env file
```

### Python Import Errors

**Error: `ModuleNotFoundError`**

Solution:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Port Already in Use

**Error: `Address already in use`**

Solution:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn backend.app.main:app --port 8001
```

## Next Steps

After successful setup:

1. Read [API Documentation](./API.md)
2. Review [Architecture](./ARCHITECTURE.md)
3. Check [Contributing Guidelines](./CONTRIBUTING.md)
4. Follow [Deployment Guide](./DEPLOYMENT.md)

## Support

If you encounter issues:

1. Check [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Search [GitHub Issues](https://github.com/suryasai87/voyce/issues)
3. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Logs
