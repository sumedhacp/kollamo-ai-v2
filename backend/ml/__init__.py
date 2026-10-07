"""Canonical Phase 2 ML Interface and Schemas Package for Kollamo.ai."""

from backend.ml.schemas.prediction import (
    SentimentPrediction,
    SentimentProbabilities,
)
from backend.ml.inference.service import (
    SentimentInferenceService,
    SentimentInferenceProtocol,
    ModelReadiness,
)
from backend.ml.exceptions import (
    KollamoMLException,
    ModelNotReadyError,
    ModelUnavailableError,
    InferenceError,
)

__all__ = [
    "SentimentPrediction",
    "SentimentProbabilities",
    "SentimentInferenceService",
    "SentimentInferenceProtocol",
    "ModelReadiness",
    "KollamoMLException",
    "ModelNotReadyError",
    "ModelUnavailableError",
    "InferenceError",
]
