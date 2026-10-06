"""Tests for YouTube Data API v3 Client with Mocked Responses."""

import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from backend.app.services.youtube_client import (
    YouTubeClient,
    VideoMetadata,
    YouTubeCommentData,
    YouTubeAPIError,
    YouTubeVideoNotFoundError,
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
    YouTubeAuthError,
    YouTubeNetworkError,
)

SAMPLE_VIDEO_ID = "dQw4w9WgXcQ"


def create_mock_video_response(video_id: str = SAMPLE_VIDEO_ID) -> dict:
    """Creates a mock response for videos.list endpoint."""
    return {
        "items": [
            {
                "id": video_id,
                "snippet": {
                    "title": "Aavesham Official Trailer | Fahadh Faasil",
                    "channelTitle": "Anwar Rasheed Entertainments",
                    "publishedAt": "2024-04-10T12:00:00Z",
                },
                "statistics": {
                    "viewCount": "15420000",
                    "likeCount": "450000",
                    "commentCount": "12500",
                },
            }
        ]
    }


def create_mock_comments_response(
    count: int = 2, next_page_token: str = None
) -> dict:
    """Creates a mock response for commentThreads.list endpoint."""
    items = []
    for i in range(count):
        items.append({
            "id": f"comment_{i}",
            "snippet": {
                "topLevelComment": {
                    "id": f"comment_{i}",
                    "snippet": {
                        "textOriginal": f"Sample comment {i} kidilan aayi",
                        "authorDisplayName": f"Viewer {i}",
                        "likeCount": i * 10,
                        "publishedAt": f"2024-04-11T1{i}:00:00Z",
                    },
                },
                "totalReplyCount": i,
            },
        })

    resp = {"items": items}
    if next_page_token:
        resp["nextPageToken"] = next_page_token
    return resp


@pytest.mark.asyncio
async def test_missing_api_key_raises_auth_error():
    """Client raises YouTubeAuthError when API key is completely absent."""
    client = YouTubeClient(api_key="")
    with pytest.raises(YouTubeAuthError) as exc_info:
        await client.fetch_video_metadata(SAMPLE_VIDEO_ID)
    assert "YouTube API key is not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_video_metadata_success():
    """Client parses and returns video metadata correctly."""
    mock_data = create_mock_video_response()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(200, json=mock_data, request=httpx.Request("GET", "https://api.test"))
    mock_client.get.return_value = mock_resp

    yt = YouTubeClient(api_key="test_key", http_client=mock_client)
    metadata = await yt.fetch_video_metadata(SAMPLE_VIDEO_ID)

    assert metadata.video_id == SAMPLE_VIDEO_ID
    assert "Aavesham" in metadata.title
    assert metadata.channel_title == "Anwar Rasheed Entertainments"
    assert metadata.view_count == 15420000
    assert metadata.comment_count == 12500


@pytest.mark.asyncio
async def test_fetch_video_metadata_not_found():
    """Client raises YouTubeVideoNotFoundError when video is missing or private."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(200, json={"items": []}, request=httpx.Request("GET", "https://api.test"))
    mock_client.get.return_value = mock_resp

    yt = YouTubeClient(api_key="test_key", http_client=mock_client)
    with pytest.raises(YouTubeVideoNotFoundError):
        await yt.fetch_video_metadata("nonexistent_id")


@pytest.mark.asyncio
async def test_fetch_comments_pagination():
    """Client follows nextPageToken across multiple pages to collect requested comments."""
    page1 = create_mock_comments_response(count=2, next_page_token="TOKEN_PAGE_2")
    page2 = create_mock_comments_response(count=2, next_page_token=None)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    resp1 = httpx.Response(200, json=page1, request=httpx.Request("GET", "https://api.test"))
    resp2 = httpx.Response(200, json=page2, request=httpx.Request("GET", "https://api.test"))
    mock_client.get.side_effect = [resp1, resp2]

    yt = YouTubeClient(api_key="test_key", http_client=mock_client)
    comments = await yt.fetch_comments(SAMPLE_VIDEO_ID, sample_size=4, sort_mode="top")

    assert len(comments) == 4
    assert mock_client.get.call_count == 2


@pytest.mark.asyncio
async def test_fetch_comments_sample_size_cutoff():
    """Client stops requesting once sample_size threshold is reached."""
    page1 = create_mock_comments_response(count=5, next_page_token="MORE_AVAILABLE")

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    resp1 = httpx.Response(200, json=page1, request=httpx.Request("GET", "https://api.test"))
    mock_client.get.return_value = resp1

    yt = YouTubeClient(api_key="test_key", http_client=mock_client)
    comments = await yt.fetch_comments(SAMPLE_VIDEO_ID, sample_size=3, sort_mode="newest")

    assert len(comments) == 3
    assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_fetch_comments_disabled_error():
    """Client raises YouTubeCommentsDisabledError on 403 commentsDisabled reason."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    err_body = {
        "error": {
            "code": 403,
            "message": "The video has disabled comments.",
            "errors": [{"reason": "commentsDisabled"}],
        }
    }
    mock_resp = httpx.Response(403, json=err_body, request=httpx.Request("GET", "https://api.test"))
    mock_client.get.return_value = mock_resp

    yt = YouTubeClient(api_key="test_key", http_client=mock_client)
    with pytest.raises(YouTubeCommentsDisabledError):
        await yt.fetch_comments(SAMPLE_VIDEO_ID)


@pytest.mark.asyncio
async def test_fetch_comments_quota_exceeded_error():
    """Client raises YouTubeQuotaExceededError on 403 quotaExceeded reason."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    err_body = {
        "error": {
            "code": 403,
            "message": "Quota exceeded",
            "errors": [{"reason": "quotaExceeded"}],
        }
    }
    mock_resp = httpx.Response(403, json=err_body, request=httpx.Request("GET", "https://api.test"))
    mock_client.get.return_value = mock_resp

    yt = YouTubeClient(api_key="test_key", http_client=mock_client)
    with pytest.raises(YouTubeQuotaExceededError):
        await yt.fetch_comments(SAMPLE_VIDEO_ID)


@pytest.mark.asyncio
async def test_fetch_comments_bad_api_key_error():
    """Client raises YouTubeAuthError when API key is rejected by Google."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    err_body = {
        "error": {
            "code": 400,
            "message": "API key not valid",
            "errors": [{"reason": "keyInvalid"}],
        }
    }
    mock_resp = httpx.Response(400, json=err_body, request=httpx.Request("GET", "https://api.test"))
    mock_client.get.return_value = mock_resp

    yt = YouTubeClient(api_key="bad_key", http_client=mock_client)
    with pytest.raises(YouTubeAuthError):
        await yt.fetch_comments(SAMPLE_VIDEO_ID)


@pytest.mark.asyncio
async def test_retry_on_transient_error():
    """Client retries transient 500 server errors and succeeds if next attempt works."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    err_resp = httpx.Response(503, text="Service Unavailable", request=httpx.Request("GET", "https://api.test"))
    ok_resp = httpx.Response(200, json=create_mock_video_response(), request=httpx.Request("GET", "https://api.test"))
    mock_client.get.side_effect = [err_resp, ok_resp]

    with patch("asyncio.sleep", return_value=None):  # Fast forward sleep
        yt = YouTubeClient(api_key="test_key", http_client=mock_client, max_retries=2)
        metadata = await yt.fetch_video_metadata(SAMPLE_VIDEO_ID)

    assert metadata.video_id == SAMPLE_VIDEO_ID
    assert mock_client.get.call_count == 2
