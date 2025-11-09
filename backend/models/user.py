"""
User model for authentication and authorization.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    # Primary key
    id = Column(
        UUID(as_uuid=True) if Base.metadata.bind and 'postgresql' in str(Base.metadata.bind.url) else String(36),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile fields
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Additional fields
    bio = Column(Text, nullable=True)
    organization = Column(String(255), nullable=True)
    role = Column(String(50), default="user", nullable=False)

    # Indexes
    __table_args__ = (
        Index('ix_users_email', 'email'),
        Index('ix_users_username', 'username'),
        Index('ix_users_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

    def to_dict(self):
        """Convert user to dictionary (exclude sensitive data)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "bio": self.bio,
            "organization": self.organization,
            "role": self.role,
        }
