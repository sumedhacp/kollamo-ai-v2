"""Unit Tests for ModelLoader Abstraction and Lifecycle."""

import pytest
from unittest.mock import MagicMock, patch
import torch
from ml.models.loader import ModelLoader
from ml.exceptions import ModelLoadingError, ConfigurationError
from ml.models.baseline_model import BaselineClassifier
from ml.inference.predictor import SentimentPredictor


def test_model_loader_initialization_and_device():
    loader = ModelLoader(device="cpu")
    assert loader.device == "cpu"
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
    with pytest.raises(ModelLoadingError):
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
