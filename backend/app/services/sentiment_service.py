"""Sentiment Analysis Service integrating ML Inference Predictor."""

import os
from pathlib import Path
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.sentiment import (
    ClassProbabilities,
    SentimentRequest,
    SentimentResponse,
)
from ml.inference.predictor import SentimentPredictor
from ml.models.baseline_model import BaselineClassifier


class SentimentService:
    """Singleton service managing sentiment model lifecycle and inference requests."""

    _instance: Optional["SentimentService"] = None

    def __init__(self) -> None:
        self.predictor: Optional[SentimentPredictor] = None
        self._is_ready: bool = False
        self._load_model()

    @classmethod
    def get_instance(cls) -> "SentimentService":
        """Returns the singleton instance of the SentimentService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self) -> None:
        """Loads trained weights once at startup."""
        weights_path = Path(settings.FINETUNED_WEIGHTS_PATH)
        logger.info(f"Loading sentiment model weights from: {weights_path}")

        try:
            if weights_path.exists() and weights_path.suffix == ".joblib":
                model = BaselineClassifier.load(str(weights_path))
                self.predictor = SentimentPredictor(model=model, device=settings.ML_DEVICE)
                self._is_ready = True
                logger.info("Successfully loaded TF-IDF baseline sentiment classifier.")
            elif weights_path.exists():
                # Potential PyTorch / Hugging Face model directory
                from transformers import AutoTokenizer
                from ml.models.muril_classifier import MuRILSentimentClassifier
                import torch

                tokenizer = AutoTokenizer.from_pretrained(settings.MURIL_MODEL_PATH)
                model = MuRILSentimentClassifier.from_pretrained(str(weights_path))
                model.to(settings.ML_DEVICE)
                model.eval()
                self.predictor = SentimentPredictor(
                    model=model, tokenizer=tokenizer, device=settings.ML_DEVICE
                )
                self._is_ready = True
                logger.info("Successfully loaded fine-tuned MuRIL neural sentiment classifier.")
            else:
                # If weights file not found, fall back to fitting baseline on corpus
                logger.warning(
                    f"Saved model weights not found at {weights_path}. Initializing fallback baseline."
                )
                from ml.data.dataset_loader import load_sentiment_dataset

                train_texts, train_labels, _, _ = load_sentiment_dataset()
                model = BaselineClassifier()
                model.fit(train_texts, train_labels)
                self.predictor = SentimentPredictor(model=model, device=settings.ML_DEVICE)
                self._is_ready = True
                logger.info("Fitted in-memory fallback baseline model.")
        except Exception as exc:
            logger.error(f"Failed to load sentiment model: {exc}")
            self._is_ready = False

    def is_ready(self) -> bool:
        """Returns True if the ML inference engine is initialized and ready."""
        return self._is_ready and self.predictor is not None

    def analyze_comment(self, request: SentimentRequest) -> SentimentResponse:
        """Performs non-heuristic sentiment classification on a single comment."""
        if not self.is_ready():
            raise RuntimeError("Sentiment model engine is not loaded or ready.")

        prediction = self.predictor.predict_single(request.text)

        # Handle translation using translation service abstraction
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

        return SentimentResponse(
            original_text=prediction["original_text"],
            detected_language=prediction["detected_language"],
            detected_script=prediction["detected_script"],
            sentiment=prediction["sentiment"],
            confidence=prediction["confidence"],
            class_probabilities=ClassProbabilities(**prediction["class_probabilities"]),
            translation_status=translation_status,
            translated_text=translated_text,
        )


def get_sentiment_service() -> SentimentService:
    """Dependency provider for SentimentService."""
    return SentimentService.get_instance()
