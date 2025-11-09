"""
Analytics router for dashboard and metrics endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from models.user import User
from models.submission import VoiceSubmission
from models.transcription import Transcription
from models.analysis import Analysis
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class DashboardStats(BaseModel):
    """Dashboard statistics schema."""
    total_submissions: int
    processed_submissions: int
    pending_submissions: int
    failed_submissions: int
    total_duration: float  # Total audio duration in seconds
    average_duration: float
    submissions_this_week: int
    submissions_this_month: int


class SentimentDistribution(BaseModel):
    """Sentiment distribution schema."""
    positive: int
    negative: int
    neutral: int
    mixed: int


class CategoryStats(BaseModel):
    """Category statistics schema."""
    category: str
    count: int
    percentage: float


class TimeSeriesPoint(BaseModel):
    """Time series data point."""
    date: str
    count: int


class AnalyticsResponse(BaseModel):
    """Analytics response schema."""
    stats: DashboardStats
    sentiment_distribution: SentimentDistribution
    category_stats: List[CategoryStats]
    submissions_over_time: List[TimeSeriesPoint]
    top_keywords: List[Dict[str, any]]
    top_intents: List[Dict[str, int]]


class TrendAnalysis(BaseModel):
    """Trend analysis schema."""
    period: str
    metric: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend: str  # up, down, stable


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard analytics for the user."""
    logger.info(f"Getting dashboard analytics for user {current_user.id}")

    # Date ranges
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    period_start = now - timedelta(days=days)

    # Get total submissions
    total_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            VoiceSubmission.user_id == current_user.id
        )
    )
    total_submissions = total_result.scalar() or 0

    # Get processed submissions
    processed_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.status == "completed"
            )
        )
    )
    processed_submissions = processed_result.scalar() or 0

    # Get pending submissions
    pending_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.status == "pending"
            )
        )
    )
    pending_submissions = pending_result.scalar() or 0

    # Get failed submissions
    failed_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.status == "failed"
            )
        )
    )
    failed_submissions = failed_result.scalar() or 0

    # Get total and average duration
    duration_result = await db.execute(
        select(
            func.sum(VoiceSubmission.duration),
            func.avg(VoiceSubmission.duration)
        ).where(VoiceSubmission.user_id == current_user.id)
    )
    duration_row = duration_result.one_or_none()
    total_duration = duration_row[0] or 0.0
    average_duration = duration_row[1] or 0.0

    # Get submissions this week
    week_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.created_at >= week_ago
            )
        )
    )
    submissions_this_week = week_result.scalar() or 0

    # Get submissions this month
    month_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.created_at >= month_ago
            )
        )
    )
    submissions_this_month = month_result.scalar() or 0

    # Dashboard stats
    stats = DashboardStats(
        total_submissions=total_submissions,
        processed_submissions=processed_submissions,
        pending_submissions=pending_submissions,
        failed_submissions=failed_submissions,
        total_duration=total_duration,
        average_duration=average_duration,
        submissions_this_week=submissions_this_week,
        submissions_this_month=submissions_this_month
    )

    # Get sentiment distribution
    sentiment_query = await db.execute(
        select(Analysis.sentiment, func.count()).
        join(VoiceSubmission, Analysis.submission_id == VoiceSubmission.id).
        where(VoiceSubmission.user_id == current_user.id).
        group_by(Analysis.sentiment)
    )
    sentiment_data = {row[0]: row[1] for row in sentiment_query.all()}

    sentiment_distribution = SentimentDistribution(
        positive=sentiment_data.get("positive", 0),
        negative=sentiment_data.get("negative", 0),
        neutral=sentiment_data.get("neutral", 0),
        mixed=sentiment_data.get("mixed", 0)
    )

    # Get category stats
    category_query = await db.execute(
        select(VoiceSubmission.category, func.count()).
        where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.category.isnot(None)
            )
        ).
        group_by(VoiceSubmission.category).
        order_by(desc(func.count()))
    )
    category_rows = category_query.all()

    category_stats = []
    for category, count in category_rows:
        percentage = (count / total_submissions * 100) if total_submissions > 0 else 0
        category_stats.append(CategoryStats(
            category=category,
            count=count,
            percentage=round(percentage, 2)
        ))

    # Get submissions over time (daily for the period)
    time_series_query = await db.execute(
        select(
            func.date(VoiceSubmission.created_at).label('date'),
            func.count()
        ).
        where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.created_at >= period_start
            )
        ).
        group_by(func.date(VoiceSubmission.created_at)).
        order_by(func.date(VoiceSubmission.created_at))
    )

    submissions_over_time = [
        TimeSeriesPoint(date=str(row[0]), count=row[1])
        for row in time_series_query.all()
    ]

    # Top keywords (placeholder - would need text analysis)
    top_keywords = []

    # Top intents
    intent_query = await db.execute(
        select(Analysis.intent, func.count()).
        join(VoiceSubmission, Analysis.submission_id == VoiceSubmission.id).
        where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                Analysis.intent.isnot(None)
            )
        ).
        group_by(Analysis.intent).
        order_by(desc(func.count())).
        limit(10)
    )

    top_intents = [
        {"intent": row[0], "count": row[1]}
        for row in intent_query.all()
    ]

    return AnalyticsResponse(
        stats=stats,
        sentiment_distribution=sentiment_distribution,
        category_stats=category_stats,
        submissions_over_time=submissions_over_time,
        top_keywords=top_keywords,
        top_intents=top_intents
    )


@router.get("/trends", response_model=List[TrendAnalysis])
async def get_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trend analysis comparing current period to previous period."""
    logger.info(f"Getting trend analysis for user {current_user.id}")

    # Date ranges
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    # Get submissions this week
    current_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.created_at >= week_ago
            )
        )
    )
    current_count = current_result.scalar() or 0

    # Get submissions previous week
    previous_result = await db.execute(
        select(func.count()).select_from(VoiceSubmission).where(
            and_(
                VoiceSubmission.user_id == current_user.id,
                VoiceSubmission.created_at >= two_weeks_ago,
                VoiceSubmission.created_at < week_ago
            )
        )
    )
    previous_count = previous_result.scalar() or 0

    # Calculate change
    if previous_count > 0:
        change_pct = ((current_count - previous_count) / previous_count) * 100
    else:
        change_pct = 100.0 if current_count > 0 else 0.0

    trend = "up" if change_pct > 5 else "down" if change_pct < -5 else "stable"

    trends = [
        TrendAnalysis(
            period="week",
            metric="submissions",
            current_value=float(current_count),
            previous_value=float(previous_count),
            change_percentage=round(change_pct, 2),
            trend=trend
        )
    ]

    return trends


@router.get("/sentiment-over-time", response_model=List[Dict])
async def get_sentiment_over_time(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sentiment distribution over time."""
    period_start = datetime.utcnow() - timedelta(days=days)

    # This would require more complex query joining submissions and analyses
    # Placeholder implementation
    return []
