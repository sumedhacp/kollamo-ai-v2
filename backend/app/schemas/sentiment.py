"""Sentiment Analysis Request and Response Schemas."""

from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ModelInfo(BaseModel):
    """Metadata regarding the inference model."""

    name: str = Field(..., description="Model architecture or identifier")
    version: str = Field(..., description="Model version tag")


class ProcessingInfo(BaseModel):
    """Execution timing and processing metadata."""

    processing_time_ms: float = Field(..., description="Measured processing time in milliseconds")


class SentimentProbabilities(BaseModel):
    """Normalized probability distribution over the 5 discrete sentiment classes."""

    Positive: float = Field(..., ge=0.0, le=1.0)
    Negative: float = Field(..., ge=0.0, le=1.0)
    Neutral: float = Field(..., ge=0.0, le=1.0)
    Mixed: float = Field(..., ge=0.0, le=1.0)
    Unsupported: float = Field(..., ge=0.0, le=1.0)


class SentimentAnalyzeRequest(BaseModel):
    """Request payload for POST /api/v1/sentiment."""

    text: str = Field(
        ...,
        description="The social media comment to analyze.",
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Comment text cannot be null.")
        if not isinstance(v, str):
            raise ValueError("Comment text must be a string.")
        if not v.strip():
            raise ValueError("Comment text cannot be empty or contain only whitespace.")
        if len(v) > 5000:
            raise ValueError("Comment text exceeds maximum length of 5000 characters.")
        return v


class SentimentAnalyzeResponse(BaseModel):
    """Authoritative response payload for POST /api/v1/sentiment."""

    original_text: str = Field(..., description="Original raw text submitted for analysis")
    sentiment: Literal[
        "Positive",
        "Negative",
        "Neutral",
        "Mixed",
        "Unsupported",
    ] = Field(..., description="Primary sentiment classification label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score for the top class")
    probabilities: SentimentProbabilities = Field(
        ..., description="Full probability distribution over the 5 sentiment classes"
    )
    model: ModelInfo = Field(..., description="Model information")
    processing: ProcessingInfo = Field(..., description="Processing telemetry")


# Aliases and Legacy Compatibility Schemas
class ClassProbabilities(BaseModel):
    """Normalized probability distribution over the 5 discrete sentiment classes (legacy)."""

    positive: float = Field(..., ge=0.0, le=1.0)
    negative: float = Field(..., ge=0.0, le=1.0)
    neutral: float = Field(..., ge=0.0, le=1.0)
    mixed: float = Field(..., ge=0.0, le=1.0)
    unsupported: float = Field(..., ge=0.0, le=1.0)


class SentimentRequest(BaseModel):
    """Request payload for single-comment sentiment classification (legacy compatible)."""

    text: str = Field(
        ...,
        description="The social media comment to analyze.",
    )
    translate: bool = Field(
        default=True,
        description="Whether to provide English translation for regional/code-mixed comments.",
    )

    @field_validator("text")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if v is None:
            raise ValueError("Comment text cannot be null.")
        if not isinstance(v, str):
            raise ValueError("Comment text must be a string.")
        if not v.strip():
            raise ValueError("Comment text cannot be empty or contain only whitespace.")
        if len(v) > 5000:
            raise ValueError("Comment text exceeds maximum allowed size.")
        return v


class SentimentResponse(BaseModel):
    """Response payload for single-comment sentiment classification (legacy compatible)."""

    original_text: str = Field(..., description="Original raw text submitted for analysis")
    detected_language: str = Field(..., description="Detected language code (ml, en, ml-en, etc.)")
    detected_script: str = Field(..., description="Detected script type (Malayalam, Latin, Mixed, etc.)")
    sentiment: str = Field(..., description="Primary sentiment classification label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score for the top class")
    class_probabilities: ClassProbabilities = Field(
        ..., description="Full probability distribution over all 5 sentiment classes"
    )
    probabilities: Optional[Dict[str, float]] = Field(
        default=None, description="Normalized probability distribution over the 5 sentiment classes"
    )
    translation_status: str = Field(
        ..., description="Translation execution state (original, translated, not_needed, untranslated)"
    )
    translated_text: Optional[str] = Field(
        None, description="English translation if requested and applicable"
    )
    model_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="ML Model architecture, device, and checkpoint metadata"
    )
    processing_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Inference runtime, token count, and preprocessing metadata"
    )
