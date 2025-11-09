"""
Authentication service for JWT token generation and password hashing.
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Token decode failed: {str(e)}")
        raise


def create_email_verification_token(email: str) -> str:
    """
    Create a token for email verification.

    Args:
        email: User email address

    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {
        "sub": email,
        "type": "email_verification",
        "exp": expire,
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_password_reset_token(email: str) -> str:
    """
    Create a token for password reset.

    Args:
        email: User email address

    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {
        "sub": email,
        "type": "password_reset",
        "exp": expire,
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_email_token(token: str) -> str:
    """
    Verify an email verification token.

    Args:
        token: Email verification token

    Returns:
        Email address from token

    Raises:
        JWTError: If token is invalid
    """
    payload = decode_token(token)

    if payload.get("type") != "email_verification":
        raise JWTError("Invalid token type")

    email = payload.get("sub")
    if not email:
        raise JWTError("Invalid token payload")

    return email


def verify_password_reset_token(token: str) -> str:
    """
    Verify a password reset token.

    Args:
        token: Password reset token

    Returns:
        Email address from token

    Raises:
        JWTError: If token is invalid
    """
    payload = decode_token(token)

    if payload.get("type") != "password_reset":
        raise JWTError("Invalid token type")

    email = payload.get("sub")
    if not email:
        raise JWTError("Invalid token payload")

    return email
