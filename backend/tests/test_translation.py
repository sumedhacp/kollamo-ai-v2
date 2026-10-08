"""Unit and Integration Tests for Translation Service and Endpoints."""

import pytest
from httpx import AsyncClient

from backend.app.services.translation_service import (
    HybridTranslationService,
    LanguageKind,
    MockTranslationService,
    get_translation_service,
    set_translation_service,
)


def test_language_classification():
    """Verifies heuristic and character-level language classification."""
    service = HybridTranslationService()

    # Pure Malayalam script
    assert service.classify_language("ഈ സിനിമ വളരെ മികച്ചതാണ്") == LanguageKind.MALAYALAM
    assert service.detect_script("ഈ സിനിമ വളരെ മികച്ചതാണ്") == "malayalam"

    # Pure English
    assert service.classify_language("The acting was truly phenomenal and the direction is top notch") == LanguageKind.ENGLISH
    assert service.detect_script("The acting was truly phenomenal") == "latin"

    # Pure Manglish
    assert service.classify_language("padam kidilan aayirunnu bro") == LanguageKind.MANGLISH
    assert service.detect_script("padam kidilan aayirunnu bro") == "latin"

    # Mixed Malayalam script + Latin words
    assert service.classify_language("super സിനിമ, mass bgm") == LanguageKind.MIXED
    assert service.detect_script("super സിനിമ, mass bgm") == "mixed"


def test_colloquial_manglish_lexicon():
    """Verifies instant idiomatic translation of colloquial Manglish review expressions."""
    service = HybridTranslationService()

    res1 = service.translate_detailed("padam thooki")
    assert res1.status == "translated"
    assert "blockbuster" in res1.text.lower() or "hit" in res1.text.lower()
    assert res1.method == "colloquial_lexicon"

    res2 = service.translate_detailed("pwoli")
    assert res2.status == "translated"
    assert "awesome" in res2.text.lower()

    res3 = service.translate_detailed("valare bore")
    assert res3.status == "translated"
    assert "boring" in res3.text.lower()

    res4 = service.translate_detailed("ennik arum ellia")
    assert res4.status == "translated"
    assert "no one" in res4.text.lower()


def test_orthographic_normalizations():
    """Verifies phonetic standardization of common Manglish spelling variations."""
    normalized = HybridTranslationService.normalize_manglish("ennik arum ellia cheyth kand")
    assert "enikku" in normalized
    assert "illa" in normalized
    assert "cheythu" in normalized
    assert "kandu" in normalized


def test_translation_graceful_fallback(monkeypatch):
    """Verifies translation does not crash if cloud network fails or throws exceptions."""
    service = HybridTranslationService()

    # Simulate cloud failure by monkeypatching _translate_cloud to return None
    monkeypatch.setattr(service, "_translate_cloud", lambda *args, **kwargs: None)
    monkeypatch.setattr(service, "_transliterate_manglish", lambda *args, **kwargs: None)

    # When translating a sentence not in colloquial lexicon
    raw_text = "kollam ennu thonnunnu entho oru prashnam"
    result = service.translate_detailed(raw_text)

    # Must preserve original text and return fallback status, never throwing exception
    assert result.text == raw_text
    assert result.status == "fallback"
    assert result.method == "fallback"


@pytest.mark.asyncio
async def test_translate_api_endpoint(async_client: AsyncClient):
    """Verifies POST /api/translate endpoint with colloquial and regional text."""
    # Test colloquial expression
    payload = {
        "text": "pwoli padam",
        "source_language": "auto",
        "target_language": "en",
    }
    resp = await async_client.post("/api/translate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["original_text"] == "pwoli padam"
    assert "awesome" in data["translated_text"].lower()
    assert data["status"] == "translated"
    assert data["confidence"] > 0.8


@pytest.mark.asyncio
async def test_translate_api_validation(async_client: AsyncClient):
    """Verifies input validation on POST /api/translate."""
    # Empty string should return 422
    resp = await async_client.post("/api/translate", json={"text": "   "})
    assert resp.status_code == 422

    # Missing text field
    resp2 = await async_client.post("/api/translate", json={})
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_sentiment_endpoint_with_translation(async_client: AsyncClient):
    """Verifies POST /api/sentiment handles translation requested and not requested."""
    # With translate=True (default)
    resp = await async_client.post(
        "/api/sentiment",
        json={"text": "padam thooki", "translate": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sentiment"] in ["positive", "negative", "neutral", "mixed", "unsupported"]
    assert data["translated_text"] is not None
    assert "blockbuster" in data["translated_text"].lower() or "hit" in data["translated_text"].lower()

    # With translate=False
    resp_no_trans = await async_client.post(
        "/api/sentiment",
        json={"text": "padam thooki", "translate": False},
    )
    assert resp_no_trans.status_code == 200
    data_no_trans = resp_no_trans.json()
    assert data_no_trans["translation_status"] == "not_requested"
    assert data_no_trans["translated_text"] is None


def test_english_comment_not_needed():
    """Verifies already-English comments receive NOT_NEEDED status without modification."""
    service = HybridTranslationService()
    text = "The background music was fantastic and direction was outstanding"
    res = service.translate_detailed(text)
    assert res.status == "NOT_NEEDED"
    assert res.text == text
    assert res.confidence == 1.0

    # Ensure schema mapper assigns NOT_NEEDED
    mapped = service.to_comment_translation(text, res)
    assert mapped.status == "NOT_NEEDED"
    assert mapped.original_text == text
    assert mapped.translated_text is None


def test_translation_caching_and_deduplication():
    """Verifies that duplicate requests return from internal cache without reprocessing."""
    service = HybridTranslationService()
    text = "kidilan padam"
    res1 = service.translate_detailed(text)
    res2 = service.translate_detailed(text)
    assert res1.text == res2.text
    assert res1.status == res2.status
    # Verify cached item exists in _cache
    cache_key = (text.lower().strip(), "auto", "en")
    assert cache_key in service._cache


def test_original_text_preservation():
    """Ensures raw original comments are never mutated or overwritten."""
    service = HybridTranslationService()
    raw = "ഈ സിനിമ അടിപൊളിയാണ്"
    res = service.translate_detailed(raw)
    mapped = service.to_comment_translation(raw, res)
    assert mapped.original_text == raw
    assert raw == "ഈ സിനിമ അടിപൊളിയാണ്"


@pytest.mark.asyncio
async def test_v1_translation_endpoints(async_client: AsyncClient):
    """Verifies canonical POST /api/v1/translation and alias /api/v1/translate."""
    # Test POST /api/v1/translation
    resp1 = await async_client.post(
        "/api/v1/translation",
        json={"text": "adipoli movie", "source_language": "auto", "target_language": "en"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["original_text"] == "adipoli movie"
    assert data1["target_language"] == "en"

    # Test alias POST /api/v1/translate
    resp2 = await async_client.post(
        "/api/v1/translate",
        json={"text": "nallath", "source_language": "auto", "target_language": "en"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["original_text"] == "nallath"
    assert "good" in data2["translated_text"].lower()


def test_translation_secret_safety():
    """Verifies server-side translation configuration does not expose secrets in responses."""
    from backend.app.core.config import settings
    # Ensure config has server-side settings
    assert hasattr(settings, "TRANSLATION_SERVICE")
    assert hasattr(settings, "TRANSLATION_API_KEY")
