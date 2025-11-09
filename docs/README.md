# Voyce Documentation

Welcome to the Voyce Voice Feedback Platform documentation. This comprehensive guide will help you understand, deploy, and maintain the platform.

## Table of Contents

1. [Architecture](./ARCHITECTURE.md) - System architecture and design
2. [API Documentation](./API.md) - Complete API reference
3. [Setup Guide](./SETUP.md) - Environment setup instructions
4. [Deployment](./DEPLOYMENT.md) - Deployment procedures
5. [Security](./SECURITY.md) - Security measures and best practices
6. [Testing](./TESTING.md) - Test execution and coverage
7. [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions
8. [Cost Optimization](./COST_OPTIMIZATION.md) - Cost-saving strategies
9. [Database Schema](./DATABASE_SCHEMA.md) - Database design
10. [ML Pipeline](./ML_PIPELINE.md) - Machine learning workflows
11. [Contributing](./CONTRIBUTING.md) - Contribution guidelines

## Quick Links

- [Quick Start Guide](../QUICK_START.md)
- [Main README](../README.md)
- [License](../LICENSE)

## What is Voyce?

Voyce is an AI-powered voice feedback platform that enables users to submit voice recordings through multiple channels (web, mobile, Chrome extension), automatically transcribes them using advanced speech-to-text models, and analyzes them for sentiment, intent, and actionable insights.

## Key Features

- **Multi-Channel Collection**: Web interface, mobile apps, and Chrome extension
- **Automatic Transcription**: High-accuracy speech-to-text using Whisper and other models
- **AI-Powered Analysis**: Sentiment analysis, emotion detection, intent classification
- **Real-Time Processing**: FastAPI backend with async processing
- **Databricks Integration**: Scalable data processing and ML workflows
- **Enterprise Security**: OAuth2, JWT, encryption at rest and in transit
- **Analytics Dashboard**: Real-time insights and trends

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: OAuth2 + JWT
- **Storage**: Cloud storage (S3/Azure Blob/GCS)
- **API Documentation**: OpenAPI/Swagger

### Data Platform
- **Processing**: Databricks (Serverless compute)
- **Analytics**: SQL Serverless
- **ML Models**: Whisper (transcription), Transformers (sentiment)
- **Storage**: Unity Catalog

### Frontend
- **Web**: React/Next.js
- **Mobile**: React Native
- **Extension**: Chrome Extension API

### Infrastructure
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with Python JSON Logger
- **Deployment**: Docker, Kubernetes, Databricks

## Getting Started

For a quick start, see the [Quick Start Guide](../QUICK_START.md).

For detailed setup instructions, see the [Setup Guide](./SETUP.md).

## Support and Community

- **Issues**: [GitHub Issues](https://github.com/suryasai87/voyce/issues)
- **Discussions**: [GitHub Discussions](https://github.com/suryasai87/voyce/discussions)
- **Email**: support@voyce.ai

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Documentation Version

- **Version**: 1.0.0
- **Last Updated**: 2025-01-08
- **Platform Version**: 1.0.0
