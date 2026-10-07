"""Translation Request and Response Schemas."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


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


class TranslationResponse(BaseModel):
    """Response payload for text translation."""

    original_text: str = Field(..., description="Original raw text submitted for translation")
    translated_text: str = Field(..., description="English translated text")
    source_language: str = Field(..., description="Detected or specified source language")
    target_language: str = Field(..., description="Target language")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Translation confidence score")
    detected_script: Optional[str] = Field(None, description="Detected script type")
    intermediate_malayalam: Optional[str] = Field(
        None, description="Intermediate Malayalam script if transliterated from Manglish"
    )
    method: str = Field(..., description="Method used for translation (lexicon, translit+cloud, direct, identity, fallback)")
    status: str = Field(..., description="Translation execution state (translated, original, fallback, error)")
