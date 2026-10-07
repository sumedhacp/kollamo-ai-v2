"""YouTube Ingestion Route conforming to Phase 4 Contract."""

from fastapi import APIRouter, Depends, status
try:
    from app.schemas.common import ErrorResponse
    from app.schemas.youtube import (
        YouTubeIngestRequest,
        YouTubeIngestionResult,
    )
    from app.services.youtube.service import (
        YouTubeIngestionService,
        get_youtube_service,
    )
except ImportError:
    from backend.app.schemas.common import ErrorResponse
    from backend.app.schemas.youtube import (
        YouTubeIngestRequest,
        YouTubeIngestionResult,
    )
    from backend.app.services.youtube.service import (
        YouTubeIngestionService,
        get_youtube_service,
    )

router = APIRouter(prefix="/youtube", tags=["YouTube"])


@router.post(
    "/ingest",
    response_model=YouTubeIngestionResult,
    status_code=status.HTTP_200_OK,
    summary="Synchronously ingest YouTube video metadata and comments",
    description=(
        "Accepts a YouTube video URL or ID, queries the official YouTube Data API v3, "
        "and returns normalized metadata and comments bounded by requested limits and sorting."
    ),
    responses={
        200: {
            "model": YouTubeIngestionResult,
            "description": "Successful YouTube video metadata and comments ingestion",
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid video URL or identifier (YOUTUBE_INVALID_VIDEO)",
        },
        404: {
            "model": ErrorResponse,
            "description": "Video was not found or is private (YOUTUBE_VIDEO_NOT_FOUND)",
        },
        422: {
            "model": ErrorResponse,
            "description": "Comments disabled (YOUTUBE_COMMENTS_DISABLED) or validation failure (VALIDATION_ERROR)",
        },
        429: {
            "model": ErrorResponse,
            "description": "YouTube Data API quota exceeded (YOUTUBE_QUOTA_EXCEEDED)",
        },
        502: {
            "model": ErrorResponse,
            "description": "Upstream YouTube API error or communication failure (YOUTUBE_API_ERROR)",
        },
        503: {
            "model": ErrorResponse,
            "description": "YouTube API key configuration missing (YOUTUBE_CONFIG_ERROR)",
        },
        500: {
            "model": ErrorResponse,
            "description": "Unexpected internal server error (INTERNAL_ERROR)",
        },
    },
)
async def ingest_youtube_video(
    request: YouTubeIngestRequest,
    youtube_service: YouTubeIngestionService = Depends(get_youtube_service),
) -> YouTubeIngestionResult:
    """Ingests video metadata and comments synchronously from YouTube Data API v3."""
    return await youtube_service.ingest(
        video_url=request.video_url,
        comment_limit=request.comment_limit,
        sort_by=request.sort_by,
    )
