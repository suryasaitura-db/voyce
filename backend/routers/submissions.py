"""
Voice submissions router for upload and query endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from datetime import datetime

from app.database import get_db
from app.config import settings
from models.user import User
from models.submission import VoiceSubmission
from models.transcription import Transcription
from models.analysis import Analysis
from routers.auth import get_current_user
from services.storage_service import upload_file, get_file_url

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class SubmissionCreate(BaseModel):
    """Submission creation schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


class SubmissionResponse(BaseModel):
    """Submission response schema."""
    id: str
    user_id: str
    file_name: str
    file_size: int
    file_format: str
    duration: Optional[float]
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    status: str
    is_processed: bool
    is_transcribed: bool
    is_analyzed: bool
    created_at: str
    updated_at: str


class SubmissionDetailResponse(SubmissionResponse):
    """Detailed submission response with transcription and analysis."""
    transcription: Optional[dict] = None
    analysis: Optional[dict] = None


class SubmissionListResponse(BaseModel):
    """Paginated submission list response."""
    items: List[SubmissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("/upload", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def upload_voice_submission(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    source: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a voice submission."""
    logger.info(f"Upload attempt by user {current_user.id}: {file.filename}")

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Check file extension
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"
        )

    # Read file
    file_content = await file.read()
    file_size = len(file_content)

    # Check file size
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )

    # Upload file to storage
    try:
        file_path = await upload_file(
            file_content=file_content,
            file_name=file.filename,
            user_id=str(current_user.id),
            content_type=file.content_type or "audio/wav"
        )
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )

    # Parse tags
    tags_list = None
    if tags:
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

    # Create submission record
    submission = VoiceSubmission(
        user_id=current_user.id,
        file_path=file_path,
        file_name=file.filename,
        file_size=file_size,
        file_format=file_extension,
        mime_type=file.content_type or "audio/wav",
        title=title,
        description=description,
        category=category,
        tags=tags_list,
        source=source,
        source_url=source_url,
        status="pending"
    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    logger.info(f"Submission created successfully: {submission.id}")

    # TODO: Trigger async processing (transcription, analysis)
    # This would be done via a task queue like Celery or background tasks

    return SubmissionResponse(**submission.to_dict())


@router.get("/", response_model=SubmissionListResponse)
async def list_submissions(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's voice submissions with pagination."""
    # Build query
    query = select(VoiceSubmission).where(VoiceSubmission.user_id == current_user.id)

    if status_filter:
        query = query.where(VoiceSubmission.status == status_filter)

    if category:
        query = query.where(VoiceSubmission.category == category)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(desc(VoiceSubmission.created_at))
    query = query.limit(page_size).offset((page - 1) * page_size)

    result = await db.execute(query)
    submissions = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return SubmissionListResponse(
        items=[SubmissionResponse(**s.to_dict()) for s in submissions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific submission with transcription and analysis."""
    # Get submission
    result = await db.execute(
        select(VoiceSubmission).where(
            VoiceSubmission.id == submission_id,
            VoiceSubmission.user_id == current_user.id
        )
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Get transcription
    transcription = None
    if submission.is_transcribed:
        result = await db.execute(
            select(Transcription).where(Transcription.submission_id == submission_id)
        )
        trans = result.scalar_one_or_none()
        if trans:
            transcription = trans.to_dict()

    # Get analysis
    analysis = None
    if submission.is_analyzed:
        result = await db.execute(
            select(Analysis).where(Analysis.submission_id == submission_id)
        )
        anal = result.scalar_one_or_none()
        if anal:
            analysis = anal.to_dict()

    return SubmissionDetailResponse(
        **submission.to_dict(),
        transcription=transcription,
        analysis=analysis
    )


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a submission."""
    # Get submission
    result = await db.execute(
        select(VoiceSubmission).where(
            VoiceSubmission.id == submission_id,
            VoiceSubmission.user_id == current_user.id
        )
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # TODO: Delete file from storage

    # Delete submission (cascade will delete transcription and analysis)
    await db.delete(submission)
    await db.commit()

    logger.info(f"Submission deleted: {submission_id}")

    return None
