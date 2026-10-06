"""Tests for Ingestion API Endpoint /api/analyze/{job_id}/ingest."""

import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from backend.app.main import app
from backend.app.services.ingestion_service import (
    IngestionService,
    get_ingestion_service,
)
from backend.app.services.youtube_client import (
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
    YouTubeVideoNotFoundError,
)


@pytest.mark.asyncio
async def test_ingest_endpoint_success(async_client: AsyncClient):
    """Verifies POST /api/analyze/{job_id}/ingest executes ingestion and returns 200."""
    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "sample_size": 50},
    )
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    mock_ingestion = AsyncMock(spec=IngestionService)
    mock_ingestion.ingest_job_comments.return_value = (None, [])
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion

    try:
        resp = await async_client.post(f"/api/analyze/{job_id}/ingest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert mock_ingestion.ingest_job_comments.called
    finally:
        app.dependency_overrides.pop(get_ingestion_service, None)


@pytest.mark.asyncio
async def test_ingest_endpoint_comments_disabled_returns_403(async_client: AsyncClient):
    """Verifies that disabled comments return 403 Forbidden with error envelope."""
    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    job_id = create_resp.json()["job_id"]

    mock_ingestion = AsyncMock(spec=IngestionService)
    mock_ingestion.ingest_job_comments.side_effect = YouTubeCommentsDisabledError("Comments disabled")
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion

    try:
        resp = await async_client.post(f"/api/analyze/{job_id}/ingest")
        assert resp.status_code == 403
        data = resp.json()
        assert "error" in data
        assert "Comments are disabled" in data["error"]["message"]
    finally:
        app.dependency_overrides.pop(get_ingestion_service, None)


@pytest.mark.asyncio
async def test_ingest_endpoint_quota_exceeded_returns_429(async_client: AsyncClient):
    """Verifies that quota exhaustion returns 429 Too Many Requests."""
    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    job_id = create_resp.json()["job_id"]

    mock_ingestion = AsyncMock(spec=IngestionService)
    mock_ingestion.ingest_job_comments.side_effect = YouTubeQuotaExceededError("Quota exceeded")
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion

    try:
        resp = await async_client.post(f"/api/analyze/{job_id}/ingest")
        assert resp.status_code == 429
        data = resp.json()
        assert "error" in data
        assert "quota exceeded" in data["error"]["message"].lower()
    finally:
        app.dependency_overrides.pop(get_ingestion_service, None)


@pytest.mark.asyncio
async def test_ingest_endpoint_video_not_found_returns_404(async_client: AsyncClient):
    """Verifies that missing or private video returns 404 Not Found."""
    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    job_id = create_resp.json()["job_id"]

    mock_ingestion = AsyncMock(spec=IngestionService)
    mock_ingestion.ingest_job_comments.side_effect = YouTubeVideoNotFoundError("Video not found")
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion

    try:
        resp = await async_client.post(f"/api/analyze/{job_id}/ingest")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert "Video was not found" in data["error"]["message"]
    finally:
        app.dependency_overrides.pop(get_ingestion_service, None)
