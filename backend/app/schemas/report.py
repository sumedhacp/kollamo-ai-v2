"""Report Generation Request and Response Schemas."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ReportVideoInfo(BaseModel):
    """Metadata regarding the analyzed YouTube video."""

    video_id: str = Field(..., description="YouTube video identifier")
    title: str = Field(..., description="Video title")
    channel_title: str = Field(..., description="Channel or creator name")
    url: str = Field(..., description="Canonical YouTube video URL")
    published_at: Optional[str] = Field(None, description="Video publication date")


class ReportSentimentSummary(BaseModel):
    """Aggregated sentiment metrics and approval index."""

    counts: Dict[str, int] = Field(..., description="Absolute counts per sentiment class")
    percentages: Dict[str, float] = Field(..., description="Percentage share per sentiment class")
    dominant_sentiment: str = Field(..., description="Primary overall sentiment label")
    net_approval_index: float = Field(
        ..., description="Net Sentiment Approval spread (% Positive - % Negative)"
    )
    consensus_label: str = Field(
        ..., description="Categorical consensus label (Overwhelmingly Positive, etc.)"
    )
    average_confidence: float = Field(..., description="Mean model classification confidence")


class ReportEngagementSummary(BaseModel):
    """Audience engagement and reaction metrics."""

    total_likes: int = Field(..., description="Sum of likes across analyzed comments")
    average_likes_per_comment: float = Field(..., description="Mean likes per comment")
    average_likes_per_sentiment: Dict[str, float] = Field(
        ..., description="Average likes per sentiment category"
    )


class ReportLinguisticBreakdown(BaseModel):
    """Language and script distribution statistics."""

    malayalam_script_count: int = Field(..., description="Count of pure Malayalam script comments")
    manglish_count: int = Field(..., description="Count of Romanized Malayalam (Manglish) comments")
    code_mixed_count: int = Field(..., description="Count of Malayalam-English code-mixed comments")
    english_count: int = Field(..., description="Count of English comments")
    malayalam_percentage: float = Field(..., description="Percentage of pure Malayalam comments")
    manglish_percentage: float = Field(..., description="Percentage of Manglish comments")
    code_mixed_percentage: float = Field(..., description="Percentage of code-mixed comments")
    english_percentage: float = Field(..., description="Percentage of English comments")


class ReportCommentItem(BaseModel):
    """Exemplary comment with sentiment and English translation."""

    comment_id: str = Field(..., description="Comment identifier")
    author: str = Field(..., description="Author display name")
    original_text: str = Field(..., description="Raw comment text preserved")
    translated_text: Optional[str] = Field(None, description="English translation")
    sentiment: str = Field(..., description="Sentiment label")
    confidence: float = Field(..., description="Model confidence score")
    like_count: int = Field(..., description="Community likes count")
    detected_script: str = Field(..., description="Detected script / language")


class ReportMethodology(BaseModel):
    """Academic and architectural methodology disclosures."""

    model_name: str = Field(..., description="Name of pre-trained model backbone")
    model_version: str = Field(..., description="Fine-tuned model checkpoint / version")
    architecture: str = Field(..., description="Model architecture type")
    sentiment_classes: List[str] = Field(..., description="Discrete classification labels")
    translation_engine: str = Field(..., description="Translation service architecture")
    evaluation_framework: str = Field(..., description="Evaluation benchmark framework")


class AnalysisReportResponse(BaseModel):
    """Full comprehensive audience intelligence report payload."""

    job_id: str = Field(..., description="Analysis job UUID")
    title: str = Field(default="Kollamo.ai Audience Intelligence Executive Report")
    generated_at: str = Field(..., description="ISO 8601 report generation timestamp")
    total_comments_analyzed: int = Field(..., description="Total volume of comments analyzed")
    video_info: ReportVideoInfo = Field(..., description="Analyzed video metadata")
    sentiment_summary: ReportSentimentSummary = Field(..., description="Aggregated sentiment metrics")
    engagement_summary: ReportEngagementSummary = Field(..., description="Engagement telemetry")
    linguistic_breakdown: ReportLinguisticBreakdown = Field(..., description="Script breakdown")
    top_positive_comments: List[ReportCommentItem] = Field(
        default_factory=list, description="Top positive comments by engagement and confidence"
    )
    top_negative_comments: List[ReportCommentItem] = Field(
        default_factory=list, description="Top negative / critical comments by engagement and confidence"
    )
    methodology: ReportMethodology = Field(..., description="Methodology and model details")
    disclaimer: str = Field(..., description="Academic and legal disclaimer")
