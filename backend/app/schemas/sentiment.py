"""Sentiment Analysis Request and Response Schemas."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SentimentRequest(BaseModel):
    """Request payload for single-comment sentiment classification."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The social media comment to analyze (max 5000 characters).",
    )
    translate: bool = Field(
        default=True,
        description="Whether to provide English translation for regional/code-mixed comments.",
    )

    @field_validator("text")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Comment text cannot be empty or contain only whitespace.")
        return v


class ClassProbabilities(BaseModel):
    """Normalized probability distribution over the 5 discrete sentiment classes."""

    positive: float = Field(..., ge=0.0, le=1.0)
    negative: float = Field(..., ge=0.0, le=1.0)
    neutral: float = Field(..., ge=0.0, le=1.0)
    mixed: float = Field(..., ge=0.0, le=1.0)
    unsupported: float = Field(..., ge=0.0, le=1.0)


class SentimentResponse(BaseModel):
    """Response payload for single-comment sentiment classification."""

    original_text: str = Field(..., description="Original raw text submitted for analysis")
    detected_language: str = Field(..., description="Detected language code (ml, en, ml-en, etc.)")
    detected_script: str = Field(..., description="Detected script type (Malayalam, Latin, Mixed, etc.)")
    sentiment: str = Field(..., description="Primary sentiment classification label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score for the top class")
    class_probabilities: ClassProbabilities = Field(
        ..., description="Full probability distribution over all 5 sentiment classes"
    )
    translation_status: str = Field(
        ..., description="Translation execution state (original, translated, not_needed, untranslated)"
    )
    translated_text: Optional[str] = Field(
        None, description="English translation if requested and applicable"
    )
