"""Pydantic Request and Normalized Response Schemas for YouTube Ingestion."""

from datetime import datetime
from typing import List, Optional, Literal, Union, Any
from pydantic import BaseModel, Field, field_validator


class YouTubeIngestRequest(BaseModel):
    """Request model for YouTube video comment ingestion."""

    video_url: str = Field(
        ...,
        description="A supported YouTube video URL or canonical 11-character video ID.",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )
    comment_limit: Union[Literal[50, 100, 250, 500], Literal["ALL"]] = Field(
        default=100,
        description="Target maximum number of comments to collect: 50, 100, 250, 500, or ALL.",
        examples=[100],
    )
    sort_by: Literal["most_liked", "newest", "oldest"] = Field(
        default="newest",
        description="Sorting strategy for collected comments: most_liked, newest, or oldest.",
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


class YouTubeVideo(BaseModel):
    """Normalized metadata for an ingested YouTube video."""

    video_id: str = Field(..., description="Canonical 11-character YouTube video ID")
    title: str = Field(..., description="Video title")
    channel_title: Optional[str] = Field(None, description="Publishing channel title")
    published_at: Optional[datetime] = Field(None, description="Video upload / publication timestamp")
    description: Optional[str] = Field(None, description="Video description snippet")
    view_count: Optional[int] = Field(None, description="Total video view count")
    like_count: Optional[int] = Field(None, description="Total video like count")
    comment_count: Optional[int] = Field(None, description="Total comment count reported by video statistics")
    comment_count_available: Optional[int] = Field(None, description="Total comment count available")


class YouTubeComment(BaseModel):
    """Normalized representation of a single top-level YouTube comment."""

    comment_id: str = Field(..., description="Unique comment identifier")
    video_id: str = Field(..., description="Associated video ID")
    author_name: Optional[str] = Field(None, description="Display name of the comment author")
    text: str = Field(..., description="Original raw comment text (preserving Malayalam, emojis, script exactly)")
    published_at: Optional[datetime] = Field(None, description="Comment publication timestamp")
    updated_at: Optional[datetime] = Field(None, description="Comment last-updated timestamp")
    like_count: int = Field(default=0, description="Comment upvote / like count")


class YouTubeIngestionResult(BaseModel):
    """Normalized response envelope returned by the YouTube Ingestion Service."""

    video: YouTubeVideo = Field(..., description="Ingested video metadata")
    comments: List[YouTubeComment] = Field(..., description="List of ingested comments in requested sort order")
    requested_limit: Union[int, Literal["ALL"]] = Field(..., description="Requested comment limit")
    returned_count: int = Field(..., description="Actual number of comments collected")
    sort_by: Literal["most_liked", "newest", "oldest"] = Field(..., description="Applied sorting strategy")
