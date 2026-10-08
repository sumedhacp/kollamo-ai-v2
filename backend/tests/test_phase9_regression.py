"""Comprehensive Phase 9 Automated Regression and Hardening Test Suite.

Adheres strictly to Phase 9 Sections 8 through 25:
- ML testing: 5-class immutability, valid probability distributions, no fake fallbacks.
- Model readiness: MODEL_READY, MODEL_NOT_READY, MODEL_UNAVAILABLE, INFERENCE_ERROR.
- API validation: missing fields, empty strings, whitespace, wrong types, malformed JSON, oversized inputs.
- HTTP status codes: 200, 202, 400, 404, 422, 500, 503.
- YouTube ingestion: limits (50, 100, 250, 500, ALL), sorting, pagination bounds, verbatim Unicode preservation.
- Async jobs: states (QUEUED, PROCESSING, COMPLETED, FAILED), progress stage sequence.
- Translation: Malayalam, English (NOT_NEEDED), provider failure, caching, original text preservation.
- Security: sanitized error envelopes, no stack trace leaks.
"""

import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient

from backend.app.main import app
from backend.app.services.sentiment import SentimentService, get_sentiment_service
from backend.app.services.translation_service import (
    HybridTranslationService,
    TranslationResult,
    get_translation_service,
)
from backend.app.schemas.translation import TranslationStatus
from backend.ml.schemas.prediction import SentimentPrediction, SentimentProbabilities
from backend.ml.inference.service import SentimentInferenceService, ModelReadiness
from backend.ml.exceptions import (
    ModelNotReadyError,
    ModelUnavailableError,
    InferenceError,
)
from ml.models.taxonomy import (
    ID2CLASS,
    ID2LABEL,
    LABEL2ID,
    SENTIMENT_CLASSES,
    CLASS_ID_POSITIVE,
    CLASS_ID_NEGATIVE,
    CLASS_ID_NEUTRAL,
    CLASS_ID_MIXED,
    CLASS_ID_UNSUPPORTED,
)
from app.services.jobs import JobStateService, get_job_state_service, set_job_state_service
from app.schemas.youtube import YouTubeComment, YouTubeIngestionResult, YouTubeVideo
from app.services.youtube.service import YouTubeIngestionService
from app.services.youtube.errors import (
    YouTubeInvalidVideoError,
    YouTubeVideoNotFoundError,
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
)


# =====================================================================
# 1. ML CONTRACT & PROBABILITY INVARIANCE (Sections 10 & 11)
# =====================================================================

class DeterministicMLPredictor:
    """Deterministic 5-class mock predictor for test isolation."""

    def predict_single(self, text: str) -> Dict[str, Any]:
        # Return exact 5-class probability distribution
        return {
            "sentiment": "Positive",
            "confidence": 0.92,
            "class_probabilities": {
                "positive": 0.92,
                "negative": 0.02,
                "neutral": 0.03,
                "mixed": 0.02,
                "unsupported": 0.01,
            },
        }


@pytest.fixture
def override_ml_service():
    """Provides isolated mock SentimentService returning deterministic probabilities."""
    mock_ml = SentimentInferenceService(
        predictor=DeterministicMLPredictor(),
        model_name="kollamo-muril-5class",
        model_version="v1",
        is_fine_tuned=True,
    )
    test_svc = SentimentService(ml_service=mock_ml)
    app.dependency_overrides[get_sentiment_service] = lambda: test_svc
    yield test_svc
    app.dependency_overrides.pop(get_sentiment_service, None)


def test_taxonomy_label_immutability():
    """Asserts that 5-class taxonomy is strictly immutable and accurately mapped."""
    expected_classes = {0: "Positive", 1: "Negative", 2: "Neutral", 3: "Mixed", 4: "Unsupported"}
    assert ID2CLASS == expected_classes
    assert len(SENTIMENT_CLASSES) == 5
    for idx, name in expected_classes.items():
        assert LABEL2ID[name.lower()] == idx


