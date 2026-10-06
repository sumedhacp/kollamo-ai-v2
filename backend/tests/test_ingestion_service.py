"""Tests for IngestionService with Database Persistence."""

import uuid
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from sqlalchemy import select

from backend.app.models.job import AnalysisJob
from backend.app.models.video import Video
from backend.app.models.comment import Comment
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.youtube_client import (
    YouTubeClient,
    VideoMetadata,
    YouTubeCommentData,
    YouTubeCommentsDisabledError,
)
from backend.tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_ingest_job_comments_success():
    """IngestionService retrieves metadata and comments and persists them in database."""
    async with TestingSessionLocal() as session:
        # Create initial video and job
        video_id = "test_vid_123"
        video = Video(video_id=video_id, title="Initial Title", view_count=0)
        session.add(video)
        await session.flush()

        job = AnalysisJob(
            id=uuid.uuid4(),
            video_id=video_id,
            status="queued",
            sample_size_requested=50,
            sort_mode="top",
            total_comments=0,
            processed_comments=0,
        )
        session.add(job)
        await session.commit()
        job_id = job.id

        # Mock YouTube client
        mock_yt = AsyncMock(spec=YouTubeClient)
        mock_yt.fetch_video_metadata.return_value = VideoMetadata(
            video_id=video_id,
            title="Aavesham Malayalam Movie Review",
            channel_title="Cinema Daddy",
            published_at=datetime.now(timezone.utc),
            view_count=850000,
            like_count=45000,
            comment_count=1200,
        )
        mock_yt.fetch_comments.return_value = [
            YouTubeCommentData(
                comment_id="c1",
                video_id=video_id,
                original_text="ഈ സിനിമ അതിഗംഭീരമാണ്!",
                author_display_name="User Malayalam",
                like_count=25,
                reply_count=2,
                published_at=datetime.now(timezone.utc),
            ),
            YouTubeCommentData(
                comment_id="c2",
                video_id=video_id,
                original_text="Padam nalla vibe aayirunnu bro",
                author_display_name="User Manglish",
                like_count=10,
                reply_count=0,
                published_at=datetime.now(timezone.utc),
            ),
        ]

        ingestion = IngestionService(youtube_client=mock_yt)
        saved_video, saved_comments = await ingestion.ingest_job_comments(session, job_id)

        assert saved_video.title == "Aavesham Malayalam Movie Review"
        assert saved_video.view_count == 850000
        assert len(saved_comments) == 2

        # Verify database records
        comments_result = await session.execute(
            select(Comment).where(Comment.job_id == job_id)
        )
        db_comments = comments_result.scalars().all()
        assert len(db_comments) == 2

        c1 = next(c for c in db_comments if c.comment_id == "c1")
        assert c1.original_text == "ഈ സിനിമ അതിഗംഭീരമാണ്!"
        assert c1.detected_script == "Malayalam"
        assert c1.detected_language in ("ml", "ml-en")

        c2 = next(c for c in db_comments if c.comment_id == "c2")
        assert c2.original_text == "Padam nalla vibe aayirunnu bro"
        assert c2.detected_script == "Latin"

        # Verify job status and total count
        job_result = await session.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        updated_job = job_result.scalars().first()
        assert updated_job.total_comments == 2
        assert updated_job.error_message is None


@pytest.mark.asyncio
async def test_ingest_job_comments_disabled_fails_gracefully():
    """IngestionService sets job to failed status with error message when comments are disabled."""
    async with TestingSessionLocal() as session:
        video_id = "test_vid_disabled"
        video = Video(video_id=video_id, title="Disabled Comments Video", view_count=0)
        session.add(video)
        await session.flush()

        job = AnalysisJob(
            id=uuid.uuid4(),
            video_id=video_id,
            status="queued",
            sample_size_requested=100,
            sort_mode="top",
        )
        session.add(job)
        await session.commit()
        job_id = job.id

        mock_yt = AsyncMock(spec=YouTubeClient)
        mock_yt.fetch_video_metadata.return_value = VideoMetadata(
            video_id=video_id,
            title="Disabled Comments Video",
            channel_title="Creator",
            published_at=datetime.now(timezone.utc),
            view_count=5000,
            like_count=100,
            comment_count=0,
        )
        mock_yt.fetch_comments.side_effect = YouTubeCommentsDisabledError(
            "Comments are disabled on this video."
        )

        ingestion = IngestionService(youtube_client=mock_yt)
        with pytest.raises(YouTubeCommentsDisabledError):
            await ingestion.ingest_job_comments(session, job_id)

        # Check job status in database
        job_result = await session.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        updated_job = job_result.scalars().first()
        assert updated_job.status == "failed"
        assert "Comments are disabled" in updated_job.error_message
