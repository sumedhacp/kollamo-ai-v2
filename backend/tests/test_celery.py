"""Tests for Celery Application Configuration and Task Registration (Phase 5)."""

import pytest
from app.core.config import settings
from app.workers.celery_app import celery_app


def test_celery_app_initialization() -> None:
    """Verifies that Celery application initializes with canonical app name and settings."""
    assert celery_app.main == "kollamo"
    expected_broker = getattr(settings, "REDIS_URL", settings.CELERY_BROKER_URL)
    # Broker URL should match application configuration
    assert celery_app.conf.broker_url == expected_broker


def test_celery_configuration_settings() -> None:
    """Verifies task serializers, timezone, timeouts, and safe content handling."""
    conf = celery_app.conf
    assert conf.task_serializer == "json"
    assert conf.result_serializer == "json"
    assert conf.accept_content == ["json"]
    assert conf.timezone == "UTC"
    assert conf.enable_utc is True
    assert conf.task_time_limit == 1800  # 30 minutes hard timeout
    assert conf.task_soft_time_limit == 1500  # 25 minutes soft timeout
    assert conf.task_acks_late is True


def test_celery_tasks_registered() -> None:
    """Verifies that canonical Phase 5 task 'process_analysis_job' is registered."""
    registered = celery_app.tasks.keys()
    assert "process_analysis_job" in registered
    assert "process_youtube_analysis_job" in registered


def test_celery_configuration_does_not_leak_secrets() -> None:
    """Verifies that Celery configuration strings and logs do not expose sensitive credentials."""
    conf_dict = celery_app.conf.humanize()
    # Confirm passwords / secret tokens are not dumped in plain text
    assert "super_secret" not in conf_dict
    assert "APP_SECRET_KEY" not in conf_dict
