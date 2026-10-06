"""Tests for Health and Root Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Verifies root endpoint returns 200 with platform metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "Kollamo.ai"
    assert "version" in data
    assert data["status"] == "online"
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient) -> None:
    """Verifies GET /api/health returns 200 and structured services status."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "timestamp" in data
    assert "services" in data

    services = data["services"]
    assert "database" in services
    assert "redis" in services
    assert "ml_engine" in services
    assert services["ml_engine"] == "loaded"
