"""
Transcription model for voice-to-text conversion results.
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Index, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Transcription(Base):
    """Transcription model for voice-to-text results."""

    __tablename__ = "transcriptions"

    # Primary key
    id = Column(
        UUID(as_uuid=True) if Base.metadata.bind and 'postgresql' in str(Base.metadata.bind.url) else String(36),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign keys
    submission_id = Column(
        UUID(as_uuid=True) if Base.metadata.bind and 'postgresql' in str(Base.metadata.bind.url) else String(36),
        ForeignKey("voice_submissions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Transcription content
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=True)  # ISO 639-1 language code
    confidence = Column(Float, nullable=True)  # Overall confidence score 0-1

    # Word-level timestamps and confidence
    words = Column(JSON, nullable=True)  # Array of {word, start, end, confidence}
    segments = Column(JSON, nullable=True)  # Array of segments with timestamps

    # Transcription metadata
    model = Column(String(100), nullable=True)  # whisper-large-v3, etc.
    model_version = Column(String(50), nullable=True)
    provider = Column(String(50), nullable=True)  # openai, assemblyai, azure, etc.

    # Processing information
    processing_time = Column(Float, nullable=True)  # in seconds
    audio_duration = Column(Float, nullable=True)  # in seconds

    # Quality metrics
    word_count = Column(Integer, nullable=True)
    speaking_rate = Column(Float, nullable=True)  # words per minute
    silence_duration = Column(Float, nullable=True)  # total silence in seconds

    # Additional features
    detected_language = Column(String(10), nullable=True)
    language_confidence = Column(Float, nullable=True)
    is_multilingual = Column(Boolean, default=False, nullable=False)

    # Entity extraction
    entities = Column(JSON, nullable=True)  # Named entities, keywords, etc.
    topics = Column(JSON, nullable=True)  # Detected topics/themes

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    # submission = relationship("VoiceSubmission", back_populates="transcription")

    # Indexes
    __table_args__ = (
        Index('ix_transcriptions_submission_id', 'submission_id'),
        Index('ix_transcriptions_language', 'language'),
        Index('ix_transcriptions_created_at', 'created_at'),
        Index('ix_transcriptions_confidence', 'confidence'),
    )

    def __repr__(self):
        return f"<Transcription(id={self.id}, submission_id={self.submission_id}, language={self.language}, confidence={self.confidence})>"

    def to_dict(self):
        """Convert transcription to dictionary."""
        return {
            "id": str(self.id),
            "submission_id": str(self.submission_id),
            "text": self.text,
            "language": self.language,
            "confidence": self.confidence,
            "words": self.words,
            "segments": self.segments,
            "model": self.model,
            "model_version": self.model_version,
            "provider": self.provider,
            "processing_time": self.processing_time,
            "audio_duration": self.audio_duration,
            "word_count": self.word_count,
            "speaking_rate": self.speaking_rate,
            "silence_duration": self.silence_duration,
            "detected_language": self.detected_language,
            "language_confidence": self.language_confidence,
            "is_multilingual": self.is_multilingual,
            "entities": self.entities,
            "topics": self.topics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "error_message": self.error_message,
        }

    def get_summary(self) -> str:
        """Get a summary of the transcription."""
        if self.text:
            # Return first 200 characters
            return self.text[:200] + "..." if len(self.text) > 200 else self.text
        return ""
