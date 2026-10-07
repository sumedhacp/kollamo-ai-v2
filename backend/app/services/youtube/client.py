"""Official YouTube Data API v3 Client."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

try:
    from app.core.config import settings
    from app.core.logging import logger
    from app.schemas.youtube import YouTubeComment, YouTubeVideo
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logging import logger
    from backend.app.schemas.youtube import YouTubeComment, YouTubeVideo

from .errors import (
    YouTubeAPIError,
    YouTubeCommentsDisabledError,
    YouTubeConfigError,
    YouTubeQuotaExceededError,
    YouTubeVideoNotFoundError,
)

YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeClient:
    """Asynchronous client interacting with the official YouTube Data API v3."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or getattr(settings, "YOUTUBE_API_KEY", "")
        self.timeout = timeout
        self._custom_client = http_client

    def _ensure_api_key(self) -> str:
        """Validates that a YouTube API key is present without logging or exposing it."""
        if not self.api_key or not self.api_key.strip():
            raise YouTubeConfigError(
                "YouTube API key is not configured. Please set YOUTUBE_API_KEY in the server environment."
            )
        return self.api_key.strip()

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns the configured custom HTTP client or a new asynchronous client."""
        if self._custom_client is not None:
            return self._custom_client
        return httpx.AsyncClient(timeout=self.timeout)

    async def _request(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes a GET request against the YouTube Data API v3 with error mapping."""
        key = self._ensure_api_key()
        full_params = {**params, "key": key}
        url = f"{YOUTUBE_API_BASE_URL}/{endpoint}"

        client_created = self._custom_client is None
        client = await self._get_client()

        try:
            response = await client.get(url, params=full_params)

            if response.status_code == 200:
                return response.json()

            # Inspect error payload safely
            error_data = {}
            try:
                error_data = response.json().get("error", {})
            except Exception:
                pass

            errors_list = error_data.get("errors", [])
            reason = errors_list[0].get("reason", "") if errors_list else ""
            status_code = response.status_code

            # Handle quota exceeded
            if status_code == 403 and reason in (
                "quotaExceeded",
                "dailyLimitExceeded",
                "rateLimitExceeded",
            ):
                logger.warning("YouTube Data API quota exceeded.")
                raise YouTubeQuotaExceededError(
                    "YouTube Data API daily quota has been exceeded. Please try again later."
                )

            # Handle comments disabled
            if status_code == 403 and reason == "commentsDisabled":
                logger.info("Comments are disabled on the requested YouTube video.")
                raise YouTubeCommentsDisabledError(
                    "Comments are disabled on this YouTube video."
                )

            # Handle invalid API key
            if status_code in (400, 403) and reason in (
                "keyInvalid",
                "API_KEY_INVALID",
                "badRequest",
            ):
                logger.error("YouTube API key authentication failed.")
                raise YouTubeConfigError(
                    "Invalid YouTube API key configuration. Please check your YOUTUBE_API_KEY."
                )

            # Handle video not found
            if status_code == 404:
                raise YouTubeVideoNotFoundError(
                    "The requested YouTube video was not found or is private."
                )

            # General upstream error
            logger.error(
                f"YouTube Data API error: HTTP {status_code}, reason={reason}"
            )
            raise YouTubeAPIError(
                f"YouTube Data API error ({status_code}). Please try again later.",
                status_code=502,
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as net_err:
            logger.error(f"Network error communicating with YouTube Data API: {net_err}")
            raise YouTubeAPIError(
                "Failed to communicate with YouTube Data API due to a network timeout or connection error.",
                status_code=502,
            ) from net_err

        finally:
            if client_created:
                await client.aclose()

    async def fetch_video_metadata(self, video_id: str) -> YouTubeVideo:
        """Fetches metadata for a single YouTube video.

        Args:
            video_id: Canonical 11-character video ID.

        Returns:
            Normalized YouTubeVideo model.

        Raises:
            YouTubeVideoNotFoundError: If the video does not exist or is private.
            YouTubeQuotaExceededError: If quota is exceeded.
            YouTubeConfigError: If API key is invalid or missing.
            YouTubeAPIError: On other API communication failures.
        """
        params = {
            "part": "snippet,statistics",
            "id": video_id,
        }
        data = await self._request("videos", params)
        items = data.get("items", [])
        if not items:
            raise YouTubeVideoNotFoundError(
                f"The requested YouTube video with ID '{video_id}' was not found or is private."
            )

        item = items[0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        published_at: Optional[datetime] = None
        pub_str = snippet.get("publishedAt")
        if pub_str:
            try:
                published_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        def _safe_int(val: Any) -> Optional[int]:
            try:
                return int(val) if val is not None else None
            except (ValueError, TypeError):
                return None

        return YouTubeVideo(
            video_id=video_id,
            title=snippet.get("title", f"YouTube Video ({video_id})"),
            channel_title=snippet.get("channelTitle"),
            published_at=published_at,
            description=snippet.get("description"),
            view_count=_safe_int(statistics.get("viewCount")),
            like_count=_safe_int(statistics.get("likeCount")),
            comment_count=_safe_int(statistics.get("commentCount")),
        )

    async def fetch_comment_threads(
        self,
        video_id: str,
        max_results: int = 100,
        page_token: Optional[str] = None,
        order: str = "time",
    ) -> Dict[str, Any]:
        """Fetches a single page of comment threads from YouTube Data API v3.

        Args:
            video_id: Canonical video ID.
            max_results: Page size (between 1 and 100).
            page_token: Pagination token from previous response.
            order: YouTube order parameter ('time' or 'relevance').

        Returns:
            Dictionary containing 'items' and optional 'nextPageToken'.
        """
        params: Dict[str, Any] = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(max(max_results, 1), 100),
            "order": order,
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        return await self._request("commentThreads", params)

    def parse_comment_item(
        self, item: Dict[str, Any], video_id: str
    ) -> YouTubeComment:
        """Parses a raw YouTube commentThread resource into a normalized YouTubeComment.

        CRITICAL: Preserves raw original text verbatim without stripping or normalizing Malayalam/emojis.
        """
        snippet = item.get("snippet", {})
        top_level = snippet.get("topLevelComment", {})
        top_snippet = top_level.get("snippet", {})

        # Extract text: prioritize textOriginal then textDisplay
        text = top_snippet.get("textOriginal")
        if text is None:
            text = top_snippet.get("textDisplay", "")

        comment_id = item.get("id") or top_level.get("id") or "unknown_id"
        author_name = top_snippet.get("authorDisplayName")

        published_at: Optional[datetime] = None
        pub_str = top_snippet.get("publishedAt")
        if pub_str:
            try:
                published_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        updated_at: Optional[datetime] = None
        upd_str = top_snippet.get("updatedAt")
        if upd_str:
            try:
                updated_at = datetime.fromisoformat(upd_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        like_count = 0
        try:
            like_count = int(top_snippet.get("likeCount", 0))
        except (ValueError, TypeError):
            pass

        return YouTubeComment(
            comment_id=comment_id,
            video_id=video_id,
            author_name=author_name,
            text=text,
            published_at=published_at,
            updated_at=updated_at,
            like_count=like_count,
        )
