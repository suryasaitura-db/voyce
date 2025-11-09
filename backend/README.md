# Voice Feedback Platform - Backend API

FastAPI backend for the voice feedback platform with support for PostgreSQL and Databricks backends.

## Features

- **Dual Database Support**: PostgreSQL and Databricks (configurable via environment)
- **JWT Authentication**: Secure authentication with 15-minute access tokens
- **File Upload**: Support for local, S3, and Databricks Volumes storage
- **Async/Await**: Fully async codebase for optimal performance
- **Row-Level Security**: Built-in support for multi-tenant data isolation
- **Monitoring**: Health checks and Prometheus metrics
- **Structured Logging**: JSON logging in production
- **CORS**: Configured for web, mobile, and browser extensions

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Settings and configuration
│   └── database.py       # Database connection and session management
├── models/
│   ├── __init__.py
│   ├── user.py           # User model
│   ├── submission.py     # Voice submission model
│   ├── transcription.py  # Transcription model
│   └── analysis.py       # AI analysis model
├── routers/
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── submissions.py    # Voice submission endpoints
│   └── analytics.py      # Analytics and dashboard endpoints
├── services/
│   ├── __init__.py
│   ├── auth_service.py   # JWT and password handling
│   └── storage_service.py # File storage service
├── utils/
│   ├── __init__.py
│   ├── security.py       # Security utilities
│   └── logger.py         # Logging configuration
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

### Database Backends

#### PostgreSQL (Development)
```env
DB_BACKEND=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=voyce
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

#### Databricks (Production)
```env
DB_BACKEND=databricks
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ACCESS_TOKEN=your_token
DATABRICKS_CATALOG=main
DATABRICKS_SCHEMA=voyce
```

### Storage Backends

#### Local Storage
```env
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads
```

#### AWS S3
```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=voyce-uploads
```

#### Databricks Volumes
```env
STORAGE_BACKEND=databricks_volumes
DATABRICKS_VOLUME_PATH=/Volumes/main/voyce/uploads
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout

### Submissions
- `POST /api/submissions/upload` - Upload voice submission
- `GET /api/submissions/` - List submissions (paginated)
- `GET /api/submissions/{id}` - Get submission details
- `DELETE /api/submissions/{id}` - Delete submission

### Analytics
- `GET /api/analytics/dashboard` - Get dashboard statistics
- `GET /api/analytics/trends` - Get trend analysis
- `GET /api/analytics/sentiment-over-time` - Get sentiment trends

### System
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /api/docs` - API documentation (Swagger UI)
- `GET /api/redoc` - API documentation (ReDoc)

## Security Features

- **TLS 1.2+**: Minimum TLS version enforcement
- **JWT Tokens**: 15-minute access tokens, 7-day refresh tokens
- **Password Requirements**: Configurable strength requirements
- **CORS**: Restricted origins
- **Row-Level Security**: User data isolation
- **Request Validation**: Pydantic models
- **Rate Limiting**: Built-in support (TODO: implement)

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Formatting
```bash
black .
isort .
```

### Linting
```bash
flake8 .
mypy .
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Databricks
Upload to Databricks workspace and run as a Databricks App:
```bash
databricks apps create voyce-backend
```

## Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: JSON structured logs to stdout

## License

MIT
