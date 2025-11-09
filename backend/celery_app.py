"""
Celery application configuration for Voyce data synchronization.
Import this module to use Celery with the sync scheduler.
"""
from services.sync_scheduler import celery_app

# Re-export celery_app for easier imports
__all__ = ['celery_app']

if __name__ == '__main__':
    celery_app.start()
