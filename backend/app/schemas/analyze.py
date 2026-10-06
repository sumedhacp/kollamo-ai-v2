"""YouTube Ingestion and Batch Analysis Job Schemas."""

import re
from datetime import datetime
from typing import Dict, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator

# Regex for YouTube video URL validation
YOUTUBE_URL_REGEX = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
    re.IGNORECASE,
)


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extracts the 11-character video ID from a YouTube URL if valid."""
    match = YOUTUBE_URL_REGEX.search(url.strip())
    if match:
        return match.group(4)
    return None


class AnalyzeRequest(BaseModel):
    """Payload to dispatch a YouTube video comment ingestion and analysis job."""

    youtube_url: str = Field(
        ...,
        description="Valid YouTube video URL (e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
    )
    sample_size: Union[int, Literal["all"]] = Field(
        default=250,
        description="Number of comments to sample: 50, 100, 250, 500, or 'all'",
    )
    sort_mode: Literal["top", "newest", "oldest"] = Field(
        default="top",
        description="YouTube comment sort mode: 'top' (Most Liked), 'newest', or 'oldest'",
    )

    @field_validator("youtube_url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        if not v or not extract_youtube_video_id(v):
            raise ValueError(
                "Invalid YouTube URL. Must be a valid standard watch, youtu.be, or shorts URL."
            )
        return v.strip()

    @field_validator("sample_size")
    @classmethod
    def validate_sample_size(cls, v: Union[int, str]) -> Union[int, str]:
        allowed_sizes = {50, 100, 250, 500, "all"}
        if v not in allowed_sizes:
            raise ValueError(f"Sample size must be one of {allowed_sizes}. Got: {v}")
        return v


class AnalyzeResponse(BaseModel):
    """Immediate 202 Accepted response upon queueing an analysis job."""

    job_id: str = Field(..., description="Unique UUID assigned to the analysis job")
    status: str = Field(default="queued", description="Initial job state ('queued')")
    message: str = Field(
        default="Analysis job queued successfully",
        description="Status description for user confirmation",
    )
    created_at: datetime = Field(..., description="Timestamp when the job was accepted")


class VideoSummary(BaseModel):
    """Metadata summary of the analyzed YouTube video."""

    video_id: str = Field(..., description="YouTube 11-character video ID")
    title: str = Field(..., description="Video title")
    channel_title: Optional[str] = Field(None, description="Channel / creator name")
    view_count: int = Field(default=0, description="Total video view count at ingestion time")


class SentimentCounts(BaseModel):
    """Total comment counts grouped by sentiment label."""

    positive: int = 0
    negative: int = 0
    neutral: int = 0
    mixed: int = 0
    unsupported: int = 0


class SentimentPercentages(BaseModel):
    """Percentage share per sentiment label (0.0 - 100.0)."""

    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0
    mixed: float = 0.0
    unsupported: float = 0.0


class EngagementMetrics(BaseModel):
    """Audience interaction and like distribution metrics."""

    total_likes: int = 0
    average_likes_per_sentiment: Dict[str, float] = Field(
        default_factory=lambda: {
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 0.0,
            "mixed": 0.0,
            "unsupported": 0.0,
        }
    )


class JobSummary(BaseModel):
    """Complete aggregated audience intelligence metrics for a job."""

    sentiment_counts: SentimentCounts
    sentiment_percentages: SentimentPercentages
    engagement_metrics: EngagementMetrics


class JobStatusResponse(BaseModel):
    """Detailed telemetry and results response for GET /api/analyze/{job_id}."""

    job_id: str = Field(..., description="Unique job UUID")
    status: str = Field(
        ...,
        description="Current state: 'queued', 'running', 'completed', 'failed', 'cancelled'",
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Deterministic job completion ratio (0.0 to 1.0)",
    )
    processed_comments: int = Field(default=0, description="Comments processed so far")
    total_comments: int = Field(default=0, description="Total comments discovered/targeted")
    video: Optional[VideoSummary] = Field(None, description="Video metadata if available")
    summary: Optional[JobSummary] = Field(None, description="Audience metrics if available")
    created_at: datetime = Field(..., description="Queueing timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error: Optional[str] = Field(None, description="Failure diagnostic message if status is 'failed'")
