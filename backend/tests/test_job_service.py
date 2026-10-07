"""Tests for JobStateService Lifecycle Operations and Progress Tracking (Phase 5)."""

import uuid
import pytest
from app.services.jobs import JobStateService, JobNotFoundError


@pytest.fixture
def memory_job_service() -> JobStateService:
    """Provides a fresh isolated JobStateService using in-memory store."""
    service = JobStateService(redis_client=None, use_memory_fallback=True)
    service.clear()
    return service


def test_job_service_create_job(memory_job_service: JobStateService) -> None:
    """Verifies creating an initial job records QUEUED status and initial progress."""
    job_id = str(uuid.uuid4())
    payload = {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "comment_limit": 100}

    record = memory_job_service.create_job(job_id=job_id, request_data=payload)

    assert record["job_id"] == job_id
    assert record["status"] == "QUEUED"
    assert record["result"] is None
    assert record["error"] is None
    assert "created_at" in record

    progress = record["progress"]
    assert progress["stage"] == "QUEUED"
    assert progress["completed"] == 0
    assert progress["total"] is None
    assert progress["percentage"] is None


def test_job_service_update_progress_and_stage(memory_job_service: JobStateService) -> None:
    """Verifies updating progress correctly reflects stage changes."""
    job_id = str(uuid.uuid4())
    memory_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    updated = memory_job_service.update_job(
        job_id=job_id,
        status="PROCESSING",
        progress={"stage": "SENTIMENT_ANALYSIS", "completed": 42, "total": 100, "percentage": 42},
    )

    assert updated is not None
    assert updated["status"] == "PROCESSING"
    assert updated["progress"]["stage"] == "SENTIMENT_ANALYSIS"
    assert updated["progress"]["completed"] == 42
    assert updated["progress"]["total"] == 100
    assert updated["progress"]["percentage"] == 42


def test_job_service_mark_completed(memory_job_service: JobStateService) -> None:
    """Verifies updating job to COMPLETED stores result and clears error."""
    job_id = str(uuid.uuid4())
    memory_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    result_payload = {
        "video": {"video_id": "test_id", "title": "Test Title"},
        "total_comments": 5,
        "processed_comments": 5,
        "comments": [],
    }

    updated = memory_job_service.update_job(
        job_id=job_id,
        status="COMPLETED",
        progress={"stage": "COMPLETED", "completed": 5, "total": 5, "percentage": 100},
        result=result_payload,
    )

    assert updated["status"] == "COMPLETED"
    assert updated["result"] == result_payload
    assert updated["error"] is None


def test_job_service_mark_failed(memory_job_service: JobStateService) -> None:
    """Verifies updating job to FAILED records error detail."""
    job_id = str(uuid.uuid4())
    memory_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    error_payload = {
        "code": "MODEL_NOT_READY",
        "message": "The sentiment model is not ready.",
        "details": None,
    }

    updated = memory_job_service.update_job(
        job_id=job_id,
        status="FAILED",
        error=error_payload,
    )

    assert updated["status"] == "FAILED"
    assert updated["error"] == error_payload
    assert updated["result"] is None


def test_job_service_unknown_job(memory_job_service: JobStateService) -> None:
    """Verifies get_job returns None for non-existent job ID."""
    assert memory_job_service.get_job("non-existent-uuid") is None


def test_job_service_delete_job(memory_job_service: JobStateService) -> None:
    """Verifies delete_job removes the job record."""
    job_id = str(uuid.uuid4())
    memory_job_service.create_job(job_id=job_id, request_data={"test": 1})
    assert memory_job_service.get_job(job_id) is not None

    deleted = memory_job_service.delete_job(job_id)
    assert deleted is True
    assert memory_job_service.get_job(job_id) is None
