"""Tests for Celery Background Task 'process_analysis_job' (Phase 5)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.schemas.youtube import YouTubeComment, YouTubeIngestionResult, YouTubeVideo
from app.services.jobs import JobStateService, get_job_state_service, set_job_state_service
from app.services.youtube.errors import (
    YouTubeCommentsDisabledError,
    YouTubeInvalidVideoError,
    YouTubeQuotaExceededError,
)
from app.workers.tasks import process_analysis_job
from backend.ml.inference.service import ModelReadiness
from backend.ml.schemas.prediction import SentimentPrediction, SentimentProbabilities


@pytest.fixture
def fresh_job_service() -> JobStateService:
    """Provides a fresh isolated in-memory JobStateService."""
    service = JobStateService(redis_client=None, use_memory_fallback=True)
    service.clear()
    set_job_state_service(service)
    yield service
    set_job_state_service(None)


def test_process_analysis_job_success(fresh_job_service: JobStateService) -> None:
    """Verifies end-to-end task execution: 3 comments -> 3 predictions -> COMPLETED."""
    job_id = str(uuid.uuid4())
    request_data = {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "comment_limit": 100,
        "sort_by": "newest",
    }
    fresh_job_service.create_job(job_id=job_id, request_data=request_data)

    # 1. Mock Video & Comments
    mock_video = YouTubeVideo(
        video_id="dQw4w9WgXcQ",
        title="Sample Video",
        channel_title="Sample Channel",
        view_count=50000,
    )
    mock_comments = [
        YouTubeComment(
            comment_id="c1",
            video_id="dQw4w9WgXcQ",
            author_name="User1",
            text="ഈ സിനിമ വളരെ മികച്ചതാണ്! Superb direction.",
            like_count=10,
        ),
        YouTubeComment(
            comment_id="c2",
            video_id="dQw4w9WgXcQ",
            author_name="User2",
            text="Very bad movie, total waste of time.",
            like_count=2,
        ),
        YouTubeComment(
            comment_id="c3",
            video_id="dQw4w9WgXcQ",
            author_name="User3",
            text="Nalla padam, one time watchable.",
            like_count=5,
        ),
    ]
    mock_ingest_result = YouTubeIngestionResult(
        video=mock_video,
        comments=mock_comments,
        requested_limit=100,
        returned_count=3,
        sort_by="newest",
    )

    # 2. Mock Prediction
    def mock_analyze(text: str) -> SentimentPrediction:
        probs = SentimentProbabilities(
            Positive=0.8 if "മികച്ചതാണ്" in text or "Nalla" in text else 0.1,
            Negative=0.8 if "bad" in text else 0.1,
            Neutral=0.05,
            Mixed=0.03,
            Unsupported=0.02,
        )
        sentiment = "Positive" if "മികച്ചതാണ്" in text or "Nalla" in text else "Negative"
        return SentimentPrediction(
            original_text=text,
            sentiment=sentiment,
            confidence=0.8,
            probabilities=probs,
            model_name="kollamo-muril-5class",
            model_version="v1",
        )

    # 3. Patch Services
    with patch("app.services.sentiment.SentimentService.get_instance") as mock_sent_svc_get, \
         patch("app.services.youtube.service.YouTubeIngestionService.ingest", new_callable=AsyncMock) as mock_ingest:

        mock_sent_service = MagicMock()
        mock_sent_service.get_model_readiness.return_value = ModelReadiness(
            status="MODEL_READY", is_ready=True
        )
        mock_sent_service.ml_service.model_name = "kollamo-muril-5class"
        mock_sent_service.ml_service.model_version = "v1"
        mock_sent_service.ml_service.analyze.side_effect = mock_analyze
        mock_sent_svc_get.return_value = mock_sent_service

        mock_ingest.return_value = mock_ingest_result

        # Execute task
        res = process_analysis_job(job_id=job_id, request_data=request_data)

        assert res["status"] == "COMPLETED"
        job = fresh_job_service.get_job(job_id)
        assert job["status"] == "COMPLETED"
        assert job["error"] is None

        # Verify progress reaches 100%
        progress = job["progress"]
        assert progress["stage"] == "COMPLETED"
        assert progress["completed"] == 3
        assert progress["total"] == 3
        assert progress["percentage"] == 100

        # Verify result contains normalized structure
        result = job["result"]
        assert result["total_comments"] == 3
        assert result["processed_comments"] == 3
        assert len(result["comments"]) == 3
        assert result["comments"][0]["sentiment"] == "Positive"
        assert result["comments"][1]["sentiment"] == "Negative"
        assert result["comments"][2]["sentiment"] == "Positive"


def test_process_analysis_job_model_not_ready(fresh_job_service: JobStateService) -> None:
    """Verifies that MODEL_NOT_READY fails job clearly without generating fake sentiment."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    with patch("app.services.sentiment.SentimentService.get_instance") as mock_sent_svc_get:
        mock_sent_service = MagicMock()
        mock_sent_service.get_model_readiness.return_value = ModelReadiness(
            status="MODEL_NOT_READY", is_ready=False
        )
        mock_sent_svc_get.return_value = mock_sent_service

        res = process_analysis_job(job_id=job_id, request_data={"video_url": "test"})

        assert res["status"] == "FAILED"
        job = fresh_job_service.get_job(job_id)
        assert job["status"] == "FAILED"
        assert job["error"]["code"] == "MODEL_NOT_READY"
        assert job["result"] is None


