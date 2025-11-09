"""
AI analysis model for sentiment, intent, and insights from transcriptions.
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Index, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Analysis(Base):
    """AI analysis model for sentiment and insights."""

    __tablename__ = "analyses"

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

    transcription_id = Column(
        UUID(as_uuid=True) if Base.metadata.bind and 'postgresql' in str(Base.metadata.bind.url) else String(36),
        ForeignKey("transcriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Sentiment analysis
    sentiment = Column(String(50), nullable=True)  # positive, negative, neutral, mixed
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    sentiment_confidence = Column(Float, nullable=True)  # 0 to 1
    sentiment_breakdown = Column(JSON, nullable=True)  # {positive: 0.7, negative: 0.2, neutral: 0.1}

    # Emotion detection
    emotions = Column(JSON, nullable=True)  # {joy: 0.8, anger: 0.1, sadness: 0.05, ...}
    dominant_emotion = Column(String(50), nullable=True)
    emotion_confidence = Column(Float, nullable=True)

    # Intent classification
    intent = Column(String(100), nullable=True)  # feedback, complaint, suggestion, question, etc.
    intent_confidence = Column(Float, nullable=True)
    sub_intents = Column(JSON, nullable=True)  # Array of secondary intents

    # Key insights
    summary = Column(Text, nullable=True)  # AI-generated summary
    key_points = Column(JSON, nullable=True)  # Array of key points/bullets
    action_items = Column(JSON, nullable=True)  # Extracted action items

    # Topic analysis
    topics = Column(JSON, nullable=True)  # Detected topics with scores
    categories = Column(JSON, nullable=True)  # Classification categories
    tags = Column(JSON, nullable=True)  # Auto-generated tags

    # Entity extraction
    entities = Column(JSON, nullable=True)  # Named entities (people, orgs, products, etc.)
    keywords = Column(JSON, nullable=True)  # Important keywords with relevance scores

    # Quality metrics
    clarity_score = Column(Float, nullable=True)  # How clear/coherent is the feedback
    urgency_score = Column(Float, nullable=True)  # How urgent is the issue
    importance_score = Column(Float, nullable=True)  # Overall importance rating

    # Flags
    is_actionable = Column(Boolean, default=False, nullable=False)
    requires_follow_up = Column(Boolean, default=False, nullable=False)
    is_complaint = Column(Boolean, default=False, nullable=False)
    is_positive_feedback = Column(Boolean, default=False, nullable=False)

    # AI model information
    model = Column(String(100), nullable=True)  # gpt-4, claude-3, etc.
    model_version = Column(String(50), nullable=True)
    provider = Column(String(50), nullable=True)  # openai, anthropic, azure, etc.

    # Processing information
    processing_time = Column(Float, nullable=True)  # in seconds
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    # submission = relationship("VoiceSubmission", back_populates="analysis")
    # transcription = relationship("Transcription", back_populates="analysis")

    # Indexes
    __table_args__ = (
        Index('ix_analyses_submission_id', 'submission_id'),
        Index('ix_analyses_transcription_id', 'transcription_id'),
        Index('ix_analyses_sentiment', 'sentiment'),
        Index('ix_analyses_intent', 'intent'),
        Index('ix_analyses_created_at', 'created_at'),
        Index('ix_analyses_importance_score', 'importance_score'),
    )

    def __repr__(self):
        return f"<Analysis(id={self.id}, submission_id={self.submission_id}, sentiment={self.sentiment}, intent={self.intent})>"

    def to_dict(self):
        """Convert analysis to dictionary."""
        return {
            "id": str(self.id),
            "submission_id": str(self.submission_id),
            "transcription_id": str(self.transcription_id),
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
            "sentiment_confidence": self.sentiment_confidence,
            "sentiment_breakdown": self.sentiment_breakdown,
            "emotions": self.emotions,
            "dominant_emotion": self.dominant_emotion,
            "emotion_confidence": self.emotion_confidence,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "sub_intents": self.sub_intents,
            "summary": self.summary,
            "key_points": self.key_points,
            "action_items": self.action_items,
            "topics": self.topics,
            "categories": self.categories,
            "tags": self.tags,
            "entities": self.entities,
            "keywords": self.keywords,
            "clarity_score": self.clarity_score,
            "urgency_score": self.urgency_score,
            "importance_score": self.importance_score,
            "is_actionable": self.is_actionable,
            "requires_follow_up": self.requires_follow_up,
            "is_complaint": self.is_complaint,
            "is_positive_feedback": self.is_positive_feedback,
            "model": self.model,
            "model_version": self.model_version,
            "provider": self.provider,
            "processing_time": self.processing_time,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "error_message": self.error_message,
        }
