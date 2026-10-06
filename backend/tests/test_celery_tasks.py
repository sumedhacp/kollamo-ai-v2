"""Tests for Celery Background Tasks and Metric Aggregation."""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from backend.app.models.job import AnalysisJob
from backend.app.models.video import Video
from backend.app.models.comment import Comment
from backend.app.models.prediction import Prediction
from backend.app.models.summary_metrics import SummaryMetric
from backend.app.workers.tasks import (
    compute_summary_metrics,
    run_analysis_pipeline,
    process_youtube_analysis_job,
)
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.youtube_client import VideoMetadata, YouTubeCommentData
from backend.tests.conftest import TestingSessionLocal
from ml.data.dataset_loader import SENTIMENT_LABELS


def test_compute_summary_metrics():
    """Verifies percentage rollups and engagement average calculations."""
    job_id = uuid.uuid4()
    c1 = Comment(comment_id="c1", job_id=job_id, original_text="good", like_count=10)
    p1 = Prediction(id=uuid.uuid4(), comment_id="c1", sentiment="positive", confidence=0.9, class_probabilities={})

    c2 = Comment(comment_id="c2", job_id=job_id, original_text="bad", like_count=5)
    p2 = Prediction(id=uuid.uuid4(), comment_id="c2", sentiment="negative", confidence=0.8, class_probabilities={})

    c3 = Comment(comment_id="c3", job_id=job_id, original_text="neutral", like_count=0)
    p3 = Prediction(id=uuid.uuid4(), comment_id="c3", sentiment="neutral", confidence=0.7, class_probabilities={})

    pairs = [(c1, p1), (c2, p2), (c3, p3)]
    metrics = compute_summary_metrics(pairs)

    counts = metrics["sentiment_counts"]
    percentages = metrics["sentiment_percentages"]
    engagement = metrics["engagement_metrics"]

    assert counts["positive"] == 1
    assert counts["negative"] == 1
    assert counts["neutral"] == 1
    assert counts["mixed"] == 0
    assert counts["unsupported"] == 0

    assert percentages["positive"] == pytest.approx(33.33, 0.1)
    assert percentages["negative"] == pytest.approx(33.33, 0.1)
    assert percentages["neutral"] == pytest.approx(33.33, 0.1)

    assert engagement["total_likes"] == 15
    assert engagement["average_likes_per_sentiment"]["positive"] == 10.0
    assert engagement["average_likes_per_sentiment"]["negative"] == 5.0
    assert engagement["average_likes_per_sentiment"]["neutral"] == 0.0


@pytest.mark.asyncio
async def test_run_analysis_pipeline_success():
    """Verifies end-to-end execution of micro-batching and metric creation."""
    async with TestingSessionLocal() as session:
        video_id = "vid_async_test"
        video = Video(video_id=video_id, title="Async Review", view_count=1000)
        session.add(video)
        await session.flush()

        job = AnalysisJob(
            id=uuid.uuid4(),
            video_id=video_id,
            status="queued",
            sample_size_requested=4,
            sort_mode="top",
        )
        session.add(job)
        await session.flush()
        job_id = job.id

        # Insert 4 test comments
        test_texts = [
            "ഈ സിനിമ വളരെ മികച്ചതാണ്, കണ്ടിരിക്കേണ്ടതാണ്",
            "Padam valare bore aayirunnu, total waste",
            "Average padam, not bad but not great",
            "Kidilam acting and direction super",
        ]
        for idx, text in enumerate(test_texts):
            c = Comment(
                comment_id=f"comm_{idx}",
                job_id=job_id,
                video_id=video_id,
                original_text=text,
                author_display_name=f"User {idx}",
                like_count=idx * 5,
            )
            session.add(c)
        await session.commit()

        # Run pipeline with micro-batch size 2
        result = await run_analysis_pipeline(job_id=job_id, session=session, batch_size=2)

        assert result["status"] == "completed"
        assert result["total_comments"] == 4
        assert result["processed_comments"] == 4

        # Verify DB state
        job_db = (
            await session.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
        ).scalars().first()
        assert job_db.status == "completed"
        assert job_db.processed_comments == 4
        assert job_db.completed_at is not None

        # Verify predictions created
        preds = (
            await session.execute(
                select(Prediction).join(Comment).where(Comment.job_id == job_id)
            )
        ).scalars().all()
        assert len(preds) == 4
        for p in preds:
            assert p.sentiment in SENTIMENT_LABELS
            assert 0.0 <= p.confidence <= 1.0

        # Verify SummaryMetric
        summary = (
            await session.execute(
                select(SummaryMetric).where(SummaryMetric.job_id == job_id)
            )
        ).scalars().first()
        assert summary is not None
        assert sum(summary.sentiment_counts.values()) == 4
        assert summary.engagement_metrics["total_likes"] == 30  # 0 + 5 + 10 + 15


@pytest.mark.asyncio
async def test_run_analysis_pipeline_failure_handling():
    """Verifies that unhandled pipeline errors transition job to failed state."""
    async with TestingSessionLocal() as session:
        video_id = "vid_fail_test"
        video = Video(video_id=video_id, title="Fail Video", view_count=0)
        session.add(video)
        await session.flush()

        job = AnalysisJob(
            id=uuid.uuid4(),
            video_id=video_id,
            status="queued",
            sample_size_requested=10,
            sort_mode="top",
        )
        session.add(job)
        await session.commit()
        job_id = job.id

        # Mock IngestionService to raise an error
        mock_ingestion = AsyncMock(spec=IngestionService)
        mock_ingestion.ingest_job_comments.side_effect = RuntimeError("Fatal ingestion failure")

        with pytest.raises(RuntimeError):
            await run_analysis_pipeline(
                job_id=job_id,
                session=session,
                ingestion_service=mock_ingestion,
            )

        # Check job status
        job_db = (
            await session.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
        ).scalars().first()
        assert job_db.status == "failed"
        assert "Fatal ingestion failure" in job_db.error_message


def test_celery_task_invocation():
    """Tests the Celery task wrapper function."""
    with patch("backend.app.workers.tasks.asyncio.run") as mock_run:
        mock_run.return_value = {"status": "completed"}
        task_id = str(uuid.uuid4())
        res = process_youtube_analysis_job(task_id)
        assert res["status"] == "completed"
        assert mock_run.called
