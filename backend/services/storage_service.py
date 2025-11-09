"""
Storage service for file upload handling.
Supports local storage, S3, and Databricks volumes.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
import logging
import aiofiles
import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


async def upload_file(
    file_content: bytes,
    file_name: str,
    user_id: str,
    content_type: str = "application/octet-stream"
) -> str:
    """
    Upload a file to the configured storage backend.

    Args:
        file_content: File content as bytes
        file_name: Original file name
        user_id: User ID for organizing files
        content_type: MIME type of the file

    Returns:
        File path/URL in the storage system

    Raises:
        Exception: If upload fails
    """
    # Generate unique filename
    file_extension = Path(file_name).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Organize by user and date
    today = datetime.utcnow()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    relative_path = f"{user_id}/{year}/{month}/{day}/{unique_filename}"

    if settings.STORAGE_BACKEND == "local":
        return await upload_to_local(file_content, relative_path)
    elif settings.STORAGE_BACKEND == "s3":
        return await upload_to_s3(file_content, relative_path, content_type)
    elif settings.STORAGE_BACKEND == "databricks_volumes":
        return await upload_to_databricks_volumes(file_content, relative_path)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.STORAGE_BACKEND}")


async def upload_to_local(file_content: bytes, relative_path: str) -> str:
    """
    Upload file to local storage.

    Args:
        file_content: File content as bytes
        relative_path: Relative path for the file

    Returns:
        Full file path
    """
    # Create base directory if it doesn't exist
    base_path = Path(settings.LOCAL_STORAGE_PATH)
    base_path.mkdir(parents=True, exist_ok=True)

    # Full file path
    file_path = base_path / relative_path

    # Create parent directories
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)

    logger.info(f"File uploaded to local storage: {file_path}")

    return str(file_path)


async def upload_to_s3(file_content: bytes, relative_path: str, content_type: str) -> str:
    """
    Upload file to AWS S3.

    Args:
        file_content: File content as bytes
        relative_path: Relative path for the file
        content_type: MIME type of the file

    Returns:
        S3 object key

    Raises:
        ClientError: If S3 upload fails
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    try:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=relative_path,
            Body=file_content,
            ContentType=content_type,
            ServerSideEncryption='AES256'
        )

        logger.info(f"File uploaded to S3: s3://{settings.S3_BUCKET_NAME}/{relative_path}")

        return f"s3://{settings.S3_BUCKET_NAME}/{relative_path}"

    except ClientError as e:
        logger.error(f"S3 upload failed: {str(e)}", exc_info=True)
        raise


async def upload_to_databricks_volumes(file_content: bytes, relative_path: str) -> str:
    """
    Upload file to Databricks Volumes.

    Args:
        file_content: File content as bytes
        relative_path: Relative path for the file

    Returns:
        Volume file path

    Note:
        Databricks volumes are mounted as filesystem paths.
        This assumes the volume is accessible from the runtime environment.
    """
    # Databricks volume path
    volume_path = Path(settings.DATABRICKS_VOLUME_PATH)

    # Full file path
    file_path = volume_path / relative_path

    # Create parent directories
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)

    logger.info(f"File uploaded to Databricks volume: {file_path}")

    return str(file_path)


async def get_file_url(file_path: str, expires_in: int = 3600) -> str:
    """
    Get a presigned URL for accessing a file.

    Args:
        file_path: File path in storage
        expires_in: URL expiration time in seconds

    Returns:
        Presigned URL or file path

    Note:
        For local storage, returns the file path.
        For S3, returns a presigned URL.
        For Databricks volumes, returns the file path.
    """
    if settings.STORAGE_BACKEND == "s3" and file_path.startswith("s3://"):
        # Parse S3 path
        parts = file_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""

        # Generate presigned URL
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}", exc_info=True)
            raise

    # For local and Databricks volumes, return the file path
    return file_path


async def delete_file(file_path: str) -> bool:
    """
    Delete a file from storage.

    Args:
        file_path: File path in storage

    Returns:
        True if successful, False otherwise
    """
    try:
        if settings.STORAGE_BACKEND == "local":
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted from local storage: {file_path}")
                return True

        elif settings.STORAGE_BACKEND == "s3" and file_path.startswith("s3://"):
            # Parse S3 path
            parts = file_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""

            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

            s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"File deleted from S3: {file_path}")
            return True

        elif settings.STORAGE_BACKEND == "databricks_volumes":
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted from Databricks volume: {file_path}")
                return True

        return False

    except Exception as e:
        logger.error(f"File deletion failed: {str(e)}", exc_info=True)
        return False


async def file_exists(file_path: str) -> bool:
    """
    Check if a file exists in storage.

    Args:
        file_path: File path in storage

    Returns:
        True if file exists, False otherwise
    """
    try:
        if settings.STORAGE_BACKEND == "local":
            return os.path.exists(file_path)

        elif settings.STORAGE_BACKEND == "s3" and file_path.startswith("s3://"):
            # Parse S3 path
            parts = file_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""

            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

            try:
                s3_client.head_object(Bucket=bucket, Key=key)
                return True
            except ClientError:
                return False

        elif settings.STORAGE_BACKEND == "databricks_volumes":
            return os.path.exists(file_path)

        return False

    except Exception as e:
        logger.error(f"File existence check failed: {str(e)}", exc_info=True)
        return False