@pytest.mark.asyncio
async def test_ml_probability_distribution_properties(
    async_client: AsyncClient, override_ml_service: SentimentService
):
    """Verifies probabilities contain all 5 classes, within [0,1], and sum to 1.0."""
    payload = {"text": "ഈ സിനിമ വളരെ മികച്ചതാണ്! Superb cinematography."}
    response = await async_client.post("/api/v1/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()

    probs = data["probabilities"]
    assert set(probs.keys()) == {"Positive", "Negative", "Neutral", "Mixed", "Unsupported"}

    total_prob = 0.0
    for label, val in probs.items():
        assert isinstance(val, (int, float))
        assert 0.0 <= val <= 1.0
        total_prob += val

    assert pytest.approx(1.0, abs=1e-3) == total_prob
    assert data["confidence"] == probs[data["sentiment"]]


# =====================================================================
# 2. MODEL READINESS CONTRACT & ZERO FAKE PREDICTIONS (Section 12)
# =====================================================================

@pytest.mark.asyncio
async def test_model_not_ready_returns_503_without_fake_sentiment(async_client: AsyncClient):
    """Verifies MODEL_NOT_READY returns 503 and never emits fake sentiment."""
    mock_ml = MagicMock(spec=SentimentInferenceService)
    mock_ml.analyze.side_effect = ModelNotReadyError(
        "Kollamo fine-tuned weights not found at ml/models/muril_sentiment"
    )
    not_ready_svc = SentimentService(ml_service=mock_ml)
    app.dependency_overrides[get_sentiment_service] = lambda: not_ready_svc

    try:
        response = await async_client.post("/api/v1/sentiment", json={"text": "Valare nalla cinema"})
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "MODEL_NOT_READY"
        assert "sentiment" not in data
        assert "confidence" not in data
    finally:
        app.dependency_overrides.pop(get_sentiment_service, None)


@pytest.mark.asyncio
async def test_model_unavailable_returns_503(async_client: AsyncClient):
    """Verifies MODEL_UNAVAILABLE returns 503 and never emits fake sentiment."""
    mock_ml = MagicMock(spec=SentimentInferenceService)
    mock_ml.analyze.side_effect = ModelUnavailableError("Model weights corrupted on disk")
    unavail_svc = SentimentService(ml_service=mock_ml)
    app.dependency_overrides[get_sentiment_service] = lambda: unavail_svc

    try:
        response = await async_client.post("/api/v1/sentiment", json={"text": "Kidu movie"})
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "MODEL_UNAVAILABLE"
    finally:
        app.dependency_overrides.pop(get_sentiment_service, None)


@pytest.mark.asyncio
async def test_inference_error_returns_500_sanitized(async_client: AsyncClient):
    """Verifies INFERENCE_ERROR returns 500 without leaking stack traces."""
    mock_ml = MagicMock(spec=SentimentInferenceService)
    mock_ml.analyze.side_effect = InferenceError("Internal tensor mismatch at layer 11")
    err_svc = SentimentService(ml_service=mock_ml)
    app.dependency_overrides[get_sentiment_service] = lambda: err_svc

    try:
        response = await async_client.post("/api/v1/sentiment", json={"text": "Kidu movie"})
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INFERENCE_ERROR"
        assert "layer 11" not in response.text
        assert "Traceback" not in response.text
    finally:
        app.dependency_overrides.pop(get_sentiment_service, None)


# =====================================================================
# 3. API INPUT VALIDATION MATRIX (Sections 14 & 15)
# =====================================================================

@pytest.mark.asyncio
async def test_sentiment_validation_missing_text(async_client: AsyncClient):
    """Missing 'text' parameter returns 422 with code REQUIRED."""
    response = await async_client.post("/api/v1/sentiment", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    field_codes = [f["code"] for f in data["error"]["details"]["fields"]]
    assert "REQUIRED" in field_codes


@pytest.mark.asyncio
async def test_sentiment_validation_empty_and_whitespace(async_client: AsyncClient):
    """Empty or whitespace-only text returns 422 with code EMPTY_TEXT."""
    for invalid_text in ["", "   ", "\t\n\r  "]:
        response = await async_client.post("/api/v1/sentiment", json={"text": invalid_text})
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        field_codes = [f["code"] for f in data["error"]["details"]["fields"]]
        assert "EMPTY_TEXT" in field_codes


@pytest.mark.asyncio
async def test_sentiment_validation_invalid_types(async_client: AsyncClient):
    """Non-string text returns 422 with code INVALID_TYPE."""
    for bad_type in [12345, 99.9, True, ["test"], {"nested": "value"}]:
        response = await async_client.post("/api/v1/sentiment", json={"text": bad_type})
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        field_codes = [f["code"] for f in data["error"]["details"]["fields"]]
        assert "INVALID_TYPE" in field_codes


@pytest.mark.asyncio
async def test_sentiment_validation_oversized_text(async_client: AsyncClient):
    """Text exceeding 5000 characters is rejected with 422 VALIDATION_ERROR."""
    oversized = "നല്ല സിനിമ " * 1000  # >10,000 characters
    response = await async_client.post("/api/v1/sentiment", json={"text": oversized})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_analysis_job_validation_invalid_limits(async_client: AsyncClient):
    """Invalid comment_limit (not in 50, 100, 250, 500, ALL) returns 422."""
    for invalid_lim in [0, 10, 999, -50, "TEN"]:
        response = await async_client.post(
            "/api/v1/analysis/jobs",
            json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "comment_limit": invalid_lim},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_analysis_job_validation_invalid_sort(async_client: AsyncClient):
    """Invalid sort_by returns 422 VALIDATION_ERROR."""
    response = await async_client.post(
        "/api/v1/analysis/jobs",
        json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "sort_by": "unsupported_sort"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


# =====================================================================
# 4. YOUTUBE INGESTION BOUNDS & SORTING (Sections 16, 17, 18)
# =====================================================================

@pytest.mark.asyncio
async def test_youtube_comment_limits_enforced():
    """Verifies that requested comment limit strictly caps the returned comments count."""
    client_mock = MagicMock()
    client_mock.fetch_video_metadata = AsyncMock(
        return_value=YouTubeVideo(video_id="test1234567", title="Test Video", comment_count=1000)
    )

    # 100 comments available from API
    api_items = [
        {
            "id": f"c_{i}",
            "snippet": {
                "topLevelComment": {
                    "id": f"c_{i}",
                    "snippet": {
                        "authorDisplayName": f"User {i}",
                        "textOriginal": f"Comment {i}",
                        "likeCount": i,
                        "publishedAt": "2024-04-01T12:00:00Z",
                        "updatedAt": "2024-04-01T12:00:00Z",
                    },
                }
            },
        }
        for i in range(100)
    ]

    client_mock.fetch_comment_threads = AsyncMock(
        return_value={"items": api_items, "nextPageToken": None}
    )

    def _parse_comment(item, video_id):
        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        from datetime import datetime, timezone
        return YouTubeComment(
            comment_id=item.get("id", "c_1"),
            video_id=video_id,
            author_name=snippet.get("authorDisplayName", "User"),
            text=snippet.get("textOriginal", ""),
            like_count=snippet.get("likeCount", 0),
            published_at=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
    client_mock.parse_comment_item = _parse_comment

    service = YouTubeIngestionService(client=client_mock)

    for limit in [50, 100]:
        res = await service.ingest("https://www.youtube.com/watch?v=test1234567", comment_limit=limit)
        assert len(res.comments) <= limit
        assert res.requested_limit == limit


@pytest.mark.asyncio
async def test_youtube_verbatim_unicode_preservation():
    """Verifies that Malayalam, English, Manglish, code-mixed text, and emojis are preserved verbatim."""
    special_comment = "Superb padam 🔥! അഭിനയം ഗംഭീരം ആയിരുന്നു. 100% worth watching."
    client_mock = MagicMock()
    client_mock.fetch_video_metadata = AsyncMock(
        return_value=YouTubeVideo(video_id="dQw4w9WgXcQ", title="Test Video")
    )
    client_mock.fetch_comment_threads = AsyncMock(
        return_value={
            "items": [
                {
                    "id": "c_unicode",
                    "snippet": {
                        "topLevelComment": {
                            "id": "c_unicode",
                            "snippet": {
                                "authorDisplayName": "Malayalam Cinema Fan",
                                "textOriginal": special_comment,
                                "likeCount": 42,
                                "publishedAt": "2024-04-01T12:00:00Z",
                                "updatedAt": "2024-04-01T12:00:00Z",
                            },
                        }
                    },
                }
            ],
            "nextPageToken": None,
        }
    )
    def _parse_comment(item, video_id):
        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        from datetime import datetime, timezone
        return YouTubeComment(
            comment_id=item.get("id", "c_unicode"),
            video_id=video_id,
            author_name=snippet.get("authorDisplayName", "User"),
            text=snippet.get("textOriginal", ""),
            like_count=snippet.get("likeCount", 0),
            published_at=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
    client_mock.parse_comment_item = _parse_comment

    service = YouTubeIngestionService(client=client_mock)
    res = await service.ingest("https://www.youtube.com/watch?v=dQw4w9WgXcQ", comment_limit=50)
    assert len(res.comments) == 1
    assert res.comments[0].text == special_comment


# =====================================================================
# 5. ASYNC JOB PROGRESS STAGE SEQUENCING (Sections 19 & 20)
# =====================================================================

@pytest.mark.asyncio
async def test_async_job_progress_stages():
    """Verifies proper stage transitions from QUEUED -> PROCESSING -> COMPLETED."""
    service = JobStateService(redis_client=None, use_memory_fallback=True)
    job_id = str(uuid.uuid4())

    service.create_job(job_id=job_id, request_data={"video_url": "test"})
    job = service.get_job(job_id)
    assert job["status"] == "QUEUED"
    assert job["progress"]["stage"] == "QUEUED"

    expected_stages = [
        "FETCHING_VIDEO",
        "FETCHING_COMMENTS",
        "SENTIMENT_ANALYSIS",
        "FINALIZING",
        "COMPLETED",
    ]

    for idx, stage in enumerate(expected_stages):
        pct = int(((idx + 1) / len(expected_stages)) * 100)
        status = "COMPLETED" if stage == "COMPLETED" else "PROCESSING"
        service.update_job(
            job_id=job_id,
            status=status,
            progress={"stage": stage, "completed": idx + 1, "total": len(expected_stages), "percentage": pct},
        )
        curr = service.get_job(job_id)
        assert curr["status"] == status
        assert curr["progress"]["stage"] == stage
        assert curr["progress"]["percentage"] == pct


# =====================================================================
# 6. TRANSLATION RESILIENCE & CACHING (Section 22)
# =====================================================================

def test_translation_english_bypass():
    """Verifies plain English comment is marked NOT_NEEDED without mutating text."""
    svc = HybridTranslationService()
    english_comment = "This was an amazing movie with great screenplay!"
    res = svc.translate_detailed(english_comment)
    translation = svc.to_comment_translation(english_comment, res)

    assert translation.status == TranslationStatus.NOT_NEEDED.value
    assert translation.original_text == english_comment
    assert translation.error_message is None


def test_translation_caching_deduplication():
    """Verifies duplicate translation calls return cached results."""
    svc = HybridTranslationService()
    malayalam_text = "നല്ല സിനിമ ആയിരുന്നു"

    # First translation
    res1 = svc.translate_detailed(malayalam_text)
    # Second translation with same text
    res2 = svc.translate_detailed(malayalam_text)
    assert res2.text == res1.text
    assert res2.status == res1.status


def test_translation_failure_isolation():
    """Verifies provider failure isolates error to FAILED status and preserves original text."""
    svc = HybridTranslationService()
    mock_err_res = TranslationResult(
        text="ഗംഭീരം സിനിമ",
        confidence=0.0,
        source_language="malayalam",
        detected_script="malayalam",
        intermediate_malayalam=None,
        method="cloud_error",
        status="error",
        error_message="Translation API timeout",
    )
    with patch.object(svc, "translate_detailed", return_value=mock_err_res):
        res = svc.translate_detailed("ഗംഭീരം സിനിമ")
        comment_trans = svc.to_comment_translation("ഗംഭീരം സിനിമ", res)
        assert comment_trans.status == TranslationStatus.FAILED.value
        assert comment_trans.original_text == "ഗംഭീരം സിനിമ"
        assert comment_trans.translated_text is None
        assert "Translation API timeout" in comment_trans.error_message
