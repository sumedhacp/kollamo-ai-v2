"""Service for Analysis Jobs and Video Management."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.models.job import AnalysisJob
from backend.app.models.video import Video
from backend.app.models.comment import Comment
from backend.app.models.summary_metrics import SummaryMetric
from backend.app.schemas.analyze import (
    AnalyzeRequest,
    JobStatusResponse,
    JobSummary,
    VideoSummary,
    SentimentCounts,
    SentimentPercentages,
    EngagementMetrics,
    CommentItem,
    extract_youtube_video_id,
)


class JobService:
    """Handles analysis job creation, status querying, and telemetry formatting."""

    @staticmethod
    async def create_analysis_job(
        db: AsyncSession, request: AnalyzeRequest
    ) -> AnalysisJob:
        """Creates a new AnalysisJob and associated provisional Video record."""
        video_id = extract_youtube_video_id(request.youtube_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Check or create Video record
        stmt = select(Video).where(Video.video_id == video_id)
        result = await db.execute(stmt)
        video = result.scalars().first()

        if not video:
            video = Video(
                video_id=video_id,
                title=f"YouTube Video ({video_id})",
                channel_title="YouTube Channel",
                view_count=0,
            )
            db.add(video)
            await db.flush()

        sample_size = 0 if request.sample_size == "all" else int(request.sample_size)

        job = AnalysisJob(
            id=uuid.uuid4(),
            video_id=video_id,
            status="queued",
            sample_size_requested=sample_size,
            sort_mode=request.sort_mode,
            total_comments=0,
            processed_comments=0,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"Created analysis job {job.id} for video {video_id}")
        return job

    @staticmethod
    async def get_job_by_id(
        db: AsyncSession, job_id: uuid.UUID
    ) -> Optional[AnalysisJob]:
        """Retrieves an analysis job by UUID with eager-loaded relations."""
        stmt = (
            select(AnalysisJob)
            .options(
                selectinload(AnalysisJob.video),
                selectinload(AnalysisJob.summary_metric),
                selectinload(AnalysisJob.comments).selectinload(Comment.prediction),
            )
            .where(AnalysisJob.id == job_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def format_job_status_response(job: AnalysisJob) -> JobStatusResponse:
        """Formats an AnalysisJob ORM entity into JobStatusResponse schema."""
        progress = (
            float(job.processed_comments) / float(job.total_comments)
            if job.total_comments and job.total_comments > 0
            else 0.0
        )
        progress = min(max(progress, 0.0), 1.0)

        video_summary: Optional[VideoSummary] = None
        if job.video:
            video_summary = VideoSummary(
                video_id=job.video.video_id,
                title=job.video.title,
                channel_title=job.video.channel_title,
                view_count=job.video.view_count,
            )

        job_summary: Optional[JobSummary] = None
        if job.summary_metric:
            job_summary = JobSummary(
                sentiment_counts=SentimentCounts(**job.summary_metric.sentiment_counts),
                sentiment_percentages=SentimentPercentages(
                    **job.summary_metric.sentiment_percentages
                ),
                engagement_metrics=EngagementMetrics(
                    **job.summary_metric.engagement_metrics
                ),
            )

        comments_list: Optional[List[CommentItem]] = None
        if job.comments:
            comments_list = []
            for c in job.comments:
                sentiment = c.prediction.sentiment if c.prediction else "neutral"
                confidence = c.prediction.confidence if c.prediction else 0.0
                comments_list.append(
                    CommentItem(
                        comment_id=c.comment_id,
                        author_display_name=c.author_display_name or "Anonymous",
                        like_count=c.like_count or 0,
                        reply_count=c.reply_count or 0,
                        original_text=c.original_text,
                        detected_language=c.detected_language or "unknown",
                        detected_script=c.detected_script or "Unknown",
                        sentiment=sentiment,
                        confidence=confidence,
                        translated_text=c.translated_text,
                        published_at=c.published_at,
                    )
                )

        return JobStatusResponse(
            job_id=str(job.id),
            status=job.status,
            progress=progress,
            processed_comments=job.processed_comments,
            total_comments=job.total_comments,
            video=video_summary,
            summary=job_summary,
            comments=comments_list,
            created_at=job.created_at,
            completed_at=job.completed_at,
            error=job.error_message,
        )
