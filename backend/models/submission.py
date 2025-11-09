"""
Voice submission model for audio feedback.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class VoiceSubmission(Base):
    """Voice submission model for audio feedback."""

    __tablename__ = "voice_submissions"

    # Primary key
    id = Column(
        UUID(as_uuid=True) if Base.metadata.bind and 'postgresql' in str(Base.metadata.bind.url) else String(36),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True) if Base.metadata.bind and 'postgresql' in str(Base.metadata.bind.url) else String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # File information
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_format = Column(String(50), nullable=False)  # wav, mp3, m4a, etc.
    mime_type = Column(String(100), nullable=False)

    # Audio metadata
    duration = Column(Float, nullable=True)  # in seconds
    sample_rate = Column(Integer, nullable=True)  # in Hz
    channels = Column(Integer, nullable=True)  # mono=1, stereo=2

    # Submission metadata
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    category = Column(String(100), nullable=True)

    # Source information
    source = Column(String(50), nullable=True)  # web, mobile, chrome_extension, etc.
    source_url = Column(String(500), nullable=True)  # URL of the page/app where feedback was given
    user_agent = Column(String(500), nullable=True)

    # Processing status
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True
    )  # pending, processing, completed, failed

    # Flags
    is_processed = Column(Boolean, default=False, nullable=False)
    is_transcribed = Column(Boolean, default=False, nullable=False)
    is_analyzed = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Relationships
    # user = relationship("User", back_populates="submissions")
    # transcription = relationship("Transcription", back_populates="submission", uselist=False)
    # analysis = relationship("Analysis", back_populates="submission", uselist=False)

    # Indexes
    __table_args__ = (
        Index('ix_submissions_user_id', 'user_id'),
        Index('ix_submissions_status', 'status'),
        Index('ix_submissions_created_at', 'created_at'),
        Index('ix_submissions_category', 'category'),
        Index('ix_submissions_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<VoiceSubmission(id={self.id}, user_id={self.user_id}, file_name={self.file_name}, status={self.status})>"

    def to_dict(self):
        """Convert submission to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_format": self.file_format,
            "mime_type": self.mime_type,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "category": self.category,
            "source": self.source,
            "source_url": self.source_url,
            "status": self.status,
            "is_processed": self.is_processed,
            "is_transcribed": self.is_transcribed,
            "is_analyzed": self.is_analyzed,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }
