"""Comprehensive Tests for Single-Comment Sentiment Analysis API Contract and Validation."""

import pytest
from httpx import AsyncClient
from ml.exceptions import ModelNotTrainedError, ModelLoadingError, InferenceError
from backend.app.services.sentiment_service import SentimentService


@pytest.mark.asyncio
async def test_sentiment_v1_malayalam_success(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes native Malayalam script."""
    payload = {
        "text": "ഈ സിനിമ വളരെ മികച്ചതാണ്, അഭിനയം ഗംഭീരം!",
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Section 34 Contract: Exact response keys
    assert set(data.keys()) == {
        "original_text",
        "sentiment",
        "confidence",
        "probabilities",
        "model",
        "processing",
    }

    assert data["original_text"] == payload["text"]
    assert data["sentiment"] in ("Positive", "Negative", "Neutral", "Mixed", "Unsupported")
    assert 0.0 <= data["confidence"] <= 1.0

    # Section 34 Contract: Exact probability keys
    probs = data["probabilities"]
    assert set(probs.keys()) == {"Positive", "Negative", "Neutral", "Mixed", "Unsupported"}
    for p_val in probs.values():
        assert 0.0 <= p_val <= 1.0
    assert 0.99 <= sum(probs.values()) <= 1.01

    # Exact model info
    assert set(data["model"].keys()) == {"name", "version"}
    assert isinstance(data["model"]["name"], str)
    assert isinstance(data["model"]["version"], str)

    # Exact processing info
    assert set(data["processing"].keys()) == {"processing_time_ms"}
    assert isinstance(data["processing"]["processing_time_ms"], (int, float))
    assert data["processing"]["processing_time_ms"] >= 0.0


@pytest.mark.asyncio
async def test_sentiment_v1_english_success(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes English comments."""
    payload = {
        "text": "This was an amazing presentation, very informative and concise.",
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["sentiment"] in ("Positive", "Negative", "Neutral", "Mixed", "Unsupported")
    assert 0.0 <= data["confidence"] <= 1.0
    assert set(data["probabilities"].keys()) == {"Positive", "Negative", "Neutral", "Mixed", "Unsupported"}


@pytest.mark.asyncio
async def test_sentiment_v1_manglish_success(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes Manglish (Romanized Malayalam)."""
    payload = {
        "text": "Padam kidilan aayirunnu, super directing!",
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["sentiment"] in ("Positive", "Negative", "Neutral", "Mixed", "Unsupported")
    assert 0.0 <= data["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_sentiment_v1_code_mixed_success(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes code-mixed Malayalam-English."""
    payload = {
        "text": "Ee movie really awesome aayirunnu, screenplay was top class!",
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["sentiment"] in ("Positive", "Negative", "Neutral", "Mixed", "Unsupported")
    assert 0.0 <= data["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_sentiment_v1_missing_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that payload missing 'text' field is rejected with 422 VALIDATION_ERROR."""
    payload = {}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_null_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that null text field is rejected with 422 VALIDATION_ERROR."""
    payload = {"text": None}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_wrong_data_type_rejected(async_client: AsyncClient) -> None:
    """Verifies that non-string 'text' field is rejected with 422 VALIDATION_ERROR."""
    payload = {"text": 12345}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_empty_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that an empty text field is rejected with 422 VALIDATION_ERROR."""
    payload = {"text": ""}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_whitespace_only_rejected(async_client: AsyncClient) -> None:
    """Verifies that whitespace-only text is rejected with 422 VALIDATION_ERROR."""
    payload = {"text": "   \n\t   "}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_model_not_trained_handling(async_client: AsyncClient) -> None:
    """Verifies that when a fine-tuned model checkpoint is missing, MODEL_NOT_TRAINED 503 is returned.
    
    CRITICAL REQUIREMENT: Never return HTTP 200 with fake predictions when model is untrained.
    """
    service = SentimentService.get_instance()
    original_ready = service._is_ready
    original_error = service._load_error

    try:
        service._is_ready = False
        service._load_error = ModelNotTrainedError(
            "The Kollamo sentiment model is not available for inference.",
            details=None,
        )

        payload = {"text": "നല്ല സിനിമ"}
        response = await async_client.post("/api/v1/sentiment", json=payload)
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "MODEL_NOT_TRAINED"
        assert data["error"]["message"] == "The Kollamo sentiment model is not available for inference."
    finally:
        service._is_ready = original_ready
        service._load_error = original_error


@pytest.mark.asyncio
async def test_sentiment_v1_model_loading_error_handling(async_client: AsyncClient) -> None:
    """Verifies that model initialization/loading error returns 503 MODEL_UNAVAILABLE."""
    service = SentimentService.get_instance()
    original_ready = service._is_ready
    original_error = service._load_error

    try:
        service._is_ready = False
        service._load_error = ModelLoadingError(
            "The configured model cannot currently be loaded or accessed.",
            details=None,
        )

        payload = {"text": "നല്ല സിനിമ"}
        response = await async_client.post("/api/v1/sentiment", json=payload)
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "MODEL_UNAVAILABLE"
    finally:
        service._is_ready = original_ready
        service._load_error = original_error


@pytest.mark.asyncio
async def test_sentiment_v1_inference_error_handling(async_client: AsyncClient) -> None:
    """Verifies that unhandled model inference error returns 500 INFERENCE_ERROR without stack traces."""
    service = SentimentService.get_instance()
    original_predictor = service.predictor

    class BrokenPredictor:
        def predict_single(self, text: str):
            raise InferenceError("Forward pass calculation failed on tensor dimension mismatch.")

    try:
        service.predictor = BrokenPredictor()
        payload = {"text": "നല്ല സിനിമ"}
        response = await async_client.post("/api/v1/sentiment", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INFERENCE_ERROR"
        assert "Forward pass calculation failed" not in response.text or "traceback" not in response.text
    finally:
        service.predictor = original_predictor
