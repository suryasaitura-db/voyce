# Deployment Guide

Step-by-step deployment instructions for all components of the Voyce Voice Feedback Platform.

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Pre-deployment Checklist](#pre-deployment-checklist)
- [Environment Configuration](#environment-configuration)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Databricks Deployment](#databricks-deployment)
- [Database Migration](#database-migration)
- [Chrome Extension Deployment](#chrome-extension-deployment)
- [Post-deployment Tasks](#post-deployment-tasks)
- [Monitoring Setup](#monitoring-setup)
- [Rollback Procedures](#rollback-procedures)

## Deployment Overview

### Deployment Environments

1. **Development**: Local development and testing
2. **Staging**: Pre-production testing environment
3. **Production**: Live production environment

### Infrastructure Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION SETUP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Cloud Provider (AWS/Azure/GCP)                                │
│  ├── Load Balancer (ALB/Azure LB/GCP LB)                       │
│  ├── Container Service (ECS/AKS/GKE)                           │
│  │   ├── Backend API (FastAPI)                                 │
│  │   └── Auto-scaling: 2-10 instances                          │
│  ├── Managed Database (RDS/Azure DB/Cloud SQL)                 │
│  ├── Object Storage (S3/Blob/GCS)                              │
│  ├── CDN (CloudFront/Azure CDN/Cloud CDN)                      │
│  └── Monitoring (CloudWatch/Azure Monitor/Stackdriver)         │
│                                                                 │
│  Databricks                                                     │
│  ├── Unity Catalog                                             │
│  ├── Serverless Compute                                        │
│  ├── SQL Warehouses                                            │
│  └── Jobs & Workflows                                          │
│                                                                 │
│  Frontend Hosting                                               │
│  ├── Static Site (Vercel/Netlify/S3+CloudFront)               │
│  └── Mobile Apps (App Store/Play Store)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Pre-deployment Checklist

### Code Quality

- [ ] All tests passing (`pytest`)
- [ ] Code linting passes (`flake8`, `black`)
- [ ] Type checking passes (`mypy`)
- [ ] Security scan completed
- [ ] Code review approved
- [ ] Documentation updated

### Configuration

- [ ] Environment variables configured
- [ ] Secrets stored securely (AWS Secrets Manager, Azure Key Vault)
- [ ] Database connection strings updated
- [ ] API keys rotated
- [ ] CORS settings configured
- [ ] Domain names configured

### Infrastructure

- [ ] Cloud resources provisioned
- [ ] Database backups enabled
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] SSL certificates installed
- [ ] DNS records configured

### Security

- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Input validation implemented
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] CSRF protection enabled

## Environment Configuration

### Production Environment Variables

Create `.env.production`:

```bash
# Application
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000
APP_NAME=voyce

# Database (use managed service)
DB_BACKEND=postgresql
DB_HOST=prod-db.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=voyce_prod
DB_USER=voyce_prod_user
DB_PASSWORD=${DB_PASSWORD}  # From secrets manager
DB_SSL_MODE=require

# Databricks
DATABRICKS_PROFILE=PRODUCTION
DATABRICKS_HOST=${DATABRICKS_HOST}
DATABRICKS_TOKEN=${DATABRICKS_TOKEN}  # From secrets manager

# Cloud Storage
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_REGION=us-east-1
S3_BUCKET=voyce-production-audio

# Security
SECRET_KEY=${SECRET_KEY}  # From secrets manager
JWT_SECRET_KEY=${JWT_SECRET_KEY}  # From secrets manager
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# API
API_VERSION=v1
API_PREFIX=/api
ALLOWED_ORIGINS=https://app.voyce.ai,https://www.voyce.ai

# CORS
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_ALLOW_HEADERS=*

# Redis
REDIS_HOST=prod-redis.cache.amazonaws.com
REDIS_PORT=6379
REDIS_SSL=True
REDIS_PASSWORD=${REDIS_PASSWORD}

# Monitoring
PROMETHEUS_ENABLED=True
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=${SENTRY_DSN}

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=${SENDGRID_API_KEY}
```

## Backend Deployment

### Option 1: Docker Deployment

#### 1. Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 voyce && chown -R voyce:voyce /app
USER voyce

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=voyce_prod
      - POSTGRES_USER=voyce_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 3. Build and Deploy

```bash
# Build image
docker build -t voyce-api:latest .

# Tag for registry
docker tag voyce-api:latest your-registry/voyce-api:1.0.0

# Push to registry
docker push your-registry/voyce-api:1.0.0

# Deploy with docker-compose
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose ps
docker-compose logs -f api
```

### Option 2: Kubernetes Deployment

#### 1. Create Kubernetes Manifests

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voyce-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voyce-api
  template:
    metadata:
      labels:
        app: voyce-api
    spec:
      containers:
      - name: api
        image: your-registry/voyce-api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: voyce-secrets
              key: db-password
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: voyce-api
  namespace: production
spec:
  selector:
    app: voyce-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: voyce-api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: voyce-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace production

# Create secrets
kubectl create secret generic voyce-secrets \
  --from-literal=db-password=$DB_PASSWORD \
  --from-literal=jwt-secret=$JWT_SECRET_KEY \
  --namespace=production

# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods -n production
kubectl get svc -n production
kubectl logs -f deployment/voyce-api -n production
```

### Option 3: Serverless Deployment (AWS Lambda)

#### 1. Install Mangum

```bash
pip install mangum
```

#### 2. Create Lambda Handler

Create `lambda_handler.py`:

```python
from mangum import Mangum
from backend.app.main import app

handler = Mangum(app)
```

#### 3. Deploy with AWS SAM

Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  VoyceAPI:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: voyce-api
      Runtime: python3.9
      Handler: lambda_handler.handler
      CodeUri: .
      MemorySize: 1024
      Timeout: 30
      Environment:
        Variables:
          ENVIRONMENT: production
      Events:
        Api:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

Deploy:

```bash
sam build
sam deploy --guided
```

## Frontend Deployment

### Option 1: Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend
cd frontend

# Deploy
vercel --prod

# Configure environment variables in Vercel dashboard
```

### Option 2: Netlify Deployment

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Build frontend
npm run build

# Deploy
netlify deploy --prod --dir=build
```

### Option 3: S3 + CloudFront

```bash
# Build frontend
npm run build

# Sync to S3
aws s3 sync build/ s3://voyce-frontend-prod/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

## Databricks Deployment

### 1. Validate Bundle

```bash
databricks bundle validate -t prod
```

### 2. Deploy Bundle

```bash
databricks bundle deploy -t prod
```

### 3. Configure Jobs

Create `databricks.yml` for production:

```yaml
bundle:
  name: voyce

targets:
  prod:
    mode: production
    workspace:
      profile: PRODUCTION
      host: ${var.databricks_host}

resources:
  jobs:
    voice_processing:
      name: "Voyce - Voice Processing"
      job_clusters:
        - job_cluster_key: main
          new_cluster:
            spark_version: 15.4.x-scala2.12
            node_type_id: i3.xlarge
            num_workers: 4
            autoscale:
              min_workers: 2
              max_workers: 8
      tasks:
        - task_key: data_ingestion
          notebook_task:
            notebook_path: /Workspace/voyce/01_data_ingestion
          job_cluster_key: main
        - task_key: voice_processing
          depends_on:
            - task_key: data_ingestion
          notebook_task:
            notebook_path: /Workspace/voyce/02_voice_processing
          job_cluster_key: main
        - task_key: sentiment_analysis
          depends_on:
            - task_key: voice_processing
          notebook_task:
            notebook_path: /Workspace/voyce/03_sentiment_analysis
          job_cluster_key: main
      schedule:
        quartz_cron_expression: "0 0 * * * ?"
        timezone_id: "UTC"
```

### 4. Run Job

```bash
databricks bundle run voice_processing -t prod
```

## Database Migration

### Pre-migration

```bash
# Backup database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Upload to S3
aws s3 cp backup_*.sql s3://voyce-backups/
```

### Migration

```bash
# Run migrations
alembic upgrade head

# Or using custom script
python scripts/migrate.py --env production
```

### Verification

```bash
# Verify tables
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt"

# Check data integrity
python scripts/verify_migration.py
```

## Chrome Extension Deployment

### 1. Build Extension

```bash
cd chrome-extension
npm run build
```

### 2. Create ZIP

```bash
zip -r voyce-extension-v1.0.0.zip \
  manifest.json \
  background/ \
  popup/ \
  icons/ \
  -x "*.DS_Store"
```

### 3. Upload to Chrome Web Store

1. Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
2. Click "New Item"
3. Upload ZIP file
4. Fill in store listing details
5. Submit for review

## Post-deployment Tasks

### 1. Health Checks

```bash
# Check API health
curl https://api.voyce.ai/health

# Check database connectivity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"

# Check Databricks
databricks workspace ls /Workspace/voyce
```

### 2. Smoke Tests

```bash
# Run smoke tests
pytest tests/smoke/

# Test critical flows
python scripts/smoke_test.py --env production
```

### 3. Monitoring Setup

```bash
# Configure alerts
python scripts/setup_alerts.py --env production

# Verify metrics
curl https://api.voyce.ai/metrics
```

### 4. DNS Configuration

```bash
# Update DNS records
# A record: api.voyce.ai -> Load Balancer IP
# CNAME: www.voyce.ai -> CloudFront distribution
```

### 5. SSL Certificate

```bash
# Using certbot
sudo certbot --nginx -d api.voyce.ai

# Or use AWS ACM, Azure Key Vault, etc.
```

## Monitoring Setup

### Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'voyce-api'
    static_configs:
      - targets: ['api.voyce.ai:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import dashboard JSON from `monitoring/grafana-dashboard.json`

### Alerts

Create `alerts.yml`:

```yaml
groups:
  - name: voyce_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: http_request_duration_seconds{quantile="0.99"} > 1
        for: 5m
        annotations:
          summary: "High latency detected"
```

## Rollback Procedures

### Backend Rollback

**Docker:**
```bash
# Rollback to previous version
docker-compose pull your-registry/voyce-api:1.0.0
docker-compose up -d
```

**Kubernetes:**
```bash
# Rollback deployment
kubectl rollout undo deployment/voyce-api -n production

# Or rollback to specific revision
kubectl rollout undo deployment/voyce-api --to-revision=2 -n production
```

### Database Rollback

```bash
# Restore from backup
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_20250108_100000.sql

# Or use point-in-time recovery (if supported)
```

### Databricks Rollback

```bash
# Deploy previous version
git checkout v1.0.0
databricks bundle deploy -t prod
```

## Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Environment variables configured
- [ ] Secrets rotated and stored securely
- [ ] Database backed up
- [ ] Migration scripts tested
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] SSL certificates valid
- [ ] DNS configured
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Rollback plan prepared
- [ ] Stakeholders notified
- [ ] Deployment window scheduled

## Maintenance

### Regular Tasks

**Daily:**
- Review logs for errors
- Check system metrics
- Monitor costs

**Weekly:**
- Review security alerts
- Update dependencies
- Check backup integrity

**Monthly:**
- Rotate API keys
- Review access logs
- Update SSL certificates
- Performance optimization

## Support

For deployment issues:

1. Check [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review deployment logs
3. Contact DevOps team
4. Create incident ticket
