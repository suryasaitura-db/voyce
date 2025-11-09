"""
Celery tasks for scheduled data synchronization.
Handles periodic sync jobs, manual triggers, monitoring, and alerting.
"""
from celery import Celery, Task
from celery.schedules import crontab
from celery.signals import task_failure, task_success
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from functools import wraps

from app.config import settings
from services.sync_service import get_sync_service, DataSyncService

logger = logging.getLogger(__name__)


# Initialize Celery app
celery_app = Celery(
    'voyce_sync',
    broker=settings.CELERY_BROKER_URL if hasattr(settings, 'CELERY_BROKER_URL') else 'redis://localhost:6379/0',
    backend=settings.CELERY_RESULT_BACKEND if hasattr(settings, 'CELERY_RESULT_BACKEND') else 'redis://localhost:6379/0'
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    'sync-submissions-hourly': {
        'task': 'services.sync_scheduler.sync_submissions_to_databricks_task',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {'queue': 'sync'}
    },
    'sync-analyses-hourly': {
        'task': 'services.sync_scheduler.sync_analyses_to_postgres_task',
        'schedule': crontab(minute=30),  # Every hour at minute 30
        'options': {'queue': 'sync'}
    },
    'full-bidirectional-sync-daily': {
        'task': 'services.sync_scheduler.full_bidirectional_sync_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'sync'}
    },
    'validate-sync-daily': {
        'task': 'services.sync_scheduler.validate_sync_task',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        'options': {'queue': 'sync'}
    },
    'cleanup-old-sync-metadata': {
        'task': 'services.sync_scheduler.cleanup_old_metadata_task',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Weekly on Sunday at 4 AM
        'options': {'queue': 'maintenance'}
    }
}

# Route tasks to queues
celery_app.conf.task_routes = {
    'services.sync_scheduler.sync_*': {'queue': 'sync'},
    'services.sync_scheduler.validate_*': {'queue': 'validation'},
    'services.sync_scheduler.cleanup_*': {'queue': 'maintenance'},
}


def async_task(func):
    """Decorator to run async functions in Celery tasks."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper


class SyncTask(Task):
    """Base task class for sync operations with automatic retry and error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 300}  # Retry 3 times, wait 5 min between retries
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes backoff
    retry_jitter = True

    _sync_service: Optional[DataSyncService] = None

    @property
    def sync_service(self) -> DataSyncService:
        """Get or create sync service instance (cached per worker)."""
        if self._sync_service is None:
            loop = asyncio.get_event_loop()
            self._sync_service = loop.run_until_complete(get_sync_service())
        return self._sync_service


