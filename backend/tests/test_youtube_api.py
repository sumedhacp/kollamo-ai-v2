import pytest
from httpx import AsyncClient
from backend.app.main import app
from app.schemas.youtube import YouTubeIngestionResult, YouTubeVideo, YouTubeComment
from app.api.routes.youtube import get_youtube_service
from app.services.youtube.service import YouTubeIngestionService
from app.services.youtube.errors import (
    YouTubeConfigError,
    YouTubeInvalidVideoError,
    YouTubeVideoNotFoundError,
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
    YouTubeAPIError,
)


class MockService:
    """Mock ingestion service for API route tests."""

    def __init__(self, failure_exc: Exception | None = None):
        self.failure_exc = failure_exc

    async def ingest(self, video_url: str, comment_limit=100, sort_by="newest"):
        if self.failure_exc:
            raise self.failure_exc

        return YouTubeIngestionResult(
            video=YouTubeVideo(
                video_id="dQw4w9WgXcQ",
                title="Mock Test Video",
                channel_title="Mock Channel",
                view_count=1000,
                like_count=50,
                comment_count=5,
            ),
            comments=[
                YouTubeComment(
                    comment_id="c_1",
                    video_id="dQw4w9WgXcQ",
                    author_name="User 1",
                    text="Super movie! ഇത് ഗംഭീരം ❤️",
                    like_count=10,
                )
            ],
            requested_limit=comment_limit,
            returned_count=1,
            sort_by=sort_by,
        )


