"""Celery Application and Configuration Module for Kollamo.ai (Phase 5)."""

import os
from celery import Celery

try:
    from app.core.config import settings
    from app.core.logging import logger
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logging import logger

redis_broker = getattr(settings, "REDIS_URL", getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"))

celery_app = Celery(
    "kollamo",
    broker=redis_broker,
    backend=redis_broker,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard timeout (Section 68)
    task_soft_time_limit=1500,  # 25 minutes soft timeout
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)

# Test environment configuration
if getattr(settings, "ENVIRONMENT", "") == "test" or os.environ.get("PYTEST_CURRENT_TEST"):
    celery_app.conf.update(
        task_always_eager=False,  # Keep explicit delay mocking supported
    )

logger.info(f"Initialized Celery application 'kollamo' with broker configured")
