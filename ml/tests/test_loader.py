"""Unit Tests for ModelLoader Abstraction and Lifecycle."""

import pytest
from unittest.mock import MagicMock, patch
import torch
from ml.models.loader import ModelLoader, BASE_PRETRAINED_MODEL, DEFAULT_CHECKPOINT_NAME
from ml.exceptions import ModelLoadingError, ModelNotTrainedError, ConfigurationError
from ml.models.baseline_model import BaselineClassifier
from ml.inference.predictor import SentimentPredictor


def test_model_loader_initialization_and_device():
    loader = ModelLoader(device="cpu")
    assert loader.device == "cpu"
    assert loader.model_name == "google/muril-base-cased"
    assert BASE_PRETRAINED_MODEL == "google/muril-base-cased"
    assert DEFAULT_CHECKPOINT_NAME == "kollamo-muril-sentiment-5class"
    assert not loader.is_loaded()


def test_model_loader_cuda_fallback_when_unavailable():
    with patch("torch.cuda.is_available", return_value=False):
        loader = ModelLoader(device="cuda")
        assert loader.device == "cpu"


def test_model_loader_baseline_loading_and_predictor():
    loader = ModelLoader(model_type="baseline", device="cpu")
    predictor = loader.get_predictor()

    assert loader.is_loaded()
    assert isinstance(predictor, SentimentPredictor)
    assert predictor.model is not None

    # Predictor cache reuse
    predictor_again = loader.get_predictor()
    assert predictor is predictor_again


def test_model_loader_unload():
    loader = ModelLoader(model_type="baseline", device="cpu")
    loader.get_predictor()
    assert loader.is_loaded()

    loader.unload()
    assert not loader.is_loaded()
    assert loader._model is None
    assert loader._predictor is None


def test_model_loader_invalid_model_type():
    loader = ModelLoader(model_type="invalid_type", device="cpu")
    with pytest.raises(ConfigurationError):
        loader.load_model()


def test_model_loader_muril_mocked():
    mock_model = MagicMock(spec=torch.nn.Module)
    mock_tokenizer = MagicMock()

    loader = ModelLoader(model_type="muril", device="cpu")
    loader._model = mock_model
    loader._tokenizer = mock_tokenizer

    predictor = loader.get_predictor()
    assert isinstance(predictor, SentimentPredictor)
    assert predictor.model is mock_model
    assert predictor.tokenizer is mock_tokenizer


def test_model_loader_untrained_muril_raises_model_not_trained_error():
    # Production guard: Attempting to load untrained base model for inference raises ModelNotTrainedError
    loader = ModelLoader(
        model_type="muril",
        weights_path="ml/models/saved_weights/nonexistent_model.pt",
        allow_untrained_fallback=False,
    )
    with pytest.raises(ModelNotTrainedError) as exc_info:
        loader.load_model()
    assert "MODEL_NOT_TRAINED" in str(exc_info.value)
    assert exc_info.value.details.get("status") == "MODEL_NOT_TRAINED"


def test_model_loader_test_fallback_mode():
    loader = ModelLoader(
        model_type="muril",
        allow_untrained_fallback=True,
    )
    with patch("ml.models.muril_classifier.MurilSentimentClassifier.__init__", return_value=None):
        with patch.object(torch.nn.Module, "to", return_value=None):
            with patch.object(torch.nn.Module, "eval", return_value=None):
                model = loader.load_model()
                assert model is not None
