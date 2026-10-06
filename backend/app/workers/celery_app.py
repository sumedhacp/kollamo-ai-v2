"""Celery Application and Configuration Module."""

from celery import Celery
from backend.app.core.config import settings
from backend.app.core.logging import logger

celery_app = Celery(
    "kollamo_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard timeout
    task_soft_time_limit=1500,  # 25 minutes soft timeout
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)

if settings.ENVIRONMENT == "test":
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


logger.info(f"Initialized Celery application with broker: {settings.CELERY_BROKER_URL}")
