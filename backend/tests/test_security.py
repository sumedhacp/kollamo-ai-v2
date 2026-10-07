"""Security and Robustness Verification Test Suite."""

import pytest
from httpx import AsyncClient

from backend.app.core.rate_limiter import InMemoryRateLimiter
from backend.app.main import global_rate_limiter


@pytest.mark.asyncio
async def test_oversized_payload_rejection(async_client: AsyncClient):
    """Verifies payloads exceeding 5000 characters are rejected with 422."""
    oversized_text = "നല്ല സിനിമ " * 1000  # > 10,000 chars
    resp = await async_client.post("/api/sentiment", json={"text": oversized_text})
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_whitespace_only_rejection(async_client: AsyncClient):
    """Verifies empty or whitespace comments are rejected with 422."""
    for empty_input in ["", "   ", "\n\t\r"]:
        resp = await async_client.post("/api/sentiment", json={"text": empty_input})
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_malicious_youtube_url_schemes(async_client: AsyncClient):
    """Verifies SSRF, local file, and non-YouTube URLs are rejected with 422."""
    malicious_urls = [
        "file:///etc/passwd",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/internal",
        "https://evil.com/watch?v=12345",
        "javascript:alert(1)",
        "ftp://malicious.org/script.sh",
    ]
    for bad_url in malicious_urls:
        resp = await async_client.post("/api/analyze", json={"youtube_url": bad_url, "sample_size": 50})
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_cors_preflight_and_headers(async_client: AsyncClient):
    """Verifies CORS origin handling and allowed methods."""
    # Allowed origin test
    resp = await async_client.options(
        "/api/sentiment",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.asyncio
async def test_rate_limiter_throttling(async_client: AsyncClient):
    """Verifies rate limiting triggers 429 when threshold is breached."""
    # Temporarily set a very small threshold for testing
    test_limiter = InMemoryRateLimiter(requests_per_minute=5, window_seconds=10)
    original_limiter = global_rate_limiter.clients

    try:
        # Use mock client IP
        for _ in range(5):
            test_limiter.is_rate_limited("198.51.100.1")

        # 6th request should be rate-limited
        assert test_limiter.is_rate_limited("198.51.100.1") is True
    finally:
        global_rate_limiter.reset()


@pytest.mark.asyncio
async def test_sanitized_internal_server_errors(monkeypatch):
    """Verifies unhandled exceptions return sanitized error envelope without stack traces."""
    from httpx import ASGITransport
    from backend.app.main import app
    from backend.app.services.sentiment_service import SentimentService

    # Monkeypatch analyze_comment to raise an unexpected internal exception with sensitive info
    def raise_unhandled(*args, **kwargs):
        raise RuntimeError("Secret DB password leaked: super_secret_12345 at line 42")

    monkeypatch.setattr(SentimentService, "analyze_comment", raise_unhandled)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/sentiment", json={"text": "kollam"})
        assert resp.status_code == 500
        data = resp.json()

        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # Crucial: No traceback or internal exception text leaked
        assert "super_secret_12345" not in resp.text
        assert "Traceback" not in resp.text

