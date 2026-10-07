"""Canonical Phase 2 Inference Service.

Owned by Phase 2 under backend/ml/inference/service.py.
Consumed by Phase 3 FastAPI layer via SentimentService.
"""

from typing import Protocol, Literal, Optional, Any
from pydantic import BaseModel, Field
from ..schemas.prediction import SentimentPrediction, SentimentProbabilities
from ..exceptions import ModelNotReadyError, ModelUnavailableError, InferenceError


class ModelReadiness(BaseModel):
    """Model readiness status payload."""

    status: Literal["MODEL_READY", "MODEL_NOT_READY", "MODEL_UNAVAILABLE"] = Field(
        ..., description="Readiness state of the ML inference model"
    )
    details: Optional[str] = Field(None, description="Diagnostic context regarding model state")


class SentimentInferenceProtocol(Protocol):
    """Protocol for Phase 2 Sentiment Inference Services."""

    def analyze(self, text: str) -> SentimentPrediction:
        """Runs sentiment inference on a single text comment."""
        ...

    def get_readiness(self) -> ModelReadiness:
        """Returns the readiness state of the model."""
        ...


class SentimentInferenceService:
    """Canonical Phase 2 Inference Service implementation."""

    def __init__(
        self,
        predictor: Optional[Any] = None,
        model_name: str = "kollamo-muril-5class",
        model_version: str = "v1",
        is_fine_tuned: bool = False,
        load_error: Optional[Exception] = None,
    ) -> None:
        self.predictor = predictor
        self.model_name = model_name
        self.model_version = model_version
        self.is_fine_tuned = is_fine_tuned
        self.load_error = load_error

    def get_readiness(self) -> ModelReadiness:
        """Evaluates model readiness according to Phase 3 Section 4 definitions."""
        if not self.is_fine_tuned:
            return ModelReadiness(
                status="MODEL_NOT_READY",
                details="Trained Kollamo 5-class checkpoint has not yet been fine-tuned.",
            )

        if self.load_error is not None:
            return ModelReadiness(
                status="MODEL_UNAVAILABLE",
                details=f"Model loading failure: {self.load_error}",
            )

        if self.predictor is not None:
            return ModelReadiness(status="MODEL_READY")

        return ModelReadiness(
            status="MODEL_UNAVAILABLE",
            details="Model predictor instance is not available.",
        )

    def analyze(self, text: str) -> SentimentPrediction:
        """Executes inference or raises typed readiness/availability errors."""
        readiness = self.get_readiness()

        if readiness.status == "MODEL_NOT_READY":
            raise ModelNotReadyError(
                "The Kollamo sentiment model is not ready for inference.",
                details={"status": "MODEL_NOT_READY"},
            )
        elif readiness.status == "MODEL_UNAVAILABLE":
            raise ModelUnavailableError(
                "The Kollamo sentiment model is currently unavailable.",
                details={"status": "MODEL_UNAVAILABLE"},
            )

        try:
            prediction = self.predictor.predict_single(text)

            raw_sentiment = prediction["sentiment"]
            capitalized_sentiment = raw_sentiment.capitalize()
            if capitalized_sentiment not in ("Positive", "Negative", "Neutral", "Mixed", "Unsupported"):
                capitalized_sentiment = "Unsupported"

            raw_probs = prediction["class_probabilities"]
            probs_map = {
                "Positive": float(raw_probs.get("positive", raw_probs.get("Positive", 0.0))),
                "Negative": float(raw_probs.get("negative", raw_probs.get("Negative", 0.0))),
                "Neutral": float(raw_probs.get("neutral", raw_probs.get("Neutral", 0.0))),
                "Mixed": float(raw_probs.get("mixed", raw_probs.get("Mixed", 0.0))),
                "Unsupported": float(raw_probs.get("unsupported", raw_probs.get("Unsupported", 0.0))),
            }
            total_p = sum(probs_map.values())
            if total_p > 0:
                probs_map = {k: round(v / total_p, 4) for k, v in probs_map.items()}

            confidence = round(float(probs_map.get(capitalized_sentiment, prediction.get("confidence", 0.0))), 4)

            return SentimentPrediction(
                original_text=text,
                sentiment=capitalized_sentiment,
                confidence=confidence,
                probabilities=SentimentProbabilities(**probs_map),
                model_name=self.model_name,
                model_version=self.model_version,
            )
        except Exception as exc:
            if isinstance(exc, (ModelNotReadyError, ModelUnavailableError)):
                raise
            raise InferenceError(f"Sentiment inference calculation failed: {str(exc)}") from exc
