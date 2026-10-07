"""Comprehensive Tests for Single-Comment Sentiment Analysis API Contract and Validation.

Adheres strictly to Phase 3 Section 33 requirements:
- health
- English, Malayalam, Manglish, code-mixed input
- missing field, null, wrong type, empty string, whitespace-only string
- exact 5 probability keys, ranges, confidence relationship
- model metadata, processing time
- MODEL_NOT_READY, MODEL_UNAVAILABLE, INFERENCE_ERROR, unexpected internal exception
- OpenAPI documentation
- Isolated ML interface mocking (zero GPU, zero weight downloads required)
"""

from typing import Dict, Any
import pytest
from httpx import AsyncClient
from backend.app.main import app
from backend.app.services.sentiment import SentimentService, get_sentiment_service
from backend.ml.schemas.prediction import SentimentPrediction, SentimentProbabilities
from backend.ml.inference.service import SentimentInferenceService, ModelReadiness
from backend.ml.exceptions import (
    ModelNotReadyError,
    ModelUnavailableError,
    InferenceError,
)


class MockPredictor:
    """Mock predictor returning deterministic 5-class sentiment for unit testing."""

    def predict_single(self, text: str) -> Dict[str, Any]:
        return {
            "sentiment": "Positive",
            "confidence": 0.96,
            "class_probabilities": {
                "positive": 0.96,
                "negative": 0.01,
                "neutral": 0.01,
                "mixed": 0.01,
                "unsupported": 0.01,
            },
        }


@pytest.fixture(autouse=True)
def setup_mock_ml_service():
    """Mocks Phase 2 ML interface for API test isolation without GPU or downloaded checkpoints."""
    mock_ml = SentimentInferenceService(
        predictor=MockPredictor(),
        model_name="kollamo-muril-5class",
        model_version="v1",
        is_fine_tuned=True,
    )
    test_sentiment_service = SentimentService(ml_service=mock_ml)
    original_service = SentimentService._instance
    SentimentService.set_instance(test_sentiment_service)

    # FastAPI dependency override
    app.dependency_overrides[get_sentiment_service] = lambda: test_sentiment_service

    yield test_sentiment_service

    # Restore original instance
    SentimentService.set_instance(original_service)
    app.dependency_overrides.pop(get_sentiment_service, None)