def test_process_analysis_job_youtube_error(fresh_job_service: JobStateService) -> None:
    """Verifies that YouTube errors transition job to FAILED without retrying."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    with patch("app.services.sentiment.SentimentService.get_instance") as mock_sent_svc_get, \
         patch("app.services.youtube.service.YouTubeIngestionService.ingest", new_callable=AsyncMock) as mock_ingest:

        mock_sent_service = MagicMock()
        mock_sent_service.get_model_readiness.return_value = ModelReadiness(
            status="MODEL_READY", is_ready=True
        )
        mock_sent_svc_get.return_value = mock_sent_service

        mock_ingest.side_effect = YouTubeInvalidVideoError("Invalid video ID format")

        res = process_analysis_job(job_id=job_id, request_data={"video_url": "test"})

        assert res["status"] == "FAILED"
        job = fresh_job_service.get_job(job_id)
        assert job["status"] == "FAILED"
        assert job["error"]["code"] == "YOUTUBE_INVALID_VIDEO"
        assert job["result"] is None


def test_process_analysis_job_comments_disabled(fresh_job_service: JobStateService) -> None:
    """Verifies that disabled comments error marks job FAILED."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    with patch("app.services.sentiment.SentimentService.get_instance") as mock_sent_svc_get, \
         patch("app.services.youtube.service.YouTubeIngestionService.ingest", new_callable=AsyncMock) as mock_ingest:

        mock_sent_service = MagicMock()
        mock_sent_service.get_model_readiness.return_value = ModelReadiness(
            status="MODEL_READY", is_ready=True
        )
        mock_sent_svc_get.return_value = mock_sent_service

        mock_ingest.side_effect = YouTubeCommentsDisabledError("Comments are disabled for this video")

        res = process_analysis_job(job_id=job_id, request_data={"video_url": "test"})

        assert res["status"] == "FAILED"
        job = fresh_job_service.get_job(job_id)
        assert job["status"] == "FAILED"
        assert job["error"]["code"] == "YOUTUBE_COMMENTS_DISABLED"


def test_process_analysis_job_zero_comments(fresh_job_service: JobStateService) -> None:
    """Verifies that a video with zero comments completes with an empty list."""
    job_id = str(uuid.uuid4())
    fresh_job_service.create_job(job_id=job_id, request_data={"video_url": "test"})

    mock_video = YouTubeVideo(video_id="vid_zero", title="Empty Video")
    mock_ingest_result = YouTubeIngestionResult(
        video=mock_video,
        comments=[],
        requested_limit=100,
        returned_count=0,
        sort_by="newest",
    )

    with patch("app.services.sentiment.SentimentService.get_instance") as mock_sent_svc_get, \
         patch("app.services.youtube.service.YouTubeIngestionService.ingest", new_callable=AsyncMock) as mock_ingest:

        mock_sent_service = MagicMock()
        mock_sent_service.get_model_readiness.return_value = ModelReadiness(
            status="MODEL_READY", is_ready=True
        )
        mock_sent_service.ml_service.model_name = "kollamo-muril-5class"
        mock_sent_service.ml_service.model_version = "v1"
        mock_sent_svc_get.return_value = mock_sent_service

        mock_ingest.return_value = mock_ingest_result

        res = process_analysis_job(job_id=job_id, request_data={"video_url": "test"})

        assert res["status"] == "COMPLETED"
        job = fresh_job_service.get_job(job_id)
        assert job["status"] == "COMPLETED"
        assert job["result"]["total_comments"] == 0
        assert job["result"]["comments"] == []
