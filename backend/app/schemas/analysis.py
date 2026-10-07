"""Pydantic Request, Response, and Telemetry Schemas for Asynchronous Analysis (Phase 5)."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator

try:
    from app.schemas.common import ErrorDetail
    from app.schemas.youtube import YouTubeVideo
except ImportError:
    from backend.app.schemas.common import ErrorDetail
    from backend.app.schemas.youtube import YouTubeVideo


class AnalysisJobRequest(BaseModel):
    """Request model for creating an asynchronous YouTube analysis job."""

    video_url: str = Field(
        ...,
        description="A supported YouTube video URL or canonical 11-character video ID.",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )
    comment_limit: Union[Literal[50, 100, 250, 500], Literal["ALL"]] = Field(
        default=100,
        description="Maximum number of comments to collect: 50, 100, 250, 500, or ALL.",
        examples=[100],
    )
    sort_by: Literal["most_liked", "newest", "oldest"] = Field(
        default="newest",
        description="Sorting strategy for comments: most_liked, newest, or oldest.",
        examples=["newest"],
    )

    @field_validator("comment_limit", mode="before")
    @classmethod
    def validate_comment_limit(cls, v: Any) -> Any:
        if isinstance(v, str):
            upper = v.strip().upper()
            if upper == "ALL":
                return "ALL"
            if upper in ("50", "100", "250", "500"):
                return int(upper)
        if isinstance(v, int) and v in (50, 100, 250, 500):
            return v
        if v == "ALL":
            return "ALL"
        raise ValueError("comment_limit must be one of: 50, 100, 250, 500, 'ALL'")


class JobCreatedResponse(BaseModel):
    """Response returned upon successful asynchronous job creation (HTTP 202)."""

    job_id: str = Field(..., description="Unique UUID identifying the analysis job")
    status: Literal["QUEUED"] = Field(default="QUEUED", description="Initial lifecycle state")


class JobProgress(BaseModel):
    """Detailed progress indicators for an active analysis job."""

    stage: str = Field(
        ...,
        description="Current processing stage (QUEUED, FETCHING_VIDEO, FETCHING_COMMENTS, SENTIMENT_ANALYSIS, FINALIZING, COMPLETED)",
    )
    completed: int = Field(..., description="Number of items completed in the current stage")
    total: Optional[int] = Field(None, description="Total items expected, or null if unknown")
    percentage: Optional[int] = Field(None, description="Calculated percentage of stage completion (0-100)")


class CommentSentimentResult(BaseModel):
    """Associated sentiment inference result for an ingested comment."""

    comment_id: str = Field(..., description="YouTube comment ID")
    text: str = Field(..., description="Raw comment text preserved verbatim")
    author_name: Optional[str] = Field(None, description="Author display name")
    like_count: int = Field(default=0, description="Comment like count")
    published_at: Optional[datetime] = Field(None, description="Timestamp comment was published")
    sentiment: Literal["Positive", "Negative", "Neutral", "Mixed", "Unsupported"] = Field(
        ..., description="Five-class predicted sentiment class"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Winning class probability confidence")
    probabilities: Dict[str, float] = Field(
        ..., description="Exact 5-class probability distribution summing to 1.0"
    )


class AnalysisResult(BaseModel):
    """Normalized payload containing completed video metadata, comment predictions, and model metadata."""

    video: YouTubeVideo = Field(..., description="Ingested video metadata")
    total_comments: int = Field(..., description="Total comments retrieved and processed")
    processed_comments: int = Field(..., description="Number of comments with sentiment predictions")
    comments: List[CommentSentimentResult] = Field(
        ..., description="Ordered list of ingested comments with per-comment sentiment predictions"
    )
    model_name: Optional[str] = Field(None, description="Canonical ML model identifier")
    model_version: Optional[str] = Field(None, description="Model checkpoint version")


class JobStatusResponse(BaseModel):
    """Canonical public response schema for querying analysis job state."""

    job_id: str = Field(..., description="Unique UUID identifying the analysis job")
    status: Literal["QUEUED", "PROCESSING", "COMPLETED", "FAILED"] = Field(
        ..., description="Canonical job status"
    )
    progress: Optional[JobProgress] = Field(None, description="Live execution progress")
    result: Optional[AnalysisResult] = Field(None, description="Normalized result when COMPLETED")
    error: Optional[ErrorDetail] = Field(None, description="Sanitized error details if status is FAILED")
