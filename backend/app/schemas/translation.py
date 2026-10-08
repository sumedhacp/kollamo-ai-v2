"""Translation Request and Response Schemas for Kollamo.ai Phase 8."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TranslationStatus(str, Enum):
    """Lifecycle statuses for comment translation processing."""
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NOT_NEEDED = "NOT_NEEDED"


class TranslationRequest(BaseModel):
    """Request payload for text translation."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The Malayalam, Manglish, or code-mixed text to translate (max 5000 characters).",
    )
    source_language: str = Field(
        default="auto",
        description="Source language code ('auto', 'ml', 'en', 'manglish').",
    )
    target_language: str = Field(
        default="en",
        description="Target language code (defaults to 'en').",
    )

    @field_validator("text")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text cannot be empty or contain only whitespace.")
        return v


class CommentTranslation(BaseModel):
    """Data contract representing the translation representation for a comment."""

    original_text: str = Field(..., description="Original raw text of the comment")
    translated_text: Optional[str] = Field(None, description="English translation if completed")
    source_language: Optional[str] = Field(None, description="Source language of the comment")
    target_language: str = Field(default="en", description="Target translation language")
    status: str = Field(
        default="COMPLETED",
        description="Translation lifecycle status (NOT_REQUESTED, PENDING, COMPLETED, FAILED, NOT_NEEDED)",
    )
    error_message: Optional[str] = Field(None, description="Failure reason if status is FAILED")


class TranslationResponse(BaseModel):
    """Response payload for text translation endpoint."""

    original_text: str = Field(..., description="Original raw text submitted for translation")
    translated_text: str = Field(..., description="English translated text")
    source_language: str = Field(..., description="Detected or specified source language")
    target_language: str = Field(default="en", description="Target language")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Translation confidence score")
    detected_script: Optional[str] = Field(None, description="Detected script type")
    intermediate_malayalam: Optional[str] = Field(
        None, description="Intermediate Malayalam script if transliterated from Manglish"
    )
    method: str = Field(default="direct", description="Method used for translation (lexicon, translit+cloud, direct, identity, fallback)")
    status: str = Field(default="translated", description="Translation execution state (translated, original, fallback, error, NOT_NEEDED, COMPLETED)")
    error_message: Optional[str] = Field(None, description="Optional error message if translation failed")
