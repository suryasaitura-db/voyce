# Testing Documentation

Comprehensive testing guide for the Voyce Voice Feedback Platform.

## Table of Contents

- [Testing Overview](#testing-overview)
- [Test Setup](#test-setup)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [End-to-End Tests](#end-to-end-tests)
- [Performance Tests](#performance-tests)
- [Security Tests](#security-tests)
- [Test Coverage](#test-coverage)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Testing Overview

### Testing Pyramid

```
                    ┌─────────────┐
                    │     E2E     │
                    │   Tests     │  ← Few, slow, expensive
                    │   (10%)     │
               ┌────┴─────────────┴────┐
               │   Integration Tests   │
               │       (30%)           │  ← Moderate
          ┌────┴───────────────────────┴────┐
          │        Unit Tests                │
          │         (60%)                    │  ← Many, fast, cheap
          └──────────────────────────────────┘
```

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test complete user workflows
4. **Performance Tests**: Test system performance and scalability
5. **Security Tests**: Test security controls and vulnerabilities

### Testing Tools

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **httpx**: HTTP client for API testing
- **factory_boy**: Test data factories
- **faker**: Generate fake data
- **locust**: Load testing
- **bandit**: Security testing

## Test Setup

### Install Testing Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov httpx factory-boy faker locust
```

### Test Configuration

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=backend
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    security: Security tests
```

### Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_submissions.py
│   ├── test_analytics.py
│   └── test_services.py
├── integration/
│   ├── __init__.py
│   ├── test_api_auth.py
│   ├── test_api_submissions.py
│   └── test_database.py
├── e2e/
│   ├── __init__.py
│   ├── test_user_flows.py
│   └── test_voice_pipeline.py
├── performance/
│   ├── __init__.py
│   └── locustfile.py
├── security/
│   ├── __init__.py
│   └── test_security.py
└── fixtures/
    ├── audio_samples/
    └── test_data.json
```

### Shared Fixtures (conftest.py)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import asyncio

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.models.user import User
from backend.models.submission import VoiceSubmission

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers"""
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "password"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_audio_file():
    """Create sample audio file"""
    import io
    import wave

    # Create simple WAV file
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        wav_file.writeframes(b'\x00' * 44100)  # 1 second of silence

    buffer.seek(0)
    return buffer
```

## Unit Tests

### Testing Models

```python
# tests/unit/test_models.py
import pytest
from backend.models.user import User
from backend.models.submission import VoiceSubmission


class TestUserModel:
    """Test User model"""

    def test_create_user(self, db_session):
        """Test user creation"""
        user = User(
            email="user@example.com",
            username="testuser",
            hashed_password="hashed_pw"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "user@example.com"
        assert user.is_active is True
        assert user.is_verified is False

    def test_user_to_dict(self, test_user):
        """Test user serialization"""
        user_dict = test_user.to_dict()

        assert "id" in user_dict
        assert "email" in user_dict
        assert "hashed_password" not in user_dict  # Sensitive data excluded

    def test_unique_email_constraint(self, db_session):
        """Test email uniqueness"""
        from sqlalchemy.exc import IntegrityError

        user1 = User(email="same@example.com", username="user1", hashed_password="pw1")
        user2 = User(email="same@example.com", username="user2", hashed_password="pw2")

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestSubmissionModel:
    """Test VoiceSubmission model"""

    def test_create_submission(self, db_session, test_user):
        """Test submission creation"""
        submission = VoiceSubmission(
            user_id=test_user.id,
            file_path="s3://bucket/file.wav",
            file_name="recording.wav",
            file_size=1024,
            file_format="wav",
            mime_type="audio/wav"
        )
        db_session.add(submission)
        db_session.commit()

        assert submission.id is not None
        assert submission.status == "pending"
        assert submission.is_processed is False
```

### Testing Services

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import Mock, patch
from backend.services.voice_processor import VoiceProcessor
from backend.services.sentiment_analyzer import SentimentAnalyzer


class TestVoiceProcessor:
    """Test VoiceProcessor service"""

    @pytest.fixture
    def processor(self):
        return VoiceProcessor()

    def test_validate_audio_format(self, processor):
        """Test audio format validation"""
        assert processor.validate_format("test.wav") is True
        assert processor.validate_format("test.mp3") is True
        assert processor.validate_format("test.txt") is False

    def test_validate_file_size(self, processor):
        """Test file size validation"""
        assert processor.validate_size(1024) is True  # 1KB
        assert processor.validate_size(50 * 1024 * 1024) is True  # 50MB
        assert processor.validate_size(100 * 1024 * 1024) is False  # 100MB

    @patch('backend.services.voice_processor.extract_audio_metadata')
    def test_extract_metadata(self, mock_extract, processor, sample_audio_file):
        """Test metadata extraction"""
        mock_extract.return_value = {
            "duration": 45.5,
            "sample_rate": 44100,
            "channels": 1
        }

        metadata = processor.extract_metadata(sample_audio_file)

        assert metadata["duration"] == 45.5
        assert metadata["sample_rate"] == 44100
        assert metadata["channels"] == 1


class TestSentimentAnalyzer:
    """Test SentimentAnalyzer service"""

    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer()

    def test_analyze_positive_sentiment(self, analyzer):
        """Test positive sentiment detection"""
        text = "I absolutely love this product! It's amazing and works perfectly."
        result = analyzer.analyze(text)

        assert result["sentiment"] == "positive"
        assert result["sentiment_score"] > 0.5

    def test_analyze_negative_sentiment(self, analyzer):
        """Test negative sentiment detection"""
        text = "This is terrible. I hate it and it doesn't work at all."
        result = analyzer.analyze(text)

        assert result["sentiment"] == "negative"
        assert result["sentiment_score"] < -0.5

    def test_analyze_neutral_sentiment(self, analyzer):
        """Test neutral sentiment detection"""
        text = "The product arrived on Tuesday. It is blue."
        result = analyzer.analyze(text)

        assert result["sentiment"] == "neutral"
        assert -0.2 < result["sentiment_score"] < 0.2
```

## Integration Tests

### Testing API Endpoints

```python
# tests/integration/test_api_auth.py
import pytest


class TestAuthAPI:
    """Test authentication API endpoints"""

    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePassword123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "username": "different",
                "password": "Password123!"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "wronguser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test get current user endpoint"""
        response = client.get(
            "/api/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data

    def test_unauthorized_access(self, client):
        """Test unauthorized access"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
```

### Testing Submissions API

```python
# tests/integration/test_api_submissions.py
import pytest
from io import BytesIO


class TestSubmissionsAPI:
    """Test submissions API endpoints"""

    def test_upload_voice_submission(self, client, auth_headers, sample_audio_file):
        """Test voice file upload"""
        files = {"file": ("recording.wav", sample_audio_file, "audio/wav")}
        data = {
            "title": "Product Feedback",
            "category": "feature_request"
        }

        response = client.post(
            "/api/submissions/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        result = response.json()
        assert result["status"] == "pending"
        assert result["file_name"] == "recording.wav"

    def test_upload_invalid_file_type(self, client, auth_headers):
        """Test upload with invalid file type"""
        files = {"file": ("document.pdf", BytesIO(b"pdf content"), "application/pdf")}

        response = client.post(
            "/api/submissions/upload",
            files=files,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_list_submissions(self, client, auth_headers):
        """Test list submissions"""
        response = client.get(
            "/api/submissions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_get_submission_details(self, client, auth_headers, test_submission):
        """Test get submission details"""
        response = client.get(
            f"/api/submissions/{test_submission.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_submission.id)

    def test_delete_submission(self, client, auth_headers, test_submission):
        """Test delete submission"""
        response = client.delete(
            f"/api/submissions/{test_submission.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        response = client.get(
            f"/api/submissions/{test_submission.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
```

## End-to-End Tests

```python
# tests/e2e/test_user_flows.py
import pytest
import time


class TestCompleteUserFlow:
    """Test complete user workflows"""

    def test_user_registration_to_submission(self, client, sample_audio_file):
        """Test complete flow: register -> login -> upload -> view results"""

        # 1. Register user
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "e2e@example.com",
                "username": "e2euser",
                "password": "SecurePass123!",
                "full_name": "E2E User"
            }
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = client.post(
            "/api/auth/login",
            json={"username": "e2euser", "password": "SecurePass123!"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Upload voice file
        files = {"file": ("feedback.wav", sample_audio_file, "audio/wav")}
        upload_response = client.post(
            "/api/submissions/upload",
            files=files,
            data={"title": "E2E Test Feedback"},
            headers=headers
        )
        assert upload_response.status_code == 201
        submission_id = upload_response.json()["id"]

        # 4. Wait for processing (in real scenario)
        time.sleep(1)

        # 5. Get submission details
        details_response = client.get(
            f"/api/submissions/{submission_id}",
            headers=headers
        )
        assert details_response.status_code == 200

        # 6. View dashboard
        dashboard_response = client.get(
            "/api/analytics/dashboard",
            headers=headers
        )
        assert dashboard_response.status_code == 200
```

## Performance Tests

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between


class VoyceUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login on start"""
        response = self.client.post("/api/auth/login", json={
            "username": "loadtest",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_submissions(self):
        """List submissions (common operation)"""
        self.client.get("/api/submissions", headers=self.headers)

    @task(1)
    def get_dashboard(self):
        """Get dashboard analytics"""
        self.client.get("/api/analytics/dashboard", headers=self.headers)

    @task(1)
    def upload_file(self):
        """Upload audio file"""
        files = {"file": ("test.wav", b"audio data", "audio/wav")}
        self.client.post(
            "/api/submissions/upload",
            files=files,
            headers=self.headers
        )
```

Run performance tests:

```bash
# Start API
python main.py

# Run locust
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Open browser: http://localhost:8089
```

## Test Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=backend --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Coverage Goals

- **Overall**: 80% minimum
- **Critical paths**: 95%+
- **Models**: 90%+
- **Services**: 85%+
- **API endpoints**: 80%+

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost/test_db
        run: |
          pytest --cov=backend --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Best Practices

1. **Test Naming**: Use descriptive names (test_should_do_something_when_condition)
2. **AAA Pattern**: Arrange, Act, Assert
3. **Isolation**: Each test should be independent
4. **Fixtures**: Use fixtures for common setup
5. **Mocking**: Mock external dependencies
6. **Fast Tests**: Keep unit tests fast
7. **Deterministic**: Tests should always produce same result
8. **Coverage**: Aim for high coverage, but focus on quality
9. **CI Integration**: Run tests on every commit
10. **Documentation**: Document complex test scenarios
