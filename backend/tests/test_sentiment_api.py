"""Comprehensive Tests for Single-Comment Sentiment Analysis API Contract and Validation."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from ml.exceptions import ModelNotTrainedError, ModelLoadingError
from backend.app.services.sentiment_service import SentimentService


@pytest.mark.asyncio
async def test_sentiment_v1_malayalam(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes native Malayalam script."""
    payload = {
        "text": "ഈ സിനിമ വളരെ മികച്ചതാണ്, അഭിനയം ഗംഭീരം!",
        "translate": False,
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["detected_script"] == "Malayalam"
    assert data["detected_language"] in ("ml", "ml-en")
    assert data["sentiment"] in ("positive", "negative", "neutral", "mixed", "unsupported")
    assert 0.0 <= data["confidence"] <= 1.0

    probs = data["class_probabilities"]
    assert set(probs.keys()) == {"positive", "negative", "neutral", "mixed", "unsupported"}
    assert 0.99 <= sum(probs.values()) <= 1.01

    assert "model_metadata" in data
    assert "processing_metadata" in data


@pytest.mark.asyncio
async def test_sentiment_v1_english(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes English comments."""
    payload = {
        "text": "This was an amazing presentation, very informative and concise.",
        "translate": False,
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["detected_language"] == "en"
    assert data["detected_script"] == "Latin"
    assert data["sentiment"] in ("positive", "negative", "neutral", "mixed", "unsupported")


@pytest.mark.asyncio
async def test_sentiment_v1_manglish(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes Manglish (Romanized Malayalam)."""
    payload = {
        "text": "Padam kidilan aayirunnu, super directing!",
        "translate": True,
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["detected_script"] == "Latin"
    assert data["sentiment"] in ("positive", "negative", "neutral", "mixed", "unsupported")


@pytest.mark.asyncio
async def test_sentiment_v1_code_mixed(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes code-mixed Malayalam-English."""
    payload = {
        "text": "Ee movie really awesome aayirunnu, screenplay was top class!",
        "translate": False,
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["sentiment"] in ("positive", "negative", "neutral", "mixed", "unsupported")


@pytest.mark.asyncio
async def test_sentiment_v1_empty_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that an empty text field is rejected with 422 and structured error."""
    payload = {"text": ""}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]


@pytest.mark.asyncio
async def test_sentiment_v1_whitespace_only_rejected(async_client: AsyncClient) -> None:
    """Verifies that whitespace-only text is rejected with 422."""
    payload = {"text": "   \n\t   "}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_missing_field_rejected(async_client: AsyncClient) -> None:
    """Verifies that payload missing 'text' field is rejected with 422."""
    payload = {"translate": False}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_invalid_field_type_rejected(async_client: AsyncClient) -> None:
    """Verifies that non-string 'text' field is rejected with 422."""
    payload = {"text": 12345}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_v1_oversized_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that text exceeding 5000 characters is rejected with 422."""
    oversized = "നല്ല സിനിമ " * 600  # ~7200 characters
    payload = {"text": oversized}
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
            "Trained Kollamo checkpoint not found. Status: MODEL_NOT_TRAINED",
            details={"status": "MODEL_NOT_TRAINED"},
        )

        payload = {"text": "നല്ല സിനിമ"}
        response = await async_client.post("/api/v1/sentiment", json=payload)
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "MODEL_NOT_TRAINED"
        assert data["error"]["details"] == {"status": "MODEL_NOT_TRAINED"}
    finally:
        service._is_ready = original_ready
        service._load_error = original_error


@pytest.mark.asyncio
async def test_sentiment_v1_model_loading_error_handling(async_client: AsyncClient) -> None:
    """Verifies that model initialization/loading error returns structured 503 error."""
    service = SentimentService.get_instance()
    original_ready = service._is_ready
    original_error = service._load_error

    try:
        service._is_ready = False
        service._load_error = ModelLoadingError(
            "Model checkpoint corrupted or device failed to allocate.",
            details={"status": "MODEL_UNAVAILABLE"},
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
