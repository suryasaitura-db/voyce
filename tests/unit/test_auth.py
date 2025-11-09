"""
Unit tests for authentication
"""
import pytest
from backend.services.auth_service import AuthService


class TestAuthService:
    """Test authentication service"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self):
        """Test password verification"""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        # Correct password
        assert AuthService.verify_password(password, hashed) is True

        # Incorrect password
        assert AuthService.verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = AuthService.create_access_token(data)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_decode_token(self):
        """Test JWT token decoding"""
        original_data = {"sub": "test@example.com", "user_id": "123"}
        token = AuthService.create_access_token(original_data)

        decoded = AuthService.decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == original_data["sub"]
        assert decoded["user_id"] == original_data["user_id"]

    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        with pytest.raises(Exception):
            AuthService.decode_token("invalid.token.here")


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints"""

    async def test_register_user(self, client):
        """Test user registration"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "Password123!"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "password" not in data

    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "username": "anotheruser",
                "password": "Password123!"
            }
        )

        assert response.status_code == 400

    async def test_login(self, client, test_user):
        """Test user login"""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401

    async def test_get_current_user(self, authenticated_client, test_user):
        """Test getting current user"""
        response = await authenticated_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username

    async def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = await client.get("/api/auth/me")

        assert response.status_code == 401
