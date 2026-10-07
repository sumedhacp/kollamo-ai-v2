"""Sentiment Application Service for Kollamo.ai Backend (Phase 3).

Orchestrates calls to the canonical Phase 2 ML interface (backend/ml)
and maps results and timing into API response models.
"""

import time
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.sentiment import (
    SentimentAnalyzeRequest,
    SentimentAnalyzeResponse,
    SentimentProbabilities,
    ModelInfo,
    ProcessingInfo,
    SentimentRequest,
    SentimentResponse,
    ClassProbabilities,
)
from backend.ml.inference.service import (
    SentimentInferenceService,
    SentimentInferenceProtocol,
    ModelReadiness,
)
from backend.ml.exceptions import (
    ModelNotReadyError,
    ModelUnavailableError,
    InferenceError,
)


class SentimentService:
    """Application-level service orchestrating ML inference."""

    _instance: Optional["SentimentService"] = None

    def __init__(self, ml_service: Optional[SentimentInferenceService] = None) -> None:
        self.ml_service: SentimentInferenceService = ml_service or self._init_default_ml_service()

    @classmethod
    def get_instance(cls) -> "SentimentService":
        """Returns the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_instance(cls, instance: Optional["SentimentService"]) -> None:
        """Sets or resets the singleton instance (used for testing)."""
        cls._instance = instance

    def _init_default_ml_service(self) -> SentimentInferenceService:
        """Initializes default Phase 2 ML service."""
        try:
            from ml.models.loader import ModelLoader

            loader = ModelLoader(
                model_name=settings.MURIL_MODEL_PATH,
                weights_path=settings.FINETUNED_WEIGHTS_PATH,
                device=settings.ML_DEVICE,
                num_classes=5,
                model_type="auto",
                allow_untrained_fallback=False,
            )
            predictor = loader.get_predictor()
            logger.info("Successfully connected Phase 2 ML predictor.")
            return SentimentInferenceService(
                predictor=predictor,
                model_name=getattr(settings, "MODEL_NAME", "kollamo-muril-5class"),
                model_version=getattr(settings, "MODEL_VERSION", "v1"),
                is_fine_tuned=True,
            )
        except Exception as exc:
            # Check if this is an untrained model condition
            from ml.exceptions import ModelNotTrainedError
            if isinstance(exc, ModelNotTrainedError) or "MODEL_NOT_TRAINED" in str(exc) or "not found" in str(exc).lower():
                logger.warning(f"Fine-tuned model checkpoint not found; status MODEL_NOT_READY: {exc}")
                return SentimentInferenceService(
                    predictor=None,
                    model_name=getattr(settings, "MODEL_NAME", "kollamo-muril-5class"),
                    model_version=getattr(settings, "MODEL_VERSION", "v1"),
                    is_fine_tuned=False,
                    load_error=None,
                )
            logger.warning(f"Default Phase 2 ML service failed to load; status MODEL_UNAVAILABLE: {exc}")
            return SentimentInferenceService(
                predictor=None,
                model_name=getattr(settings, "MODEL_NAME", "kollamo-muril-5class"),
                model_version=getattr(settings, "MODEL_VERSION", "v1"),
                is_fine_tuned=False,
                load_error=exc,
            )

    def get_model_readiness(self) -> ModelReadiness:
        """Queries model readiness from canonical Phase 2 interface."""
        return self.ml_service.get_readiness()

    def analyze_v1(self, request: SentimentAnalyzeRequest) -> SentimentAnalyzeResponse:
        """Executes single-text sentiment analysis conforming to Phase 3 contract."""
        start_time = time.perf_counter()

        # Delegate to Phase 2 ML service
        prediction = self.ml_service.analyze(request.text)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return SentimentAnalyzeResponse(
            original_text=prediction.original_text,
            sentiment=prediction.sentiment,
            confidence=prediction.confidence,
            probabilities=SentimentProbabilities(**prediction.probabilities.model_dump()),
            model=ModelInfo(name=prediction.model_name, version=prediction.model_version),
            processing=ProcessingInfo(processing_time_ms=elapsed_ms),
        )

    def analyze_comment(self, request: SentimentRequest) -> SentimentResponse:
        """Legacy-compatible single-comment sentiment classification."""
        start_time = time.perf_counter()
        prediction = self.ml_service.analyze(request.text)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Convert to legacy lowercase keys dictionary for backward compatibility
        probs_dict = {
            "positive": prediction.probabilities.Positive,
            "negative": prediction.probabilities.Negative,
            "neutral": prediction.probabilities.Neutral,
            "mixed": prediction.probabilities.Mixed,
            "unsupported": prediction.probabilities.Unsupported,
        }

        return SentimentResponse(
            original_text=prediction.original_text,
            detected_language="ml",
            detected_script="Malayalam" if any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in request.text) else "Latin",
            sentiment=prediction.sentiment.lower(),
            confidence=prediction.confidence,
            class_probabilities=ClassProbabilities(**probs_dict),
            probabilities=probs_dict,
            translation_status="not_requested",
            translated_text=None,
            model_metadata={"architecture": prediction.model_name, "device": settings.ML_DEVICE},
            processing_metadata={"inference_time_ms": elapsed_ms},
        )


def get_sentiment_service() -> SentimentService:
    """Dependency injection provider."""
    return SentimentService.get_instance()
