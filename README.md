# Voyce - Voice Feedback Platform

An AI-powered voice feedback platform that enables users to submit voice recordings, automatically transcribes them using advanced speech-to-text models, and analyzes them for sentiment, intent, and actionable insights.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Databricks](https://img.shields.io/badge/Databricks-Powered-red.svg)](https://databricks.com/)

## Overview

Voyce is a comprehensive voice feedback platform that combines:

- **Multi-Channel Collection**: Web, mobile, and Chrome extension interfaces
- **AI Transcription**: High-accuracy speech-to-text using Whisper
- **Sentiment Analysis**: Advanced NLP for emotion and intent detection
- **Databricks Integration**: Scalable data processing and ML workflows
- **Real-Time Analytics**: Insights dashboard with sentiment trends

## Quick Start

```bash
# Clone repository
git clone https://github.com/suryasai87/voyce.git
cd voyce

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Initialize database
createdb voyce_db
python scripts/init_db.py

# Run locally
python main.py
```

Visit `http://localhost:8000/api/docs` for API documentation.

For detailed setup instructions, see [QUICK_START.md](./QUICK_START.md).

## Features

### Core Capabilities

- **Voice Recording**: Record and upload audio feedback
- **Automatic Transcription**: Whisper-powered speech-to-text
- **Sentiment Analysis**: Detect emotions and sentiment
- **Intent Classification**: Identify user intent (feedback, complaint, suggestion)
- **Entity Extraction**: Extract key topics and entities
- **Analytics Dashboard**: Visualize feedback trends and insights
- **Multi-Platform**: Web, mobile, and browser extension support

### Technical Features

- **FastAPI Backend**: High-performance async API
- **PostgreSQL Database**: Reliable data storage with SQLAlchemy ORM
- **Databricks Integration**: Scalable ML workflows and analytics
- **Cloud Storage**: S3/Azure/GCS support for audio files
- **JWT Authentication**: Secure OAuth2 authentication
- **Prometheus Metrics**: Built-in monitoring and observability
- **OpenAPI Documentation**: Interactive API documentation

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web App   │     │  Mobile App │     │  Extension  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  FastAPI    │
                    │  Backend    │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌─────▼─────┐    ┌─────▼─────┐
    │PostgreSQL│      │Cloud      │    │Databricks │
    │ Database │      │Storage    │    │ML Pipeline│
    └──────────┘      └───────────┘    └───────────┘
```

For detailed architecture, see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Technology Stack

### Backend
- **Python 3.9+** - Core language
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Redis** - Caching (optional)

### ML/AI
- **OpenAI Whisper** - Speech-to-text
- **HuggingFace Transformers** - NLP models
- **Databricks** - ML workflows
- **MLflow** - Model tracking

### Frontend
- **React** - Web application
- **React Native** - Mobile apps
- **JavaScript** - Chrome extension

### Infrastructure
- **Docker** - Containerization
- **Kubernetes** - Orchestration
- **AWS/Azure/GCP** - Cloud hosting
- **Prometheus/Grafana** - Monitoring

## Documentation

Comprehensive documentation is available in the [docs/](./docs/) directory:

- [Quick Start Guide](./QUICK_START.md) - Get started quickly
- [Setup Guide](./docs/SETUP.md) - Detailed environment setup
- [Architecture](./docs/ARCHITECTURE.md) - System architecture and design
- [API Documentation](./docs/API.md) - Complete API reference
- [Deployment](./docs/DEPLOYMENT.md) - Deployment procedures
- [Security](./docs/SECURITY.md) - Security best practices
- [Testing](./docs/TESTING.md) - Testing guide
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Cost Optimization](./docs/COST_OPTIMIZATION.md) - Cost-saving strategies
- [Database Schema](./docs/DATABASE_SCHEMA.md) - Database design
- [ML Pipeline](./docs/ML_PIPELINE.md) - Machine learning workflows
- [Contributing](./docs/CONTRIBUTING.md) - Contribution guidelines

## Project Structure

```
voyce/
├── backend/                    # Backend API
│   ├── app/                   # FastAPI application
│   │   ├── main.py           # Application entry point
│   │   ├── config.py         # Configuration
│   │   └── database.py       # Database setup
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py
│   │   ├── submission.py
│   │   ├── transcription.py
│   │   └── analysis.py
│   ├── routers/              # API routes
│   │   ├── auth.py
│   │   ├── submissions.py
│   │   └── analytics.py
│   ├── services/             # Business logic
│   │   ├── auth_service.py
│   │   ├── voice_processor.py
│   │   ├── storage_service.py
│   │   └── sentiment_analyzer.py
│   └── utils/                # Utilities
│       ├── logger.py
│       └── security.py
├── databricks-notebooks/      # Databricks notebooks
│   ├── 00_unity_catalog_setup.py
│   ├── 01_data_ingestion.py
│   ├── 02_voice_processing.py
│   ├── 03_sentiment_analysis.py
│   ├── 05_model_training.py
│   └── 06_batch_inference.py
├── chrome-extension/          # Chrome extension
│   ├── manifest.json
│   ├── background/
│   └── popup/
├── frontend/                  # React web app
├── mobile/                    # React Native app
├── tests/                     # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── databricks.yml            # Databricks config
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── main.py                   # Local development entry
```

## Prerequisites

- **Python**: 3.9 or higher
- **PostgreSQL**: 13 or higher
- **Node.js**: 16.x or higher (for frontend)
- **Databricks**: Workspace access
- **Cloud Storage**: AWS S3, Azure Blob, or Google Cloud Storage account

## Installation

See [QUICK_START.md](./QUICK_START.md) for quick setup or [docs/SETUP.md](./docs/SETUP.md) for detailed instructions.

## Configuration

Key environment variables:

```bash
# Application
HOST=localhost
PORT=8000
DEBUG=True

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voyce_db
DB_USER=voyce_user
DB_PASSWORD=your_password

# Databricks
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_token

# Storage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=voyce-audio-files

# Security
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
```

## Development

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server with auto-reload
python main.py

# Or use uvicorn directly
uvicorn backend.app.main:app --reload --host localhost --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 backend/

# Type checking
mypy backend/
```

## Deployment

### Docker

```bash
# Build image
docker build -t voyce-api:latest .

# Run container
docker-compose up -d
```

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n production
```

### Databricks

```bash
# Deploy Databricks bundle
databricks bundle deploy -t prod

# Run job
databricks bundle run voice_processing -t prod
```

For detailed deployment instructions, see [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md).

## API Usage

### Authentication

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "password"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### Upload Voice Submission

```bash
curl -X POST http://localhost:8000/api/submissions/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@recording.wav" \
  -F "title=Product Feedback" \
  -F "category=feature_request"
```

For complete API documentation, visit `/api/docs` or see [docs/API.md](./docs/API.md).

## Contributing

We welcome contributions! Please see [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Security

For security concerns, please email security@voyce.ai. See [docs/SECURITY.md](./docs/SECURITY.md) for security best practices.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/suryasai87/voyce/issues)
- **Discussions**: [GitHub Discussions](https://github.com/suryasai87/voyce/discussions)
- **Email**: support@voyce.ai

## Acknowledgments

- OpenAI Whisper for speech-to-text
- HuggingFace for NLP models
- Databricks for data platform
- FastAPI for the web framework
- All our contributors

## Roadmap

- [ ] Real-time transcription via WebSockets
- [ ] Multi-language support
- [ ] Custom model training per organization
- [ ] Advanced analytics dashboard
- [ ] Integration with popular tools (Slack, Teams, etc.)
- [ ] Mobile app release
- [ ] Voice-to-action automation

## Status

- **Version**: 1.0.0
- **Status**: Active Development
- **Last Updated**: January 2025

---

Made with passion by the Voyce team.