@pytest.mark.asyncio
async def test_youtube_ingest_success(async_client: AsyncClient):
    """POST /api/v1/youtube/ingest returns 200 with normalized video and comment data."""
    app.dependency_overrides[get_youtube_service] = lambda: MockService()
    try:
        payload = {
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "comment_limit": 50,
            "sort_by": "most_liked",
        }
        response = await async_client.post("/api/v1/youtube/ingest", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "video" in data
        assert data["video"]["video_id"] == "dQw4w9WgXcQ"
        assert data["video"]["title"] == "Mock Test Video"

        assert "comments" in data
        assert len(data["comments"]) == 1
        assert data["comments"][0]["text"] == "Super movie! ഇത് ഗംഭീരം ❤️"

        assert data["requested_limit"] == 50
        assert data["returned_count"] == 1
        assert data["sort_by"] == "most_liked"
    finally:
        app.dependency_overrides.pop(get_youtube_service, None)


@pytest.mark.asyncio
async def test_youtube_ingest_invalid_url_returns_400(async_client: AsyncClient):
    """Invalid video URL returns HTTP 400 YOUTUBE_INVALID_VIDEO."""
    app.dependency_overrides[get_youtube_service] = lambda: MockService(
        failure_exc=YouTubeInvalidVideoError("Unsupported domain 'google.com'. Expected a valid YouTube URL.")
    )
    try:
        payload = {"video_url": "https://www.google.com"}
        response = await async_client.post("/api/v1/youtube/ingest", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "YOUTUBE_INVALID_VIDEO"
    finally:
        app.dependency_overrides.pop(get_youtube_service, None)


@pytest.mark.asyncio
async def test_youtube_ingest_video_not_found_returns_404(async_client: AsyncClient):
    """Missing or private video returns HTTP 404 YOUTUBE_VIDEO_NOT_FOUND."""
    app.dependency_overrides[get_youtube_service] = lambda: MockService(
        failure_exc=YouTubeVideoNotFoundError("The requested YouTube video was not found or is private.")
    )
    try:
        payload = {"video_url": "https://youtu.be/dQw4w9WgXcQ"}
        response = await async_client.post("/api/v1/youtube/ingest", json=payload)
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "YOUTUBE_VIDEO_NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_youtube_service, None)


@pytest.mark.asyncio
async def test_youtube_ingest_comments_disabled_returns_422(async_client: AsyncClient):
    """Comments disabled returns HTTP 422 YOUTUBE_COMMENTS_DISABLED."""
    app.dependency_overrides[get_youtube_service] = lambda: MockService(
        failure_exc=YouTubeCommentsDisabledError("Comments are disabled on this YouTube video.")
    )
    try:
        payload = {"video_url": "https://youtu.be/dQw4w9WgXcQ"}
        response = await async_client.post("/api/v1/youtube/ingest", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "YOUTUBE_COMMENTS_DISABLED"
    finally:
        app.dependency_overrides.pop(get_youtube_service, None)


@pytest.mark.asyncio
async def test_youtube_ingest_quota_exceeded_returns_429(async_client: AsyncClient):
    """Exceeded API quota returns HTTP 429 YOUTUBE_QUOTA_EXCEEDED."""
    app.dependency_overrides[get_youtube_service] = lambda: MockService(
        failure_exc=YouTubeQuotaExceededError("YouTube Data API daily quota has been exceeded.")
    )
    try:
        payload = {"video_url": "https://youtu.be/dQw4w9WgXcQ"}
        response = await async_client.post("/api/v1/youtube/ingest", json=payload)
        assert response.status_code == 429
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "YOUTUBE_QUOTA_EXCEEDED"
    finally:
        app.dependency_overrides.pop(get_youtube_service, None)


@pytest.mark.asyncio
async def test_youtube_ingest_missing_config_returns_503(async_client: AsyncClient):
    """Missing API key returns HTTP 503 YOUTUBE_CONFIG_ERROR."""
    app.dependency_overrides[get_youtube_service] = lambda: MockService(
        failure_exc=YouTubeConfigError("YouTube API key is not configured.")
    )
    try:
        payload = {"video_url": "https://youtu.be/dQw4w9WgXcQ"}
        response = await async_client.post("/api/v1/youtube/ingest", json=payload)
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "YOUTUBE_CONFIG_ERROR"
    finally:
        app.dependency_overrides.pop(get_youtube_service, None)


@pytest.mark.asyncio
async def test_youtube_ingest_upstream_error_returns_502(async_client: AsyncClient):
    """Upstream API failure returns HTTP 502 YOUTUBE_API_ERROR."""
    app.dependency_overrides[get_youtube_service] = lambda: MockService(
        failure_exc=YouTubeAPIError("YouTube Data API communication error.", status_code=502)
    )
    try:
        payload = {"video_url": "https://youtu.be/dQw4w9WgXcQ"}
        response = await async_client.post("/api/v1/youtube/ingest", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "YOUTUBE_API_ERROR"
    finally:
        app.dependency_overrides.pop(get_youtube_service, None)


@pytest.mark.asyncio
async def test_youtube_ingest_validation_error_on_invalid_limit(async_client: AsyncClient):
    """Invalid comment_limit returns HTTP 422 VALIDATION_ERROR."""
    payload = {
        "video_url": "https://youtu.be/dQw4w9WgXcQ",
        "comment_limit": 9999,  # Unsupported limit
    }
    response = await async_client.post("/api/v1/youtube/ingest", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_youtube_ingest_validation_error_on_missing_url(async_client: AsyncClient):
    """Missing video_url field returns HTTP 422 VALIDATION_ERROR with REQUIRED field code."""
    payload = {}
    response = await async_client.post("/api/v1/youtube/ingest", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["details"]["fields"][0]["code"] == "REQUIRED"


@pytest.mark.asyncio
async def test_openapi_includes_youtube_endpoint(async_client: AsyncClient):
    """OpenAPI schema exposes /api/v1/youtube/ingest with documented response codes (Section 42)."""
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()

    paths = data.get("paths", {})
    assert "/api/v1/youtube/ingest" in paths

    post_op = paths["/api/v1/youtube/ingest"].get("post", {})
    responses = post_op.get("responses", {})

    assert "200" in responses
    assert "400" in responses
    assert "404" in responses
    assert "422" in responses
    assert "429" in responses
    assert "502" in responses
    assert "503" in responses
    assert "500" in responses