@celery_app.task(
    name='services.sync_scheduler.sync_submissions_to_databricks_task',
    base=SyncTask,
    bind=True
)
@async_task
async def sync_submissions_to_databricks_task(
    self,
    incremental: bool = True,
    force_full_sync: bool = False
) -> Dict[str, Any]:
    """
    Celery task to sync voice submissions from PostgreSQL to Databricks.

    Args:
        incremental: Only sync new/updated records
        force_full_sync: Force full sync

    Returns:
        Sync result dictionary
    """
    logger.info(f"Starting sync_submissions_to_databricks_task (incremental={incremental})")

    try:
        sync_service = await get_sync_service()
        result = await sync_service.sync_submissions_to_databricks(
            incremental=incremental,
            force_full_sync=force_full_sync
        )

        logger.info(f"Task completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        raise


@celery_app.task(
    name='services.sync_scheduler.sync_analyses_to_postgres_task',
    base=SyncTask,
    bind=True
)
@async_task
async def sync_analyses_to_postgres_task(
    self,
    incremental: bool = True,
    force_full_sync: bool = False
) -> Dict[str, Any]:
    """
    Celery task to sync AI analyses from Databricks to PostgreSQL.

    Args:
        incremental: Only sync new/updated records
        force_full_sync: Force full sync

    Returns:
        Sync result dictionary
    """
    logger.info(f"Starting sync_analyses_to_postgres_task (incremental={incremental})")

    try:
        sync_service = await get_sync_service()
        result = await sync_service.sync_analyses_to_postgres(
            incremental=incremental,
            force_full_sync=force_full_sync
        )

        logger.info(f"Task completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        raise


@celery_app.task(
    name='services.sync_scheduler.full_bidirectional_sync_task',
    base=SyncTask,
    bind=True
)
@async_task
async def full_bidirectional_sync_task(self) -> Dict[str, Any]:
    """
    Celery task to perform full bidirectional sync.

    Returns:
        Combined sync result dictionary
    """
    logger.info("Starting full_bidirectional_sync_task")

    try:
        sync_service = await get_sync_service()
        result = await sync_service.full_bidirectional_sync()

        logger.info(f"Task completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        raise


@celery_app.task(
    name='services.sync_scheduler.validate_sync_task',
    base=SyncTask,
    bind=True
)
@async_task
async def validate_sync_task(self) -> Dict[str, Any]:
    """
    Celery task to validate sync status.

    Returns:
        Validation result dictionary
    """
    logger.info("Starting validate_sync_task")

    try:
        sync_service = await get_sync_service()
        result = await sync_service.validate_sync()

        logger.info(f"Validation completed: {result}")

        # Check for sync issues
        for table, validation in result.items():
            if isinstance(validation, dict) and not validation.get("in_sync", True):
                logger.warning(
                    f"Sync validation failed for {table}: "
                    f"PG={validation.get('postgresql_count')}, "
                    f"DB={validation.get('databricks_count')}"
                )

                # Send alert (implement your alerting logic here)
                await send_sync_alert(
                    "Sync Validation Failed",
                    f"Table {table} is out of sync. Difference: {validation.get('difference')}"
                )

        return result

    except Exception as e:
        logger.error(f"Validation task failed: {e}", exc_info=True)
        raise


@celery_app.task(
    name='services.sync_scheduler.manual_sync_trigger',
    base=SyncTask,
    bind=True
)
@async_task
async def manual_sync_trigger(
    self,
    sync_type: str = "bidirectional",
    force_full: bool = False
) -> Dict[str, Any]:
    """
    Manually triggered sync task.

    Args:
        sync_type: Type of sync ('bidirectional', 'submissions', 'analyses')
        force_full: Force full sync

    Returns:
        Sync result dictionary
    """
    logger.info(f"Manual sync triggered: type={sync_type}, force_full={force_full}")

    try:
        sync_service = await get_sync_service()

        if sync_type == "bidirectional":
            result = await sync_service.full_bidirectional_sync()
        elif sync_type == "submissions":
            result = await sync_service.sync_submissions_to_databricks(
                incremental=not force_full,
                force_full_sync=force_full
            )
        elif sync_type == "analyses":
            result = await sync_service.sync_analyses_to_postgres(
                incremental=not force_full,
                force_full_sync=force_full
            )
        else:
            raise ValueError(f"Invalid sync_type: {sync_type}")

        logger.info(f"Manual sync completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Manual sync failed: {e}", exc_info=True)
        raise


@celery_app.task(
    name='services.sync_scheduler.get_sync_status',
    bind=True
)
@async_task
async def get_sync_status(self) -> Dict[str, Any]:
    """
    Get current sync status and statistics.

    Returns:
        Sync status dictionary
    """
    logger.info("Getting sync status")

    try:
        sync_service = await get_sync_service()
        status = await sync_service.get_sync_status()

        return status

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}", exc_info=True)
        raise


@celery_app.task(
    name='services.sync_scheduler.cleanup_old_metadata_task',
    bind=True
)
@async_task
async def cleanup_old_metadata_task(self, retention_days: int = 90) -> Dict[str, Any]:
    """
    Clean up old sync metadata records.

    Args:
        retention_days: Number of days to retain metadata

    Returns:
        Cleanup result dictionary
    """
    logger.info(f"Starting cleanup of sync metadata older than {retention_days} days")

    try:
        from app.database import async_session_maker
        from sqlalchemy import text

        async with async_session_maker() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            delete_query = text("""
                DELETE FROM sync_metadata
                WHERE created_at < :cutoff_date
                AND sync_status = 'completed'
            """)

            result = await session.execute(delete_query, {"cutoff_date": cutoff_date})
            deleted_count = result.rowcount

            await session.commit()

            logger.info(f"Cleaned up {deleted_count} old sync metadata records")

            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        raise


# Signal handlers for monitoring and alerting


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Handle successful task completion."""
    task_name = sender.name if sender else "unknown"
    logger.info(f"Task succeeded: {task_name}")

    # Track successful syncs
    if "sync" in task_name and isinstance(result, dict):
        records_synced = result.get("records_synced", 0)
        duration = result.get("duration_seconds", 0)

        logger.info(
            f"Sync metrics - Task: {task_name}, "
            f"Records: {records_synced}, Duration: {duration:.2f}s"
        )


@task_failure.connect
def task_failure_handler(sender=None, exception=None, traceback=None, **kwargs):
    """Handle task failure."""
    task_name = sender.name if sender else "unknown"
    logger.error(f"Task failed: {task_name}, Error: {exception}")

    # Send alert for critical failures
    if "sync" in task_name:
        asyncio.create_task(
            send_sync_alert(
                f"Sync Task Failed: {task_name}",
                f"Error: {str(exception)}\n\nTraceback: {traceback}"
            )
        )


async def send_sync_alert(subject: str, message: str):
    """
    Send alert notification for sync issues.

    Args:
        subject: Alert subject
        message: Alert message

    Note: Implement your preferred alerting mechanism (email, Slack, PagerDuty, etc.)
    """
    logger.warning(f"ALERT: {subject}\n{message}")

    # TODO: Implement your alerting logic here
    # Examples:
    # - Send email via SMTP
    # - Post to Slack webhook
    # - Create PagerDuty incident
    # - Send SMS via Twilio
    # - Post to monitoring dashboard

    # Example Slack webhook (uncomment and configure):
    # try:
    #     import httpx
    #     webhook_url = settings.SLACK_WEBHOOK_URL
    #     async with httpx.AsyncClient() as client:
    #         await client.post(
    #             webhook_url,
    #             json={
    #                 "text": f"*{subject}*\n```{message}```",
    #                 "username": "Voyce Sync Monitor"
    #             }
    #         )
    # except Exception as e:
    #     logger.error(f"Failed to send Slack alert: {e}")

    pass


# Utility functions for task management


def trigger_immediate_sync(sync_type: str = "bidirectional", force_full: bool = False) -> str:
    """
    Trigger an immediate sync job.

    Args:
        sync_type: Type of sync
        force_full: Force full sync

    Returns:
        Task ID
    """
    task = manual_sync_trigger.apply_async(
        kwargs={"sync_type": sync_type, "force_full": force_full},
        queue="sync"
    )

    logger.info(f"Triggered immediate sync: {task.id}")
    return task.id


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a task.

    Args:
        task_id: Celery task ID

    Returns:
        Task status dictionary
    """
    from celery.result import AsyncResult

    task = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None,
        "traceback": task.traceback if task.failed() else None
    }


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running task.

    Args:
        task_id: Celery task ID

    Returns:
        True if successfully cancelled
    """
    from celery.result import AsyncResult

    task = AsyncResult(task_id, app=celery_app)
    task.revoke(terminate=True)

    logger.info(f"Cancelled task: {task_id}")
    return True


def get_active_tasks() -> List[Dict[str, Any]]:
    """
    Get list of currently active tasks.

    Returns:
        List of active task dictionaries
    """
    inspect = celery_app.control.inspect()
    active = inspect.active()

    if not active:
        return []

    tasks = []
    for worker, task_list in active.items():
        for task in task_list:
            tasks.append({
                "worker": worker,
                "task_id": task["id"],
                "task_name": task["name"],
                "args": task.get("args", []),
                "kwargs": task.get("kwargs", {}),
                "time_start": task.get("time_start")
            })

    return tasks


# Health check endpoint
@celery_app.task(name='services.sync_scheduler.health_check')
def health_check() -> Dict[str, Any]:
    """
    Health check task to verify Celery is working.

    Returns:
        Health status dictionary
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "worker_count": len(celery_app.control.inspect().active() or {})
    }


if __name__ == '__main__':
    # Run celery worker
    celery_app.start()
