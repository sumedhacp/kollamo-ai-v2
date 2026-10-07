"""Model Loading and Lifecycle Abstraction for Kollamo.ai.

Provides a decoupled ModelLoader interface so backend services and worker
processes can manage model weights, device placement, and inference pipelines
without scattering Hugging Face or PyTorch initialization code across the application.

Strictly enforces the separation between base pretrained model (google/muril-base-cased)
and the fine-tuned 5-class Kollamo sentiment classifier (kollamo-muril-sentiment-5class).
"""

import logging
import os
from pathlib import Path
from typing import Optional, Any, Union, Dict
import torch

from ml.exceptions import ModelLoadingError, ModelNotTrainedError, ConfigurationError
from ml.models.baseline_model import BaselineClassifier
from ml.models.muril_classifier import MurilSentimentClassifier
from ml.models.taxonomy import (
    SENTIMENT_LABELS,
    SENTIMENT_CLASSES,
    ID2LABEL,
    ID2CLASS,
    LABEL2ID,
)

logger = logging.getLogger(__name__)

BASE_PRETRAINED_MODEL = "google/muril-base-cased"
DEFAULT_CHECKPOINT_NAME = "kollamo-muril-sentiment-5class"


class ModelLoader:
    """Manages model loading, tokenizer initialization, and SentimentPredictor creation."""

    def __init__(
        self,
        model_name: str = BASE_PRETRAINED_MODEL,
        weights_path: Optional[Union[str, Path]] = None,
        device: str = "cpu",
        num_classes: int = 5,
        model_type: str = "auto",
        allow_untrained_fallback: bool = False,
    ):
        """Initializes model loader configuration.

        Args:
            model_name: Base Hugging Face model identifier (must be google/muril-base-cased).
            weights_path: Path to fine-tuned weights file or checkpoint directory.
            device: Computing device ('cpu', 'cuda', 'mps', or 'auto').
            num_classes: Target sentiment categories (strictly 5).
            model_type: 'muril', 'baseline', or 'auto' (inferred from weights_path).
            allow_untrained_fallback: If True, allows raw architectural initialization without trained weights
                                      strictly for automated unit testing; never for production inference.
        """
        self.model_name = model_name
        self.weights_path = Path(weights_path) if weights_path else None
        self.requested_device = device
        self.num_classes = num_classes
        self.model_type = model_type
        self.allow_untrained_fallback = allow_untrained_fallback

        self._device = self._resolve_device(device)
        self._tokenizer: Optional[Any] = None
        self._model: Optional[Any] = None
        self._predictor: Optional[SentimentPredictor] = None

    @staticmethod
    def _resolve_device(device: str) -> str:
        """Resolves target computing device safely."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available. Falling back to CPU.")
            return "cpu"
        return device

    @property
    def device(self) -> str:
        """Returns the active computation device."""
        return self._device

    def is_loaded(self) -> bool:
        """Returns True if the model and predictor are fully loaded and ready."""
        return self._predictor is not None and self._model is not None

    def load_tokenizer(self, force_reload: bool = False) -> Any:
        """Loads and caches the official MuRIL WordPiece tokenizer."""
        if self._tokenizer is not None and not force_reload:
            return self._tokenizer

        try:
            from transformers import AutoTokenizer

            tokenizer_path = str(self.weights_path) if (
                self.weights_path and self.weights_path.is_dir() and (self.weights_path / "vocab.txt").exists()
            ) else self.model_name

            logger.info(f"Loading tokenizer from: {tokenizer_path}")
            self._tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
            return self._tokenizer
        except Exception as e:
            logger.error(f"Failed to load tokenizer from {self.model_name}: {e}")
            raise ModelLoadingError(f"Tokenizer loading failed for '{self.model_name}': {str(e)}") from e

    def load_model(self, force_reload: bool = False) -> Any:
        """Loads and caches the neural or baseline sentiment model."""
        if self._model is not None and not force_reload:
            return self._model

        # Determine model type
        inferred_type = self.model_type
        if inferred_type == "auto":
            if self.weights_path and self.weights_path.suffix == ".joblib":
                inferred_type = "baseline"
            else:
                inferred_type = "muril"

        logger.info(f"Loading model (type={inferred_type}, device={self._device})")

        try:
            if inferred_type == "baseline":
                if self.weights_path and self.weights_path.exists():
                    self._model = BaselineClassifier.load(str(self.weights_path))
                else:
                    logger.warning("Baseline weights not found. Fitting fallback in-memory baseline.")
                    from ml.data.dataset_loader import prepare_dataset
                    train_df, _, _, _ = prepare_dataset()
                    self._model = BaselineClassifier()
                    self._model.fit(train_df["clean_text"].tolist(), train_df["label_id"].tolist())
                return self._model

            elif inferred_type == "muril":
                if self.weights_path and self.weights_path.exists():
                    logger.info(f"Loading fine-tuned Kollamo checkpoint from: {self.weights_path}")
                    self._model = MurilSentimentClassifier.from_pretrained(
                        str(self.weights_path),
                        num_classes=self.num_classes,
                        device=self._device,
                    )
                else:
                    # Enforce critical rule: Base model is NOT the finished sentiment model
                    if not self.allow_untrained_fallback:
                        err_msg = (
                            f"Trained Kollamo checkpoint not found at '{self.weights_path or 'unspecified'}'. "
                            f"Base pretrained '{self.model_name}' cannot be used directly for production sentiment "
                            f"inference without task-specific fine-tuning. Status: MODEL_NOT_TRAINED"
                        )
                        logger.error(err_msg)
                        raise ModelNotTrainedError(err_msg, details={"status": "MODEL_NOT_TRAINED"})

                    # In test-only mode with allow_untrained_fallback=True
                    logger.warning("Initializing raw architecture without trained weights (TEST ONLY).")
                    self._model = MurilSentimentClassifier(
                        model_name=self.model_name,
                        num_classes=self.num_classes,
                        pretrained=False,
                    )
                    self._model.to(self._device)

                self._model.eval()
                return self._model

            else:
                raise ConfigurationError(f"Unsupported model type: {inferred_type}")

        except Exception as e:
            if isinstance(e, (ModelLoadingError, ModelNotTrainedError, ConfigurationError)):
                raise
            logger.error(f"Failed to load sentiment model: {e}")
            raise ModelLoadingError(f"Model initialization failed: {str(e)}") from e

    def get_predictor(self, force_reload: bool = False) -> Any:
        """Initializes and returns a reusable SentimentPredictor instance."""
        if self._predictor is not None and not force_reload:
            return self._predictor

        from ml.inference.predictor import SentimentPredictor

        model = self.load_model(force_reload=force_reload)

        # Tokenizer is required for PyTorch neural models, not for TF-IDF baseline
        tokenizer = None
        if isinstance(model, (MurilSentimentClassifier, torch.nn.Module)):
            tokenizer = self.load_tokenizer(force_reload=force_reload)

        self._predictor = SentimentPredictor(
            model=model,
            tokenizer=tokenizer,
            device=self._device,
        )
        return self._predictor

    def unload(self) -> None:
        """Frees model and tokenizer resources from memory."""
        self._model = None
        self._tokenizer = None
        self._predictor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Model and tokenizer unloaded from memory.")
