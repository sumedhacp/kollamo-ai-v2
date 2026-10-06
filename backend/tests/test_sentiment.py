"""Tests for Single-Comment Sentiment Analysis Endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sentiment_valid_malayalam(async_client: AsyncClient) -> None:
    """Tests POST /api/sentiment with valid Malayalam script comment."""
    payload = {
        "text": "ഈ സിനിമ വളരെ മികച്ചതാണ്, അഭിനയം ഗംഭീരം!",
        "translate": False,
    }
    response = await async_client.post("/api/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["detected_script"] == "Malayalam"
    assert data["detected_language"] in ("ml", "ml-en")
    assert data["sentiment"] in ("positive", "negative", "neutral", "mixed", "unsupported")
    assert 0.0 <= data["confidence"] <= 1.0

    probs = data["class_probabilities"]
    assert set(probs.keys()) == {"positive", "negative", "neutral", "mixed", "unsupported"}
    total_prob = sum(probs.values())
    assert 0.99 <= total_prob <= 1.01
    assert data["translation_status"] == "not_requested"


@pytest.mark.asyncio
async def test_sentiment_valid_manglish(async_client: AsyncClient) -> None:
    """Tests POST /api/sentiment with Manglish (Romanized Malayalam) comment."""
    payload = {
        "text": "Padam kidilan aayirunnu, super directing!",
        "translate": True,
    }
    response = await async_client.post("/api/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_text"] == payload["text"]
    assert data["detected_script"] == "Latin"
    assert data["sentiment"] in ("positive", "negative", "neutral", "mixed", "unsupported")
    assert 0.0 <= data["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_sentiment_empty_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that empty string is rejected with 422 and structured error envelope."""
    payload = {"text": ""}
    response = await async_client.post("/api/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]


@pytest.mark.asyncio
async def test_sentiment_whitespace_only_rejected(async_client: AsyncClient) -> None:
    """Verifies that whitespace-only text is rejected with 422."""
    payload = {"text": "     \n\t   "}
    response = await async_client.post("/api/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_oversized_text_rejected(async_client: AsyncClient) -> None:
    """Verifies that text exceeding 5000 characters is rejected with 422."""
    oversized = "നല്ല സിനിമ " * 600  # ~7200 characters
    payload = {"text": oversized}
    response = await async_client.post("/api/sentiment", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_sentiment_malformed_payload_rejected(async_client: AsyncClient) -> None:
    """Verifies that invalid payload types or non-JSON body are rejected with 422."""
    response = await async_client.post(
        "/api/sentiment",
        content="not a json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
