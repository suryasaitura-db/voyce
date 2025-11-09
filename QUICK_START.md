# Quick Start Guide

Get up and running with Voyce in minutes!

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Git

## 5-Minute Setup

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/suryasai87/voyce.git
cd voyce

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (or use defaults for development)
# Minimum required: DB credentials and secret keys
```

**Quick .env setup for local development:**
```bash
HOST=localhost
PORT=8000
DEBUG=True
ENVIRONMENT=development

DB_HOST=localhost
DB_PORT=5432
DB_NAME=voyce_db
DB_USER=voyce_user
DB_PASSWORD=voyce_password

# Generate secure keys
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 3. Setup Database

```bash
# Start PostgreSQL (if not running)
# macOS: brew services start postgresql@15
# Linux: sudo systemctl start postgresql

# Create database and user
psql postgres <<EOF
CREATE USER voyce_user WITH PASSWORD 'voyce_password';
CREATE DATABASE voyce_db OWNER voyce_user;
GRANT ALL PRIVILEGES ON DATABASE voyce_db TO voyce_user;
EOF

# Initialize database schema
python -c "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. Run Application

```bash
# Start the backend
python main.py
```

The API will be available at `http://localhost:8000`

### 5. Verify Installation

Open your browser and visit:

- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

You should see the interactive Swagger UI documentation.

## First Steps

### Create a User Account

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'
```

### Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!"
  }'
```

Save the `access_token` from the response.

### Upload Your First Voice Submission

```bash
# Create a test audio file (or use your own)
# Then upload:

curl -X POST http://localhost:8000/api/submissions/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@test_recording.wav" \
  -F "title=Test Feedback" \
  -F "category=feedback"
```

## Optional: Databricks Setup

For ML features (transcription, sentiment analysis):

### 1. Configure Databricks

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure credentials
databricks configure --token

# Enter your workspace URL and token when prompted
```

### 2. Deploy to Databricks

```bash
# Validate bundle
databricks bundle validate -t dev

# Deploy
databricks bundle deploy -t dev

# Upload notebooks
databricks workspace import-dir \
  ./databricks-notebooks \
  /Workspace/voyce
```

### 3. Run Unity Catalog Setup

In Databricks workspace, run the notebook:
`/Workspace/voyce/00_unity_catalog_setup`

## Common Issues

### Port 8000 Already in Use

```bash
# Use a different port
PORT=8001 python main.py

# Or kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
pg_isready

# Verify credentials
psql -h localhost -U voyce_user -d voyce_db -c "SELECT 1"
```

### Module Not Found

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

Now that you have Voyce running:

1. **Explore the API**: Visit http://localhost:8000/api/docs
2. **Read the Docs**: Check out [docs/](./docs/) for detailed guides
3. **Configure Storage**: Set up S3/Azure/GCS for file uploads
4. **Enable ML Features**: Configure Whisper for transcription
5. **Deploy to Production**: See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

## Development Workflow

```bash
# Make changes to code
# Backend auto-reloads with uvicorn --reload

# Run tests
pytest

# Format code
black .

# Check linting
flake8 backend/
```

## Getting Help

- **Documentation**: [docs/](./docs/)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)
- **Issues**: [GitHub Issues](https://github.com/suryasai87/voyce/issues)
- **Email**: support@voyce.ai

## Shortcuts

**Reset everything:**
```bash
# Drop and recreate database
dropdb voyce_db
createdb voyce_db
python -c "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())"
```

**Quick test:**
```bash
# Run all tests
pytest -v

# Run specific test
pytest tests/unit/test_auth.py -v
```

**Check logs:**
```bash
# Application logs
tail -f logs/app.log

# Or run with verbose output
LOG_LEVEL=DEBUG python main.py
```

---

You're all set! Start building with Voyce.
