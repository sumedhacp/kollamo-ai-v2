"""Tests for YouTube Ingestion and Batch Analysis Endpoints."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_analysis_job_success(async_client: AsyncClient) -> None:
    """Verifies valid YouTube URL triggers 202 Accepted and returns queued job_id."""
    payload = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "sample_size": 250,
        "sort_mode": "top",
    }
    response = await async_client.post("/api/analyze", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "job_id" in data
    assert data["status"] == "queued"
    assert "Analysis job queued successfully" in data["message"]
    assert "created_at" in data

    # Verify UUID format
    job_uuid = uuid.UUID(data["job_id"])
    assert str(job_uuid) == data["job_id"]


@pytest.mark.asyncio
async def test_create_analysis_job_invalid_url(async_client: AsyncClient) -> None:
    """Verifies that non-YouTube or malformed URL is rejected with 422."""
    payload = {
        "youtube_url": "https://example.com/not-youtube",
        "sample_size": 250,
        "sort_mode": "top",
    }
    response = await async_client.post("/api/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_analysis_job_invalid_sample_size(async_client: AsyncClient) -> None:
    """Verifies that unsupported sample size is rejected with 422."""
    payload = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "sample_size": 999,  # Only 50, 100, 250, 500, "all" allowed
        "sort_mode": "top",
    }
    response = await async_client.post("/api/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_get_analysis_job_status_existing(async_client: AsyncClient) -> None:
    """Verifies created job can be retrieved via GET /api/analyze/{job_id}."""
    create_payload = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "sample_size": 100,
        "sort_mode": "top",
    }
    create_resp = await async_client.post("/api/analyze", json=create_payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    # Query status
    status_resp = await async_client.get(f"/api/analyze/{job_id}")
    assert status_resp.status_code == 200
    job_data = status_resp.json()

    assert job_data["job_id"] == job_id
    assert job_data["status"] == "queued"
    assert job_data["progress"] == 0.0
    assert job_data["processed_comments"] == 0
    assert "video" in job_data
    assert job_data["video"]["video_id"] == "dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_get_analysis_job_not_found(async_client: AsyncClient) -> None:
    """Verifies 404 is returned for a non-existent job UUID."""
    random_uuid = str(uuid.uuid4())
    response = await async_client.get(f"/api/analyze/{random_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"


@pytest.mark.asyncio
async def test_get_analysis_job_invalid_uuid(async_client: AsyncClient) -> None:
    """Verifies 422 is returned for invalid UUID format in path."""
    response = await async_client.get("/api/analyze/invalid-uuid-string")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"


@pytest.mark.asyncio
async def test_process_job_pipeline_endpoint(async_client: AsyncClient) -> None:
    """Verifies POST /api/analyze/{job_id}/process executes pipeline and returns status."""
    from unittest.mock import AsyncMock, patch

    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "sample_size": 50},
    )
    job_id = create_resp.json()["job_id"]

    with patch("backend.app.workers.tasks.run_analysis_pipeline", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = {"status": "completed"}
        proc_resp = await async_client.post(f"/api/analyze/{job_id}/process")
        assert proc_resp.status_code == 200
        assert mock_pipeline.called
