"""YouTube Ingestion Service orchestrating URL parsing, API client, pagination, limits, and sorting."""

import time
from datetime import datetime
from typing import List, Literal, Optional, Union
try:
    from app.core.logging import logger
    from app.schemas.youtube import (
        YouTubeComment,
        YouTubeIngestionResult,
        YouTubeVideo,
    )
except ImportError:
    from backend.app.core.logging import logger
    from backend.app.schemas.youtube import (
        YouTubeComment,
        YouTubeIngestionResult,
        YouTubeVideo,
    )

from .client import YouTubeClient
from .parser import extract_video_id


class YouTubeIngestionService:
    """Service orchestrating end-to-end ingestion of YouTube video metadata and comments."""

    def __init__(self, client: Optional[YouTubeClient] = None):
        self.client = client or YouTubeClient()

    async def ingest(
        self,
        video_url: str,
        comment_limit: Union[int, Literal["ALL"]] = 100,
        sort_by: Literal["most_liked", "newest", "oldest"] = "newest",
    ) -> YouTubeIngestionResult:
        """Ingests video metadata and comments from YouTube according to limits and sort specifications.

        Args:
            video_url: Supported YouTube URL or canonical 11-character video ID.
            comment_limit: 50, 100, 250, 500, or 'ALL'.
            sort_by: 'most_liked', 'newest', or 'oldest'.

        Returns:
            Normalized YouTubeIngestionResult containing video metadata and comments list.
        """
        start_time = time.perf_counter()

        # Step 1: Parse and validate video identifier
        video_id = extract_video_id(video_url)
        logger.info(
            f"Starting YouTube ingestion for video_id='{video_id}' "
            f"(limit={comment_limit}, sort={sort_by})"
        )

        # Step 2: Fetch video metadata
        video_metadata: YouTubeVideo = await self.client.fetch_video_metadata(video_id)

        # Step 3: Determine pagination target limit
        target_limit: Optional[int] = None
        if comment_limit != "ALL":
            target_limit = int(comment_limit)

        # Map sorting mode to YouTube Data API v3 order parameter
        # 'newest' and 'oldest' use order='time'
        # 'most_liked' uses order='relevance' (YouTube's top comments parameter)
        api_order = "relevance" if sort_by == "most_liked" else "time"

        comments: List[YouTubeComment] = []
        page_token: Optional[str] = None
        safety_max = 5000  # Safety boundary preventing infinite pagination on 'ALL'

        # Step 4: Paginate through comments
        while True:
            # Calculate next page request size (between 1 and 100)
            batch_size = 100
            if target_limit is not None:
                remaining = target_limit - len(comments)
                if remaining <= 0:
                    break
                batch_size = min(remaining, 100)

            response = await self.client.fetch_comment_threads(
                video_id=video_id,
                max_results=batch_size,
                page_token=page_token,
                order=api_order,
            )

            items = response.get("items", [])
            if not items:
                break

            for item in items:
                comment = self.client.parse_comment_item(item, video_id=video_id)
                comments.append(comment)

                if target_limit is not None and len(comments) >= target_limit:
                    break

            page_token = response.get("nextPageToken")
            if not page_token:
                # No more comment pages available
                break

            if comment_limit == "ALL" and len(comments) >= safety_max:
                logger.warning(
                    f"Safety cap of {safety_max} comments reached for video_id='{video_id}'."
                )
                break

        # Step 5: Truncate to exact finite limit if requested
        if target_limit is not None and len(comments) > target_limit:
            comments = comments[:target_limit]

        # Step 6: Apply deterministic client-side sorting
        def _get_ts(c: YouTubeComment) -> float:
            if c.published_at:
                return c.published_at.timestamp()
            return 0.0

        if sort_by == "most_liked":
            # Highest like_count first, tiebreaker newest published_at
            comments.sort(key=lambda c: (-c.like_count, -_get_ts(c)))
        elif sort_by == "newest":
            # Latest publication timestamp first
            comments.sort(key=lambda c: -_get_ts(c))
        elif sort_by == "oldest":
            # Earliest publication timestamp first
            comments.sort(key=lambda c: _get_ts(c))

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            f"Completed YouTube ingestion for video_id='{video_id}': "
            f"collected={len(comments)} comments in {elapsed_ms}ms"
        )

        return YouTubeIngestionResult(
            video=video_metadata,
            comments=comments,
            requested_limit=comment_limit,
            returned_count=len(comments),
            sort_by=sort_by,
        )


def get_youtube_service() -> YouTubeIngestionService:
    """Dependency provider for FastAPI route injection."""
    return YouTubeIngestionService()
