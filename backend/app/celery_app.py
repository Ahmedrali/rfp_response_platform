"""
Celery application configuration for background task processing
"""
import os
from celery import Celery
from app.utils.config import settings

# Create Celery app instance
celery_app = Celery(
    "rfp_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.document_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "document_processing"},
    },
    
    # Task configuration
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Task retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Beat schedule (if needed for periodic tasks)
    beat_schedule={
        # Add scheduled tasks here if needed
    },
)

# Set default queue
celery_app.conf.task_default_queue = "document_processing"

if __name__ == "__main__":
    celery_app.start()