@pytest.mark.asyncio
async def test_sentiment_v1_malayalam_success(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/sentiment correctly processes native Malayalam script."""
    payload = {
        "text": "ഈ സിനിമ വളരെ മികച്ചതാണ്, അഭിനയം ഗംഭീരം!",
    }
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Section 25 & 26 Contract: Exact response keys
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

    # Section 15 Contract: Exact probability keys
    probs = data["probabilities"]
    assert set(probs.keys()) == {"Positive", "Negative", "Neutral", "Mixed", "Unsupported"}
    for p_val in probs.values():
        assert 0.0 <= p_val <= 1.0
    assert 0.99 <= sum(probs.values()) <= 1.01

    # Confidence matches the chosen sentiment's probability
    assert data["confidence"] == probs[data["sentiment"]]

    # Exact model info
    assert set(data["model"].keys()) == {"name", "version"}
    assert data["model"]["name"] == "kollamo-muril-5class"
    assert data["model"]["version"] == "v1"

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
    assert data["confidence"] == data["probabilities"][data["sentiment"]]


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
    assert set(data["probabilities"].keys()) == {"Positive", "Negative", "Neutral", "Mixed", "Unsupported"}
    assert data["confidence"] == data["probabilities"][data["sentiment"]]


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
    assert set(data["probabilities"].keys()) == {"Positive", "Negative", "Neutral", "Mixed", "Unsupported"}
    assert data["confidence"] == data["probabilities"][data["sentiment"]]


@pytest.mark.asyncio
async def test_sentiment_v1_missing_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that payload missing 'text' field is rejected with 422 VALIDATION_ERROR and code REQUIRED."""
    payload = {}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    assert "details" in data["error"]
    assert "fields" in data["error"]["details"]
    fields = data["error"]["details"]["fields"]
    assert len(fields) >= 1
    field_err = fields[0]
    assert field_err["field"] == "text"
    assert field_err["code"] == "REQUIRED"
    assert field_err["message"] == "Text is required."


@pytest.mark.asyncio
async def test_sentiment_v1_null_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that null text field is rejected with 422 VALIDATION_ERROR and code INVALID_TYPE."""
    payload = {"text": None}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    fields = data["error"]["details"]["fields"]
    assert len(fields) >= 1
    field_err = fields[0]
    assert field_err["field"] == "text"
    assert field_err["code"] == "INVALID_TYPE"
    assert field_err["message"] == "Text must be a string."


@pytest.mark.asyncio
async def test_sentiment_v1_wrong_data_type_rejected(async_client: AsyncClient) -> None:
    """Verifies that non-string 'text' field is rejected with 422 VALIDATION_ERROR and code INVALID_TYPE."""
    payload = {"text": 12345}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    fields = data["error"]["details"]["fields"]
    assert len(fields) >= 1
    field_err = fields[0]
    assert field_err["field"] == "text"
    assert field_err["code"] == "INVALID_TYPE"
    assert field_err["message"] == "Text must be a string."


@pytest.mark.asyncio
async def test_sentiment_v1_empty_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that an empty text field is rejected with 422 VALIDATION_ERROR and code EMPTY_TEXT."""
    payload = {"text": ""}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    fields = data["error"]["details"]["fields"]
    assert len(fields) >= 1
    field_err = fields[0]
    assert field_err["field"] == "text"
    assert field_err["code"] == "EMPTY_TEXT"
    assert field_err["message"] == "Text cannot be empty or contain only whitespace."


@pytest.mark.asyncio
async def test_sentiment_v1_whitespace_only_rejected(async_client: AsyncClient) -> None:
    """Verifies that whitespace-only text is rejected with 422 VALIDATION_ERROR and code EMPTY_TEXT."""
    payload = {"text": "   \n\t   "}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    fields = data["error"]["details"]["fields"]
    assert len(fields) >= 1
    field_err = fields[0]
    assert field_err["field"] == "text"
    assert field_err["code"] == "EMPTY_TEXT"
    assert field_err["message"] == "Text cannot be empty or contain only whitespace."


@pytest.mark.asyncio
async def test_sentiment_v1_model_not_ready_handling(async_client: AsyncClient) -> None:
    """Verifies that when a fine-tuned model checkpoint is missing, MODEL_NOT_READY 503 is returned.

    CRITICAL REQUIREMENT: Never return HTTP 200 with fake predictions when model is not ready.
    """
    untrained_ml = SentimentInferenceService(
        predictor=None,
        model_name="kollamo-muril-5class",
        model_version="v1",
        is_fine_tuned=False,
    )
    svc = SentimentService(ml_service=untrained_ml)
    app.dependency_overrides[get_sentiment_service] = lambda: svc

    payload = {"text": "നല്ല സിനിമ"}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MODEL_NOT_READY"
    assert data["error"]["message"] == "The Kollamo sentiment model is not ready for inference."
    assert data["error"]["details"] is None


@pytest.mark.asyncio
async def test_sentiment_v1_model_loading_error_handling(async_client: AsyncClient) -> None:
    """Verifies that model initialization/loading error returns 503 MODEL_UNAVAILABLE."""
    unavailable_ml = SentimentInferenceService(
        predictor=None,
        model_name="kollamo-muril-5class",
        model_version="v1",
        is_fine_tuned=True,
        load_error=RuntimeError("Corrupted checkpoint or CUDA failure"),
    )
    svc = SentimentService(ml_service=unavailable_ml)
    app.dependency_overrides[get_sentiment_service] = lambda: svc

    payload = {"text": "നല്ല സിനിമ"}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MODEL_UNAVAILABLE"
    assert data["error"]["message"] == "The Kollamo sentiment model is currently unavailable."
    assert data["error"]["details"] is None


@pytest.mark.asyncio
async def test_sentiment_v1_inference_error_handling(async_client: AsyncClient) -> None:
    """Verifies that unhandled model inference error returns 500 INFERENCE_ERROR without stack traces."""
    class BrokenPredictor:
        def predict_single(self, text: str):
            raise RuntimeError("Internal tensor dimension mismatch calculation error")

    broken_ml = SentimentInferenceService(
        predictor=BrokenPredictor(),
        model_name="kollamo-muril-5class",
        model_version="v1",
        is_fine_tuned=True,
    )
    svc = SentimentService(ml_service=broken_ml)
    app.dependency_overrides[get_sentiment_service] = lambda: svc

    payload = {"text": "നല്ല സിനിമ"}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INFERENCE_ERROR"
    assert data["error"]["message"] == "Sentiment inference failed."
    assert data["error"]["details"] is None
    assert "Internal tensor dimension mismatch" not in response.text
    assert "traceback" not in response.text.lower()


@pytest.mark.asyncio
async def test_sentiment_v1_internal_error_handling(async_client: AsyncClient) -> None:
    """Verifies that unexpected server exceptions return 500 INTERNAL_ERROR without leaking internals."""
    class CrashingService:
        def analyze_v1(self, request):
            raise Exception("Unexpected runtime exception in service layer")

    try:
        app.dependency_overrides[get_sentiment_service] = lambda: CrashingService()

        payload = {"text": "നല്ല സിനിമ"}
        response = await async_client.post("/api/v1/sentiment", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["error"]["message"] == "An unexpected server error occurred. Please try again later."
        assert data["error"]["details"] is None
    finally:
        app.dependency_overrides.pop(get_sentiment_service, None)


@pytest.mark.asyncio
async def test_openapi_documentation(async_client: AsyncClient) -> None:
    """Verifies that OpenAPI documentation exposes health and sentiment endpoints and all response codes."""
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()

    paths = data.get("paths", {})
    assert "/health" in paths
    assert "/api/v1/sentiment" in paths

    sentiment_post = paths["/api/v1/sentiment"].get("post", {})
    assert "requestBody" in sentiment_post
    responses = sentiment_post.get("responses", {})
    assert "200" in responses
    assert "400" in responses
    assert "422" in responses
    assert "500" in responses
    assert "503" in responses
