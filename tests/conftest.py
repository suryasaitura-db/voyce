"""
Pytest configuration and fixtures for Voyce tests
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.models.user import User
from backend.services.auth_service import AuthService


# Test database URL
TEST_DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql+asyncpg://postgres:postgres@localhost:5432/voyce_test'
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=AuthService.hash_password("password123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(test_user) -> str:
    """Generate auth token for test user"""
    token = AuthService.create_access_token(
        data={"sub": test_user.email, "user_id": str(test_user.id)}
    )
    return token


@pytest_asyncio.fixture
async def authenticated_client(client, auth_token) -> AsyncClient:
    """Create authenticated HTTP client"""
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


@pytest.fixture
def sample_audio_file(tmp_path):
    """Create sample audio file for testing"""
    import numpy as np
    from scipy.io.wavfile import write

    # Generate 1 second of silence
    sample_rate = 16000
    duration = 1
    samples = np.zeros(sample_rate * duration, dtype=np.int16)

    audio_file = tmp_path / "test_audio.wav"
    write(str(audio_file), sample_rate, samples)

    return audio_file


@pytest.fixture
def mock_whisper_response():
    """Mock Whisper API response"""
    return {
        "text": "This is a test transcription.",
        "language": "en",
        "duration": 1.0,
        "segments": [
            {
                "text": "This is a test transcription.",
                "start": 0.0,
                "end": 1.0,
                "confidence": 0.95
            }
        ]
    }


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    return {
        "summary": "Test feedback about a product issue.",
        "sentiment": "negative",
        "sentiment_score": -0.6,
        "sentiment_reasoning": "User reports a problem with the product",
        "urgency": 4,
        "urgency_reasoning": "Issue requires prompt attention",
        "category_l1": "Product",
        "category_l2": "Quality",
        "category_l3": "Defect",
        "entities": {
            "products": ["Product X"],
            "issues": ["defect", "malfunction"]
        },
        "keywords": ["product", "issue", "defect", "quality"],
        "topics": ["product quality", "defect report"],
        "confidence": 0.92
    }
