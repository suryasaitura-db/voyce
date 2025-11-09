# Security Documentation

Comprehensive security measures and best practices for the Voyce Voice Feedback Platform.

## Table of Contents

- [Security Overview](#security-overview)
- [Authentication & Authorization](#authentication--authorization)
- [Data Security](#data-security)
- [Network Security](#network-security)
- [API Security](#api-security)
- [Infrastructure Security](#infrastructure-security)
- [Secure Development Practices](#secure-development-practices)
- [Compliance](#compliance)
- [Incident Response](#incident-response)
- [Security Checklist](#security-checklist)

## Security Overview

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimum necessary access rights
3. **Zero Trust**: Never trust, always verify
4. **Security by Design**: Security built into architecture
5. **Continuous Monitoring**: Real-time threat detection

### Threat Model

**Potential Threats:**
- Unauthorized access to user data
- Data breaches and exfiltration
- DDoS attacks
- SQL injection
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)
- Man-in-the-middle attacks
- Malicious file uploads
- API abuse

## Authentication & Authorization

### OAuth2 + JWT Implementation

**Authentication Flow:**

```
┌──────────┐                ┌─────────┐                ┌──────────┐
│  Client  │                │   API   │                │ Database │
└────┬─────┘                └────┬────┘                └────┬─────┘
     │                           │                          │
     │  POST /auth/login         │                          │
     │ (username, password)      │                          │
     ├──────────────────────────>│                          │
     │                           │                          │
     │                           │  Verify credentials      │
     │                           ├─────────────────────────>│
     │                           │                          │
     │                           │  User data               │
     │                           │<─────────────────────────┤
     │                           │                          │
     │                           │  Generate JWT            │
     │                           │  (with expiry)           │
     │                           │                          │
     │  Access + Refresh tokens  │                          │
     │<──────────────────────────┤                          │
     │                           │                          │
     │  API Request with token   │                          │
     │  Authorization: Bearer    │                          │
     ├──────────────────────────>│                          │
     │                           │                          │
     │                           │  Validate JWT            │
     │                           │  Check expiry            │
     │                           │  Verify signature        │
     │                           │                          │
     │  Response                 │                          │
     │<──────────────────────────┤                          │
```

### Password Security

**Requirements:**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- No common passwords
- Password history (prevent reuse of last 5 passwords)

**Storage:**
```python
# Using bcrypt with salt rounds = 12
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

### JWT Configuration

```python
# JWT Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 256-bit secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60
REFRESH_TOKEN_EXPIRATION_DAYS = 7

# Token payload
{
    "sub": "user_id",
    "email": "user@example.com",
    "role": "user",
    "exp": 1640000000,
    "iat": 1639996400,
    "jti": "unique_token_id"
}
```

**Security Warning:** Never expose JWT secrets in code or version control.

### Role-Based Access Control (RBAC)

```python
class UserRole:
    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"
    READONLY = "readonly"

# Permission decorator
def require_role(role: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = get_current_user()
            if current_user.role != role:
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.get("/admin/users")
@require_role(UserRole.ADMIN)
async def list_users():
    # Only admins can access
    pass
```

## Data Security

### Encryption at Rest

**Database:**
- PostgreSQL: Enable Transparent Data Encryption (TDE)
- Encrypt sensitive columns (PII, financial data)
- Use encrypted storage volumes

```sql
-- Column-level encryption example
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt data
INSERT INTO users (email, encrypted_ssn)
VALUES ('user@example.com', pgp_sym_encrypt('123-45-6789', 'encryption_key'));

-- Decrypt data
SELECT email, pgp_sym_decrypt(encrypted_ssn, 'encryption_key') AS ssn
FROM users;
```

**File Storage:**
- S3: Server-side encryption (SSE-S3 or SSE-KMS)
- Azure: Storage Service Encryption
- Enable versioning for audit trail

```python
# AWS S3 encryption
s3_client.put_object(
    Bucket='voyce-audio',
    Key='file.wav',
    Body=audio_data,
    ServerSideEncryption='AES256'  # or 'aws:kms'
)
```

### Encryption in Transit

**TLS/SSL Configuration:**

```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    server_name api.voyce.ai;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL protocols
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'" always;
}
```

### Data Sanitization

**Input Validation:**

```python
from pydantic import BaseModel, validator, EmailStr
import bleach

class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    full_name: str

    @validator('username')
    def validate_username(cls, v):
        # Sanitize username
        cleaned = bleach.clean(v, strip=True)
        if len(cleaned) < 3 or len(cleaned) > 50:
            raise ValueError('Username must be 3-50 characters')
        if not cleaned.isalnum():
            raise ValueError('Username must be alphanumeric')
        return cleaned

    @validator('full_name')
    def sanitize_name(cls, v):
        # Remove HTML/script tags
        return bleach.clean(v, strip=True)
```

**Output Encoding:**

```python
import html

def safe_render(user_input: str) -> str:
    # Escape HTML to prevent XSS
    return html.escape(user_input)
```

### Sensitive Data Handling

**PII (Personally Identifiable Information):**
- Email addresses
- Phone numbers
- IP addresses
- Voice recordings (biometric data)

**Protection Measures:**
- Encrypt at rest and in transit
- Minimize collection and retention
- Implement data anonymization
- Use pseudonymization where possible
- Regular data purging

```python
# Pseudonymization example
import hashlib

def pseudonymize(email: str, salt: str) -> str:
    return hashlib.sha256(f"{email}{salt}".encode()).hexdigest()
```

## Network Security

### Firewall Rules

```
┌────────────────────────────────────────────────┐
│              INTERNET                          │
└────────────────┬───────────────────────────────┘
                 │
         ┌───────▼───────┐
         │  WAF/DDoS     │
         │  Protection   │
         └───────┬───────┘
                 │
         ┌───────▼───────┐
         │ Load Balancer │
         │ (Public)      │
         │ Port: 443     │
         └───────┬───────┘
                 │
    ┌────────────┼────────────┐
    │                         │
┌───▼───────┐         ┌───────▼───┐
│  API      │         │  API      │
│  Server   │         │  Server   │
│  (Private)│         │  (Private)│
└────┬──────┘         └──────┬────┘
     │                       │
     └───────────┬───────────┘
                 │
     ┌───────────▼───────────┐
     │   Database            │
     │   (Private Subnet)    │
     │   Port: 5432          │
     └───────────────────────┘
```

**Security Groups (AWS Example):**

```yaml
# API Server Security Group
Ingress:
  - Port: 8000
    Source: LoadBalancer SecurityGroup
  - Port: 22
    Source: Bastion SecurityGroup

Egress:
  - Port: 5432
    Destination: Database SecurityGroup
  - Port: 443
    Destination: 0.0.0.0/0  # For external APIs
```

### VPC Configuration

```
VPC: 10.0.0.0/16
├── Public Subnet (10.0.1.0/24)
│   ├── Load Balancer
│   └── NAT Gateway
├── Private Subnet (10.0.2.0/24)
│   ├── API Servers
│   └── Application Tier
└── Database Subnet (10.0.3.0/24)
    └── RDS Database
```

## API Security

### Rate Limiting

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, credentials: LoginCredentials):
    pass

@app.post("/api/submissions/upload")
@limiter.limit("50/hour")  # 50 uploads per hour
async def upload(request: Request, file: UploadFile):
    pass
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Restrictive CORS in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.voyce.ai",
        "https://www.voyce.ai"
    ],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### Input Validation

```python
from pydantic import BaseModel, validator, constr, conint

class VoiceSubmission(BaseModel):
    title: constr(min_length=1, max_length=255)
    category: constr(regex=r'^[a-z_]+$')
    file_size: conint(gt=0, le=52428800)  # Max 50MB

    @validator('title')
    def sanitize_title(cls, v):
        # Remove special characters
        return re.sub(r'[^\w\s-]', '', v)
```

### SQL Injection Prevention

```python
# ALWAYS use parameterized queries
from sqlalchemy import text

# ❌ VULNERABLE - Never do this
query = f"SELECT * FROM users WHERE email = '{user_email}'"

# ✅ SAFE - Use parameterized queries
query = text("SELECT * FROM users WHERE email = :email")
result = session.execute(query, {"email": user_email})

# ✅ SAFE - Use ORM
user = session.query(User).filter(User.email == user_email).first()
```

### XSS Prevention

```python
from markupsafe import escape

# Escape user input before rendering
def render_comment(comment: str) -> str:
    return escape(comment)

# Use Content Security Policy
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https://api.voyce.ai"
    )
    return response
```

### CSRF Protection

```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/api/submissions/upload")
async def upload(
    request: Request,
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    # Process upload
```

### File Upload Security

```python
import magic
import os

ALLOWED_MIME_TYPES = [
    'audio/wav',
    'audio/mpeg',
    'audio/mp4',
    'audio/ogg',
    'audio/flac'
]

MAX_FILE_SIZE = 52428800  # 50MB

async def validate_audio_file(file: UploadFile) -> bool:
    # Check file size
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    # Verify MIME type
    file_content = await file.read(1024)
    mime = magic.from_buffer(file_content, mime=True)
    await file.seek(0)

    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "Invalid file type")

    return True
```

## Infrastructure Security

### Secrets Management

**AWS Secrets Manager:**

```python
import boto3
import json

def get_secret(secret_name: str) -> dict:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
db_credentials = get_secret('voyce/prod/database')
DB_PASSWORD = db_credentials['password']
```

**Environment Variables:**

```python
# ❌ Never hardcode secrets
API_KEY = "sk-1234567890abcdef"

# ✅ Use environment variables
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not set")
```

### Container Security

```dockerfile
# Use minimal base images
FROM python:3.9-slim

# Run as non-root user
RUN useradd -m -u 1000 voyce
USER voyce

# Don't install unnecessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Scan for vulnerabilities
# docker scan voyce-api:latest
```

### Database Security

```sql
-- Create read-only user for analytics
CREATE USER analytics_readonly WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE voyce_prod TO analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- Revoke unnecessary privileges
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE voyce_prod FROM PUBLIC;

-- Enable SSL
ALTER SYSTEM SET ssl = on;

-- Set password encryption
ALTER SYSTEM SET password_encryption = 'scram-sha-256';
```

## Secure Development Practices

### Code Review Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] SQL queries use parameterization
- [ ] Authentication/authorization checks
- [ ] Error messages don't leak sensitive info
- [ ] Logging doesn't contain PII
- [ ] Dependencies up to date
- [ ] Security headers configured
- [ ] HTTPS enforced

### Security Testing

**Static Analysis:**

```bash
# Bandit - Python security linter
bandit -r backend/

# Safety - dependency vulnerability scanner
safety check

# Semgrep - SAST tool
semgrep --config=auto backend/
```

**Dynamic Analysis:**

```bash
# OWASP ZAP
zap-cli quick-scan http://localhost:8000

# SQLMap for SQL injection testing
sqlmap -u "http://localhost:8000/api/users?id=1" --batch
```

### Dependency Management

```bash
# Check for vulnerabilities
pip-audit

# Update dependencies
pip list --outdated
pip install --upgrade package_name

# Pin versions in production
pip freeze > requirements.txt
```

## Compliance

### GDPR Compliance

**User Rights:**
- Right to access data
- Right to rectification
- Right to erasure
- Right to data portability
- Right to object

**Implementation:**

```python
@app.get("/api/users/me/data")
async def export_user_data(current_user: User = Depends(get_current_user)):
    """Export all user data (GDPR compliance)"""
    return {
        "user": current_user.to_dict(),
        "submissions": get_user_submissions(current_user.id),
        "analytics": get_user_analytics(current_user.id)
    }

@app.delete("/api/users/me")
async def delete_account(current_user: User = Depends(get_current_user)):
    """Delete user account and all data (Right to erasure)"""
    await delete_user_data(current_user.id)
    return {"message": "Account deleted"}
```

### SOC 2 Compliance

**Requirements:**
- Access controls
- Encryption
- Monitoring and logging
- Incident response
- Regular security audits

### HIPAA Compliance (if applicable)

**For healthcare use cases:**
- Business Associate Agreement (BAA)
- Audit logging
- Access controls
- Encryption at rest and in transit
- Data retention policies

## Incident Response

### Incident Response Plan

**1. Detection**
- Monitor alerts and logs
- Security information from users

**2. Containment**
- Isolate affected systems
- Revoke compromised credentials
- Block malicious IPs

**3. Eradication**
- Remove malware/backdoors
- Patch vulnerabilities
- Update security rules

**4. Recovery**
- Restore from backups
- Verify system integrity
- Resume normal operations

**5. Lessons Learned**
- Document incident
- Update security measures
- Train team on findings

### Security Contacts

```
Security Team: security@voyce.ai
Incident Hotline: +1-XXX-XXX-XXXX
PGP Key: https://voyce.ai/security.asc
```

### Vulnerability Disclosure

**Report security vulnerabilities to:** security@voyce.ai

**Expected Response Time:**
- Acknowledgment: 24 hours
- Initial assessment: 48 hours
- Fix timeline: Based on severity

## Security Checklist

### Development
- [ ] Code reviewed for security issues
- [ ] No secrets in code or version control
- [ ] Input validation implemented
- [ ] Output encoding implemented
- [ ] Dependencies up to date
- [ ] Static analysis passed

### Deployment
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Firewall rules configured
- [ ] Secrets stored securely
- [ ] Access controls configured
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Incident response plan in place

### Ongoing
- [ ] Regular security audits
- [ ] Dependency updates
- [ ] Security training for team
- [ ] Log monitoring
- [ ] Access review
- [ ] Penetration testing

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
