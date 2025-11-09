"""
Application configuration using pydantic-settings.
Loads settings from environment variables and .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Literal
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application settings
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment"
    )
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Database settings
    DB_BACKEND: Literal["postgresql", "databricks"] = Field(
        default="postgresql",
        description="Database backend to use"
    )

    # PostgreSQL settings
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="voyce", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="", description="PostgreSQL password")

    # Databricks settings
    DATABRICKS_SERVER_HOSTNAME: str = Field(default="", description="Databricks server hostname")
    DATABRICKS_HTTP_PATH: str = Field(default="", description="Databricks HTTP path")
    DATABRICKS_ACCESS_TOKEN: str = Field(default="", description="Databricks access token")
    DATABRICKS_CATALOG: str = Field(default="main", description="Databricks catalog")
    DATABRICKS_SCHEMA: str = Field(default="voyce", description="Databricks schema")

    # JWT settings
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token signing"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="JWT access token expiration in minutes"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="JWT refresh token expiration in days"
    )

    # Storage settings
    STORAGE_BACKEND: Literal["local", "s3", "databricks_volumes"] = Field(
        default="local",
        description="Storage backend for file uploads"
    )
    LOCAL_STORAGE_PATH: str = Field(
        default="./uploads",
        description="Local storage path"
    )

    # AWS S3 settings
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS secret access key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    S3_BUCKET_NAME: str = Field(default="", description="S3 bucket name")

    # Databricks Volumes settings
    DATABRICKS_VOLUME_PATH: str = Field(
        default="/Volumes/main/voyce/uploads",
        description="Databricks volume path"
    )

    # Celery settings for data sync
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )

    # Data sync settings
    SYNC_BATCH_SIZE: int = Field(
        default=1000,
        description="Number of records to sync in each batch"
    )
    SYNC_INTERVAL_MINUTES: int = Field(
        default=60,
        description="How often to sync data (in minutes)"
    )

    # Security settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(
        default=True,
        description="Require uppercase in password"
    )
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(
        default=True,
        description="Require lowercase in password"
    )
    PASSWORD_REQUIRE_DIGIT: bool = Field(
        default=True,
        description="Require digit in password"
    )
    PASSWORD_REQUIRE_SPECIAL: bool = Field(
        default=True,
        description="Require special character in password"
    )

    # File upload settings
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file upload size in bytes"
    )
    ALLOWED_AUDIO_EXTENSIONS: list[str] = Field(
        default=["wav", "mp3", "m4a", "ogg", "webm"],
        description="Allowed audio file extensions"
    )

    # TLS settings
    TLS_MIN_VERSION: str = Field(
        default="1.2",
        description="Minimum TLS version"
    )

    # CORS settings
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "chrome-extension://*"
        ],
        description="Allowed CORS origins"
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, v: str, info) -> str:
        """Validate JWT secret key in production."""
        if info.data.get("ENVIRONMENT") == "production" and v == "your-secret-key-change-in-production":
            raise ValueError("JWT_SECRET_KEY must be changed in production")
        return v

    @property
    def database_url(self) -> str:
        """Get database URL based on backend."""
        if self.DB_BACKEND == "postgresql":
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        elif self.DB_BACKEND == "databricks":
            return (
                f"databricks://token:{self.DATABRICKS_ACCESS_TOKEN}"
                f"@{self.DATABRICKS_SERVER_HOSTNAME}:443/{self.DATABRICKS_CATALOG}.{self.DATABRICKS_SCHEMA}"
                f"?http_path={self.DATABRICKS_HTTP_PATH}"
            )
        else:
            raise ValueError(f"Unsupported database backend: {self.DB_BACKEND}")


# Global settings instance
settings = Settings()
