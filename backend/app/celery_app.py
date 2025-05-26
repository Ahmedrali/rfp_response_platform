"""
Celery application configuration for background task processing
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery

# Load environment variables first
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.utils.config import settings

# Create Celery app instance
celery_app = Celery(
    "rfp_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.rfp_tasks",
    ]
)

# Make environment variables available to workers through config
celery_app.conf.update(
    # OpenAI and RAG settings
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL"),
    CHAT_MODEL=os.getenv("CHAT_MODEL"),
    EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL"),

    # Celery configuration
    # Task routing
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "document_processing"},
        "app.tasks.rfp_tasks.*": {"queue": "document_processing"},
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
