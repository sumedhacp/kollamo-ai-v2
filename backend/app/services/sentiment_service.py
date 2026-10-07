"""Sentiment Analysis Service integrating ML Inference Predictor via Phase 2 ModelLoader."""

from pathlib import Path
from typing import Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.sentiment import (
    ClassProbabilities,
    SentimentRequest,
    SentimentResponse,
)
from ml.models.loader import ModelLoader
from ml.inference.predictor import SentimentPredictor
from ml.exceptions import (
    ModelNotTrainedError,
    ModelLoadingError,
    InferenceError,
    KollamoMLException,
)


class SentimentService:
    """Singleton service managing sentiment model lifecycle and inference requests."""

    _instance: Optional["SentimentService"] = None

    def __init__(self) -> None:
        self.predictor: Optional[SentimentPredictor] = None
        self._loader: Optional[ModelLoader] = None
        self._is_ready: bool = False
        self._load_error: Optional[Exception] = None
        self._load_model()

    @classmethod
    def get_instance(cls) -> "SentimentService":
        """Returns the singleton instance of the SentimentService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_instance(cls, instance: Optional["SentimentService"]) -> None:
        """Sets or resets the singleton instance (primarily for testing and fixtures)."""
        cls._instance = instance

    def _load_model(self) -> None:
        """Loads and caches the SentimentPredictor using Phase 2 ModelLoader."""
        weights_path = Path(settings.FINETUNED_WEIGHTS_PATH) if settings.FINETUNED_WEIGHTS_PATH else None
        logger.info(f"Initializing SentimentService with weights path: {weights_path}")

        try:
            self._loader = ModelLoader(
                model_name=settings.MURIL_MODEL_PATH,
                weights_path=weights_path,
                device=settings.ML_DEVICE,
                num_classes=5,
                model_type="auto",
                allow_untrained_fallback=False,
            )
            self.predictor = self._loader.get_predictor()
            self._is_ready = True
            self._load_error = None
            logger.info("Successfully loaded sentiment inference predictor via ModelLoader.")
        except ModelNotTrainedError as exc:
            logger.warning(f"Fine-tuned sentiment model not found/trained: {exc}")
            self.predictor = None
            self._is_ready = False
            self._load_error = exc
        except Exception as exc:
            logger.error(f"Failed to load sentiment model via ModelLoader: {exc}")
            self.predictor = None
            self._is_ready = False
            self._load_error = exc

    def reload(
        self,
        weights_path: Optional[str] = None,
        allow_untrained_fallback: bool = False,
    ) -> None:
        """Reloads the underlying model with custom configuration (used for test isolation)."""
        target_path = weights_path if weights_path is not None else settings.FINETUNED_WEIGHTS_PATH
        try:
            self._loader = ModelLoader(
                model_name=settings.MURIL_MODEL_PATH,
                weights_path=Path(target_path) if target_path else None,
                device=settings.ML_DEVICE,
                num_classes=5,
                model_type="auto",
                allow_untrained_fallback=allow_untrained_fallback,
            )
            self.predictor = self._loader.get_predictor()
            self._is_ready = True
            self._load_error = None
        except Exception as exc:
            self.predictor = None
            self._is_ready = False
            self._load_error = exc

    def is_ready(self) -> bool:
        """Returns True if the ML inference engine is initialized and ready."""
        return self._is_ready and self.predictor is not None

    def analyze_comment(self, request: SentimentRequest) -> SentimentResponse:
        """Performs non-heuristic sentiment classification on a single comment."""
        if not self.is_ready():
            if isinstance(self._load_error, ModelNotTrainedError):
                raise self._load_error
            elif isinstance(self._load_error, ModelLoadingError):
                raise self._load_error
            elif self._load_error:
                raise ModelLoadingError(f"Model engine failed to load: {self._load_error}")
            else:
                raise ModelNotTrainedError(
                    "Trained Kollamo checkpoint not found. Status: MODEL_NOT_TRAINED",
                    details={"status": "MODEL_NOT_TRAINED"},
                )

        prediction = self.predictor.predict_single(request.text)

        # Handle translation using translation service abstraction safely if requested
        translated_text: Optional[str] = None
        translation_status = "not_requested"

        if request.translate:
            try:
                from backend.app.services.translation_service import get_translation_service

                t_svc = get_translation_service()
                t_res = t_svc.translate_detailed(request.text)
                if t_res.status == "translated" and t_res.text:
                    translated_text = t_res.text
                    translation_status = "translated"
                elif t_res.status == "original":
                    translation_status = "original"
                else:
                    translation_status = t_res.status
            except Exception as e:
                logger.debug(f"Translation service call error: {e}")
                translation_status = "untranslated"

        probs_dict = prediction["class_probabilities"]
        class_probs = ClassProbabilities(**probs_dict)

        return SentimentResponse(
            original_text=prediction["original_text"],
            detected_language=prediction["detected_language"],
            detected_script=prediction["detected_script"],
            sentiment=prediction["sentiment"],
            confidence=prediction["confidence"],
            class_probabilities=class_probs,
            probabilities=probs_dict,
            translation_status=translation_status,
            translated_text=translated_text,
            model_metadata=prediction.get("model_metadata"),
            processing_metadata=prediction.get("processing_metadata"),
        )


def get_sentiment_service() -> SentimentService:
    """Dependency provider for SentimentService."""
    return SentimentService.get_instance()
