"""Tests for FastAPI Application Startup, Root, Minimal Health, and OpenAPI Documentation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_app_root_endpoint(async_client: AsyncClient) -> None:
    """Verifies that the root endpoint returns 200 with platform metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "Kollamo.ai"
    assert "version" in data
    assert data["status"] == "online"
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_app_minimal_health_endpoint(async_client: AsyncClient) -> None:
    """Verifies that GET /health exactly satisfies Section 21 HealthResponse {"status": "ok"}."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_app_openapi_specification(async_client: AsyncClient) -> None:
    """Verifies that the OpenAPI JSON specification is generated and exposes key schemas."""
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"].startswith("3.")
    assert "info" in data
    assert "paths" in data

    paths = data["paths"]
    # Check that root health and versioned sentiment endpoints are documented
    assert "/health" in paths
    assert "/api/v1/sentiment" in paths


@pytest.mark.asyncio
async def test_app_docs_endpoint(async_client: AsyncClient) -> None:
    """Verifies that Swagger UI documentation is available at /docs."""
    response = await async_client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower() or "html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_app_cors_headers(async_client: AsyncClient) -> None:
    """Verifies that CORS headers are appropriately applied."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    response = await async_client.options("/api/v1/sentiment", headers=headers)
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
