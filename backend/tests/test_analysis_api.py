"""Tests for Asynchronous Analysis API Endpoints (Phase 5)."""

import uuid
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient

from backend.app.main import app
from app.services.jobs import JobStateService, get_job_state_service, set_job_state_service


@pytest.fixture
def fresh_job_service() -> JobStateService:
    """Provides a fresh isolated JobStateService."""
    service = JobStateService(redis_client=None, use_memory_fallback=True)
    service.clear()
    set_job_state_service(service)
    app.dependency_overrides[get_job_state_service] = lambda: service
    yield service
    set_job_state_service(None)
    app.dependency_overrides.pop(get_job_state_service, None)


@pytest.mark.asyncio
async def test_create_analysis_job_success(
    async_client: AsyncClient, fresh_job_service: JobStateService
) -> None:
    """Verifies valid POST /api/v1/analysis/jobs returns HTTP 202 and QUEUED state."""
    payload = {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "comment_limit": 100,
        "sort_by": "newest",
    }

    with patch("app.api.routes.analysis.process_analysis_job.delay") as mock_delay:
        mock_delay.return_value = MagicMock(id="celery-task-123")
        response = await async_client.post("/api/v1/analysis/jobs", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "QUEUED"

        # Verify job_id is valid UUID
        job_uuid = uuid.UUID(data["job_id"])
        assert str(job_uuid) == data["job_id"]

        # Verify Celery task was enqueued
        assert mock_delay.called
        call_args = mock_delay.call_args[0]
        assert call_args[0] == data["job_id"]
        assert call_args[1]["video_url"] == payload["video_url"]


@pytest.mark.asyncio
async def test_create_analysis_job_validation_error(async_client: AsyncClient) -> None:
    """Verifies that invalid comment_limit or sort_by returns HTTP 422 VALIDATION_ERROR."""
    payload = {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "comment_limit": 999,  # Only 50, 100, 250, 500, ALL allowed
    }
    response = await async_client.post("/api/v1/analysis/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_analysis_job_broker_failure(
    async_client: AsyncClient, fresh_job_service: JobStateService
) -> None:
    """Verifies that broker failure returns HTTP 503 JOB_QUEUE_UNAVAILABLE without leaving orphan job."""
    payload = {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "comment_limit": 100,
    }

    with patch("app.api.routes.analysis.process_analysis_job.delay") as mock_delay:
        mock_delay.side_effect = ConnectionError("Could not connect to Redis broker")
        response = await async_client.post("/api/v1/analysis/jobs", json=payload)

        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "JOB_QUEUE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_get_analysis_job_queued(
    async_client: AsyncClient, fresh_job_service: JobStateService
) -> None:
    """Verifies polling a QUEUED job returns initial progress and null result."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    response = await async_client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["job_id"] == job_id
    assert data["status"] == "QUEUED"
    assert data["progress"]["stage"] == "QUEUED"
    assert data["result"] is None
    assert data["error"] is None


@pytest.mark.asyncio
async def test_get_analysis_job_processing(
    async_client: AsyncClient, fresh_job_service: JobStateService
) -> None:
    """Verifies polling a PROCESSING job returns live stage progress."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})
    fresh_job_service.update_job(
        job_id=job_id,
        status="PROCESSING",
        progress={"stage": "SENTIMENT_ANALYSIS", "completed": 25, "total": 100, "percentage": 25},
    )

    response = await async_client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "PROCESSING"
    assert data["progress"]["stage"] == "SENTIMENT_ANALYSIS"
    assert data["progress"]["completed"] == 25
    assert data["progress"]["total"] == 100
    assert data["progress"]["percentage"] == 25


@pytest.mark.asyncio
async def test_get_analysis_job_completed(
    async_client: AsyncClient, fresh_job_service: JobStateService
) -> None:
    """Verifies polling a COMPLETED job returns normalized results and 100% progress."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    result_payload = {
        "video": {"video_id": "dQw4w9WgXcQ", "title": "Test Title"},
        "total_comments": 1,
        "processed_comments": 1,
        "comments": [
            {
                "comment_id": "c1",
                "text": "Kidilam cinema!",
                "sentiment": "Positive",
                "confidence": 0.95,
                "probabilities": {
                    "Positive": 0.95,
                    "Negative": 0.02,
                    "Neutral": 0.01,
                    "Mixed": 0.01,
                    "Unsupported": 0.01,
                },
            }
        ],
        "model_name": "kollamo-muril-5class",
        "model_version": "v1",
    }

    fresh_job_service.update_job(
        job_id=job_id,
        status="COMPLETED",
        progress={"stage": "COMPLETED", "completed": 1, "total": 1, "percentage": 100},
        result=result_payload,
    )

    response = await async_client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["result"]["total_comments"] == 1
    assert data["result"]["comments"][0]["sentiment"] == "Positive"
    assert data["error"] is None


@pytest.mark.asyncio
async def test_get_analysis_job_failed(
    async_client: AsyncClient, fresh_job_service: JobStateService
) -> None:
    """Verifies polling a FAILED job returns structured error detail."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})
    fresh_job_service.update_job(
        job_id=job_id,
        status="FAILED",
        error={"code": "MODEL_NOT_READY", "message": "The sentiment model is not ready.", "details": None},
    )

    response = await async_client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "FAILED"
    assert data["error"]["code"] == "MODEL_NOT_READY"
    assert data["result"] is None


@pytest.mark.asyncio
async def test_get_analysis_job_not_found(async_client: AsyncClient) -> None:
    """Verifies that polling a non-existent job ID returns HTTP 404 JOB_NOT_FOUND."""
    random_uuid = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/analysis/jobs/{random_uuid}")
    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "JOB_NOT_FOUND"
    assert random_uuid in data["error"]["message"]
