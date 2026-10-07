"""Deterministic Unit Tests for YouTube API Client using Mocked HTTP Transport (Section 36)."""

import pytest
import httpx
from datetime import datetime, timezone
from app.services.youtube.client import YouTubeClient
from app.services.youtube.errors import (
    YouTubeConfigError,
    YouTubeVideoNotFoundError,
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
    YouTubeAPIError,
)


@pytest.mark.asyncio
async def test_client_missing_api_key_raises_config_error():
    """Client raises YouTubeConfigError if API key is empty."""
    client = YouTubeClient(api_key="")
    with pytest.raises(YouTubeConfigError) as exc_info:
        await client.fetch_video_metadata("dQw4w9WgXcQ")
    assert "YOUTUBE_CONFIG_ERROR" == exc_info.value.code


@pytest.mark.asyncio
async def test_client_fetch_video_metadata_success():
    """Client parses video metadata accurately from mock YouTube API response."""
    mock_payload = {
        "items": [
            {
                "id": "dQw4w9WgXcQ",
                "snippet": {
                    "title": "Rick Astley - Never Gonna Give You Up",
                    "channelTitle": "RickAstleyVEVO",
                    "publishedAt": "2009-10-25T06:57:33Z",
                    "description": "The official video for Never Gonna Give You Up",
                },
                "statistics": {
                    "viewCount": "1500000000",
                    "likeCount": "17000000",
                    "commentCount": "2500000",
                },
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert "videos" in request.url.path
        assert request.url.params["id"] == "dQw4w9WgXcQ"
        assert request.url.params["key"] == "test-key"
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = YouTubeClient(api_key="test-key", http_client=mock_http)
        metadata = await client.fetch_video_metadata("dQw4w9WgXcQ")

        assert metadata.video_id == "dQw4w9WgXcQ"
        assert metadata.title == "Rick Astley - Never Gonna Give You Up"
        assert metadata.channel_title == "RickAstleyVEVO"
        assert metadata.view_count == 1500000000
        assert metadata.like_count == 17000000
        assert metadata.comment_count == 2500000
        assert metadata.published_at is not None
        assert metadata.published_at.year == 2009


@pytest.mark.asyncio
async def test_client_fetch_video_metadata_not_found():
    """Client raises YouTubeVideoNotFoundError when items list is empty or 404."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = YouTubeClient(api_key="test-key", http_client=mock_http)
        with pytest.raises(YouTubeVideoNotFoundError):
            await client.fetch_video_metadata("dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_client_fetch_comment_threads_success():
    """Client fetches a single page of comment threads and parses attributes."""
    mock_payload = {
        "items": [
            {
                "id": "comment_1",
                "snippet": {
                    "topLevelComment": {
                        "id": "comment_1",
                        "snippet": {
                            "authorDisplayName": "Malayalam Fan",
                            "textOriginal": "ഈ സിനിമ വളരെ മികച്ചതാണ് ❤️",
                            "publishedAt": "2024-05-01T12:00:00Z",
                            "updatedAt": "2024-05-01T12:00:00Z",
                            "likeCount": 42,
                        },
                    }
                },
            }
        ],
        "nextPageToken": "token_page_2",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert "commentThreads" in request.url.path
        assert request.url.params["videoId"] == "dQw4w9WgXcQ"
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = YouTubeClient(api_key="test-key", http_client=mock_http)
        result = await client.fetch_comment_threads("dQw4w9WgXcQ", max_results=50)

        assert len(result["items"]) == 1
        assert result["nextPageToken"] == "token_page_2"

        comment = client.parse_comment_item(result["items"][0], "dQw4w9WgXcQ")
        assert comment.comment_id == "comment_1"
        assert comment.author_name == "Malayalam Fan"
        assert comment.text == "ഈ സിനിമ വളരെ മികച്ചതാണ് ❤️"
        assert comment.like_count == 42
        assert comment.published_at is not None


@pytest.mark.asyncio
async def test_client_comments_disabled_error():
    """Client maps 403 commentsDisabled to YouTubeCommentsDisabledError."""
    mock_error = {
        "error": {
            "errors": [{"reason": "commentsDisabled"}],
            "message": "The video identified by the <code><var>videoId</var></code> parameter has disabled comments.",
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json=mock_error)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = YouTubeClient(api_key="test-key", http_client=mock_http)
        with pytest.raises(YouTubeCommentsDisabledError):
            await client.fetch_comment_threads("dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_client_quota_exceeded_error():
    """Client maps 403 quotaExceeded to YouTubeQuotaExceededError."""
    mock_error = {
        "error": {
            "errors": [{"reason": "quotaExceeded"}],
            "message": "The request cannot be completed because you have exceeded your quota.",
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json=mock_error)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = YouTubeClient(api_key="test-key", http_client=mock_http)
        with pytest.raises(YouTubeQuotaExceededError):
            await client.fetch_comment_threads("dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_client_invalid_api_key_error():
    """Client maps 400 keyInvalid to YouTubeConfigError."""
    mock_error = {
        "error": {
            "errors": [{"reason": "keyInvalid"}],
            "message": "API key not valid. Please pass a valid API key.",
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json=mock_error)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = YouTubeClient(api_key="bad-key", http_client=mock_http)
        with pytest.raises(YouTubeConfigError):
            await client.fetch_comment_threads("dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_client_network_timeout_error():
    """Client maps network timeout to YouTubeAPIError."""
    def handler(request: httpx.Request):
        raise httpx.ReadTimeout("Connection timed out")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = YouTubeClient(api_key="test-key", http_client=mock_http)
        with pytest.raises(YouTubeAPIError):
            await client.fetch_comment_threads("dQw4w9WgXcQ")
