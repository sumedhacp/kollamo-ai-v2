"""Canonical Phase 2 Prediction Schemas.

Owned by Phase 2 under backend/ml/schemas/prediction.py.
Consumed by Phase 3 FastAPI layer.
"""

from typing import Literal
from pydantic import BaseModel, Field


class SentimentProbabilities(BaseModel):
    """Exact probability distribution over the 5 discrete sentiment classes."""

    Positive: float = Field(..., ge=0.0, le=1.0)
    Negative: float = Field(..., ge=0.0, le=1.0)
    Neutral: float = Field(..., ge=0.0, le=1.0)
    Mixed: float = Field(..., ge=0.0, le=1.0)
    Unsupported: float = Field(..., ge=0.0, le=1.0)


class SentimentPrediction(BaseModel):
    """Canonical prediction contract returned by Phase 2 inference service."""

    original_text: str = Field(..., description="Original raw text submitted for inference")
    sentiment: Literal[
        "Positive",
        "Negative",
        "Neutral",
        "Mixed",
        "Unsupported",
    ] = Field(..., description="Primary sentiment classification label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model probability of the top class")
    probabilities: SentimentProbabilities = Field(
        ..., description="Exact 5-class normalized probability distribution"
    )
    model_name: str = Field(..., description="Name of the inference model")
    model_version: str = Field(..., description="Version of the inference model")
