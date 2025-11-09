# 👥 Voyce Collaborator Onboarding Guide

Welcome to the **Voyce Voice Feedback Platform** team! This guide will help you get the project running locally and understand the codebase.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Detailed Setup](#detailed-setup)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Contributing](#contributing)

---

## Prerequisites

### Required Software

```bash
# 1. Check Python version (3.9+ required)
python3 --version

# 2. Check PostgreSQL (13+ required)
psql --version

# 3. Check Node.js (16+ required)
node --version

# 4. Check Redis (7+ required)
redis-server --version

# 5. Check Docker (optional but recommended)
docker --version
docker-compose --version
```

### Install Missing Dependencies

**macOS**:
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 postgresql@15 redis node@18
brew install --cask docker  # Optional
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.11 postgresql redis-server nodejs npm
```

**Windows**:
- Install Python from python.org
- Install PostgreSQL from postgresql.org
- Install Redis from redis.io/download
- Install Node.js from nodejs.org
- Install Docker Desktop

---

## Quick Start (5 Minutes)

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/suryasai87/voyce.git
cd voyce

# 2. Start all services
docker-compose up -d

# 3. Initialize database
docker-compose exec backend python scripts/init_db.py

# 4. Access services
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
# - Frontend: http://localhost:3000
# - Celery Flower: http://localhost:5555
# - Grafana: http://localhost:3001 (admin/admin)
# - Prometheus: http://localhost:9090

# 5. View logs
docker-compose logs -f backend
```

### Option 2: Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/suryasai87/voyce.git
cd voyce

# 2. Setup backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. Start PostgreSQL and Redis
brew services start postgresql  # macOS
brew services start redis
# OR
sudo systemctl start postgresql  # Linux
sudo systemctl start redis

# 4. Create database
createdb voyce_db

# 5. Initialize schema
python scripts/init_db.py

# 6. Start backend
python main.py
# → Backend running at http://localhost:8000

# 7. Setup frontend (new terminal)
cd frontend
npm install
npm run dev
# → Frontend running at http://localhost:3000
```

---

## Detailed Setup

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your favorite editor
```

**Required Environment Variables**:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=voyce_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here  # Change this!

# Application
HOST=localhost
PORT=8000
DEBUG=True
SECRET_KEY=your-secret-key-change-this  # Generate with: openssl rand -hex 32
JWT_SECRET=your-jwt-secret-change-this  # Generate with: openssl rand -hex 32
```

**Optional API Keys** (for full functionality):

```bash
# OpenAI Whisper (for speech-to-text)
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com/api-keys

# Anthropic Claude (for sentiment analysis)
ANTHROPIC_API_KEY=sk-ant-...  # Get from https://console.anthropic.com/

# Google Cloud (optional alternative STT)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id

# AWS (optional alternative STT)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# Databricks (for ML/Analytics)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
```

**Generate Secrets**:
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET
openssl rand -hex 32
```

### 2. Database Setup

```bash
# Create database
createdb voyce_db

# Run migrations
python scripts/init_db.py

# Verify tables
psql voyce_db -c "\dt"
```

**Expected Output**:
```
                List of relations
 Schema |       Name        | Type  |  Owner
--------+-------------------+-------+----------
 public | ai_analysis       | table | postgres
 public | audit_log         | table | postgres
 public | processing_costs  | table | postgres
 public | sync_metadata     | table | postgres
 public | transcriptions    | table | postgres
 public | users             | table | postgres
 public | voice_submissions | table | postgres
```

### 3. Chrome Extension Setup

```bash
cd chrome-extension

# Create icons (choose one method)
# Method 1: Download from Icons8
# Visit: https://icons8.com/icons/set/microphone
# Download 16px, 48px, 128px icons

# Method 2: Generate with Python
python3 icons/generate_icons.py

# Method 3: Generate with Node.js
npm install canvas
node icons/generate_icons.js

# Load in Chrome
# 1. Open Chrome → chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select chrome-extension/ folder
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### 5. Databricks Setup (Optional)

```bash
# Configure Databricks CLI
databricks configure --token --profile DEFAULT

# Enter your credentials:
# - Host: https://your-workspace.cloud.databricks.com
# - Token: dapi...

# Verify connection
databricks workspace ls /

# Deploy notebooks
databricks workspace import_dir \
  databricks-notebooks/ \
  /Workspace/voyce-notebooks \
  --overwrite

# Create Unity Catalog
# Run notebook: 00_unity_catalog_setup.py in Databricks UI
```

---

## Project Structure

```
voyce/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Configuration
│   │   └── database.py        # Database connection
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── submission.py
│   │   ├── transcription.py
│   │   └── analysis.py
│   ├── routers/               # API endpoints
│   │   ├── auth.py            # POST /api/auth/login, /register
│   │   ├── submissions.py     # POST /api/submissions/upload
│   │   └── analytics.py       # GET /api/analytics/overview
│   ├── services/              # Business logic
│   │   ├── voice_processor.py      # STT engines
│   │   ├── sentiment_analyzer.py   # Sentiment analysis
│   │   ├── storage_service.py      # File storage
│   │   └── sync_service.py         # DB sync
│   └── utils/                 # Utilities
│       ├── logger.py
│       └── security.py
│
├── frontend/                   # React Web App
│   ├── src/
│   │   ├── pages/             # 6 pages
│   │   ├── components/        # 7 components
│   │   ├── hooks/             # 3 custom hooks
│   │   └── services/          # API client
│   └── package.json
│
├── chrome-extension/           # Chrome Extension
│   ├── manifest.json
│   ├── popup/                 # UI
│   └── background/            # Service worker
│
├── databricks-notebooks/       # Databricks ML
│   ├── 00_unity_catalog_setup.py
│   ├── 02_voice_processing.py
│   └── 03_sentiment_analysis.py
│
├── database/
│   └── 001_initial_schema.sql # PostgreSQL schema
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── ... (15 guides)
│
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker-compose.yml          # Docker setup
├── .env                        # Environment variables
└── main.py                     # Local dev entry point
```

---

## Development Workflow

### Starting Development

```bash
# 1. Pull latest code
git pull origin main

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install/update dependencies
pip install -r backend/requirements.txt
cd frontend && npm install

# 4. Start services
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Celery (if needed)
celery -A backend.services.celery_app:celery_app worker --loglevel=info
```

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes
# ... edit code ...

# 3. Run tests
pytest
cd frontend && npm test

# 4. Format code
black backend/
cd frontend && npm run lint

# 5. Commit changes
git add .
git commit -m "feat: your feature description"

# 6. Push to GitHub
git push origin feature/your-feature-name

# 7. Create Pull Request
# Go to GitHub and create PR
```

### Code Style

**Python (Backend)**:
```bash
# Format with Black
black backend/

# Lint with Flake8
flake8 backend/

# Type check with mypy
mypy backend/
```

**TypeScript (Frontend)**:
```bash
# Lint and format
cd frontend
npm run lint
npm run format
```

---

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test
pytest tests/unit/test_auth.py::TestAuthService::test_hash_password

# View coverage report
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

### Manual Testing

**Test Voice Upload**:

```bash
# 1. Start backend
python main.py

# 2. Open API docs
open http://localhost:8000/api/docs

# 3. Register user
# POST /api/auth/register
# Body: {"email": "test@example.com", "username": "test", "password": "Password123!"}

# 4. Login
# POST /api/auth/login
# Get access_token from response

# 5. Upload voice file
# POST /api/submissions/upload
# Headers: Authorization: Bearer {token}
# File: test.wav
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Check PostgreSQL status
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# Check port
lsof -i :5432
```

#### 2. Redis Connection Error

**Error**: `Error 61 connecting to localhost:6379. Connection refused.`

**Solution**:
```bash
# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# Check Redis
redis-cli ping
# Should return: PONG
```

#### 3. Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
PORT=8001 python main.py
```

#### 4. Frontend Build Error

**Error**: `Module not found` or dependency errors

**Solution**:
```bash
cd frontend

# Clean install
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force
npm install
```

#### 5. Python Package Errors

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# If specific package fails
pip install <package-name> --upgrade
```

### Getting Help

1. **Check Documentation**: `/docs/TROUBLESHOOTING.md`
2. **Search Issues**: https://github.com/suryasai87/voyce/issues
3. **Ask Team**: Create new GitHub issue
4. **Slack Channel**: #voyce-dev (if available)

---

## Contributing

### Before You Start

1. Read `docs/CONTRIBUTING.md`
2. Check existing issues/PRs
3. Discuss major changes in issues first

### Pull Request Process

1. **Update from main**:
   ```bash
   git checkout main
   git pull origin main
   git checkout your-branch
   git rebase main
   ```

2. **Run tests**:
   ```bash
   pytest
   cd frontend && npm test
   ```

3. **Format code**:
   ```bash
   black backend/
   cd frontend && npm run lint
   ```

4. **Create PR**:
   - Clear title: `feat: add voice recording feature`
   - Description with context
   - Link related issues
   - Add screenshots if UI changes

5. **Code Review**:
   - Address review comments
   - Keep PR focused and small
   - Update documentation

### Commit Message Convention

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting, missing semicolons, etc
refactor: code restructuring
test: adding tests
chore: maintenance tasks
```

---

## Quick Reference

### Useful Commands

```bash
# Backend
python main.py                    # Start backend
pytest                           # Run tests
black backend/                   # Format code
python scripts/init_db.py        # Reset database

# Frontend
npm run dev                      # Start dev server
npm run build                    # Build for production
npm test                         # Run tests
npm run lint                     # Lint code

# Docker
docker-compose up -d             # Start all services
docker-compose down              # Stop all services
docker-compose logs -f backend   # View logs
docker-compose exec backend bash # Shell into container

# Database
psql voyce_db                    # Connect to database
python scripts/init_db.py        # Initialize schema
pg_dump voyce_db > backup.sql    # Backup database

# Git
git status                       # Check status
git log --oneline -10            # Recent commits
git branch                       # List branches
git checkout -b feature/name     # Create branch
```

### Important URLs

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Frontend**: http://localhost:3000
- **Flower (Celery)**: http://localhost:5555
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **GitHub**: https://github.com/suryasai87/voyce

### Key Files

- `.env` - Environment configuration
- `backend/app/main.py` - FastAPI app
- `frontend/src/App.tsx` - React app
- `docker-compose.yml` - Docker setup
- `database/001_initial_schema.sql` - DB schema

---

## Next Steps

1. ✅ Complete this onboarding guide
2. ✅ Get local development running
3. ✅ Make a small test change
4. ✅ Run tests successfully
5. ✅ Create your first PR
6. Read architecture docs (`docs/ARCHITECTURE.md`)
7. Review API documentation (`docs/API.md`)
8. Join team meetings
9. Pick up your first issue

---

## Welcome to the Team! 🎉

You're now ready to contribute to Voyce! If you have any questions, don't hesitate to ask in GitHub issues or reach out to the team.

**Happy coding!** 🚀
