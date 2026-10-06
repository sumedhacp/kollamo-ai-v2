"""Official YouTube Data API v3 Asynchronous Client."""

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger

YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

# Supported sort modes mapped to YouTube API parameter
SORT_MODE_MAPPING = {
    "top": "relevance",
    "newest": "time",
    "oldest": "time",  # YouTube API orders newest-first; oldest will be reversed locally
}


class YouTubeAPIError(Exception):
    """Base exception for YouTube Data API interactions."""

    def __init__(self, message: str, status_code: Optional[int] = None, reason: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.reason = reason


class YouTubeVideoNotFoundError(YouTubeAPIError):
    """Raised when the video ID does not exist or the video is private."""
    pass


class YouTubeCommentsDisabledError(YouTubeAPIError):
    """Raised when comments are disabled on the requested video."""
    pass


class YouTubeQuotaExceededError(YouTubeAPIError):
    """Raised when YouTube Data API quota has been exhausted."""
    pass


class YouTubeAuthError(YouTubeAPIError):
    """Raised when API key is missing or invalid."""
    pass


class YouTubeNetworkError(YouTubeAPIError):
    """Raised on network failures or transient errors."""
    pass


@dataclass
class VideoMetadata:
    """Metadata container for a YouTube video."""

    video_id: str
    title: str
    channel_title: str
    published_at: Optional[datetime]
    view_count: int
    like_count: int
    comment_count: int


@dataclass
class YouTubeCommentData:
    """Standardized representation of a single YouTube comment."""

    comment_id: str
    video_id: str
    original_text: str
    author_display_name: str
    like_count: int
    reply_count: int
    published_at: Optional[datetime]


class YouTubeClient:
    """Asynchronous client for YouTube Data API v3 with robust pagination and error handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 15.0,
        max_retries: int = 3,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.timeout = timeout
        self.max_retries = max_retries
        self._custom_client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns existing client or creates a temporary one."""
        if self._custom_client is not None:
            return self._custom_client
        return httpx.AsyncClient(timeout=self.timeout)

    async def _execute_with_retry(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes GET request against YouTube Data API with exponential backoff and jitter."""
        if not self.api_key:
            raise YouTubeAuthError(
                "YouTube API key is not configured. Please provide YOUTUBE_API_KEY.",
                status_code=401,
                reason="keyMissing",
            )

        full_params = {**params, "key": self.api_key}
        url = f"{YOUTUBE_API_BASE_URL}/{endpoint}"
        client_created = self._custom_client is None
        client = await self._get_client()

        try:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.get(url, params=full_params)

                    if response.status_code == 200:
                        return response.json()

                    # Handle API error payloads
                    error_json = {}
                    try:
                        error_json = response.json().get("error", {})
                    except Exception:
                        pass

                    errors = error_json.get("errors", [])
                    reason = errors[0].get("reason", "") if errors else ""
                    message = error_json.get("message", response.text)

                    # Quota exhaustion
                    if response.status_code == 403 and reason in (
                        "quotaExceeded",
                        "dailyLimitExceeded",
                        "rateLimitExceeded",
                    ):
                        raise YouTubeQuotaExceededError(
                            "YouTube Data API daily quota exceeded. Please try again tomorrow.",
                            status_code=403,
                            reason=reason,
                        )

                    # Comments disabled
                    if response.status_code == 403 and reason == "commentsDisabled":
                        raise YouTubeCommentsDisabledError(
                            "Comments are disabled on this video.",
                            status_code=403,
                            reason="commentsDisabled",
                        )

                    # Bad API Key
                    if response.status_code in (400, 403) and reason in (
                        "keyInvalid",
                        "forbidden",
                        "API_KEY_INVALID",
                    ):
                        raise YouTubeAuthError(
                            f"YouTube API key authentication failed: {message}",
                            status_code=response.status_code,
                            reason=reason,
                        )

                    # Video not found
                    if response.status_code == 404:
                        raise YouTubeVideoNotFoundError(
                            f"Video was not found: {message}",
                            status_code=404,
                            reason="videoNotFound",
                        )

                    # Transient server error on YouTube side (500, 502, 503, 504)
                    if response.status_code in (500, 502, 503, 504) and attempt < self.max_retries:
                        backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
                        logger.warning(
                            f"YouTube API returned status {response.status_code}. Retrying in {backoff:.2f}s..."
                        )
                        await asyncio.sleep(backoff)
                        continue

                    # Unhandled API error
                    raise YouTubeAPIError(
                        f"YouTube Data API error ({response.status_code}): {message}",
                        status_code=response.status_code,
                        reason=reason,
                    )

                except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as net_err:
                    if attempt < self.max_retries:
                        backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
                        logger.warning(f"Network error communicating with YouTube API: {net_err}. Retrying in {backoff:.2f}s...")
                        await asyncio.sleep(backoff)
                        continue
                    raise YouTubeNetworkError(f"Failed to communicate with YouTube API after {self.max_retries} attempts: {net_err}")

        finally:
            if client_created:
                await client.aclose()

        raise YouTubeAPIError("Maximum retries exhausted without response.")

    async def fetch_video_metadata(self, video_id: str) -> VideoMetadata:
        """Fetches metadata, title, channel, views, and statistics for a YouTube video."""
        params = {
            "part": "snippet,statistics",
            "id": video_id,
        }
        data = await self._execute_with_retry("videos", params)
        items = data.get("items", [])
        if not items:
            raise YouTubeVideoNotFoundError(
                f"Video with ID '{video_id}' was not found or is private.",
                status_code=404,
                reason="videoNotFound",
            )

        item = items[0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        published_at_str = snippet.get("publishedAt")
        published_at: Optional[datetime] = None
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        return VideoMetadata(
            video_id=video_id,
            title=snippet.get("title", f"YouTube Video ({video_id})"),
            channel_title=snippet.get("channelTitle", "Unknown Channel"),
            published_at=published_at,
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
        )

    async def fetch_comments(
        self,
        video_id: str,
        sample_size: Optional[int] = 250,
        sort_mode: str = "top",
    ) -> List[YouTubeCommentData]:
        """Fetches top-level comments up to sample_size using robust pagination."""
        api_order = SORT_MODE_MAPPING.get(sort_mode.lower(), "relevance")
        max_comments = None if (sample_size in (None, 0, -1)) else sample_size

        comments: List[YouTubeCommentData] = []
        page_token: Optional[str] = None

        while True:
            # Calculate next batch size (up to 100 per page as allowed by YouTube API)
            remaining = 100
            if max_comments is not None:
                remaining = max_comments - len(comments)
                if remaining <= 0:
                    break

            per_page = min(remaining, 100)
            params: Dict[str, Any] = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": per_page,
                "order": api_order,
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token

            data = await self._execute_with_retry("commentThreads", params)
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                top_level = item.get("snippet", {}).get("topLevelComment", {})
                snippet = top_level.get("snippet", {})
                text = snippet.get("textOriginal") or snippet.get("textDisplay") or ""

                pub_str = snippet.get("publishedAt")
                pub_date: Optional[datetime] = None
                if pub_str:
                    try:
                        pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                comments.append(
                    YouTubeCommentData(
                        comment_id=item.get("id", str(len(comments))),
                        video_id=video_id,
                        original_text=text,
                        author_display_name=snippet.get("authorDisplayName", "Anonymous"),
                        like_count=int(snippet.get("likeCount", 0)),
                        reply_count=int(item.get("snippet", {}).get("totalReplyCount", 0)),
                        published_at=pub_date,
                    )
                )

                if max_comments is not None and len(comments) >= max_comments:
                    break

            page_token = data.get("nextPageToken")
            if not page_token:
                # No more pages returned by YouTube
                break

        # If oldest sort was requested, reverse or sort by published date
        if sort_mode.lower() == "oldest":
            comments.sort(
                key=lambda c: c.published_at or datetime.min,
                reverse=False,
            )

        logger.info(
            f"Successfully fetched {len(comments)} comments for video {video_id} (requested={sample_size}, mode={sort_mode})"
        )
        return comments
