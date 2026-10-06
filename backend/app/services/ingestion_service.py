"""YouTube Comment Ingestion Service for Kollamo.ai."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.models.job import AnalysisJob
from backend.app.models.video import Video
from backend.app.models.comment import Comment
from backend.app.services.youtube_client import (
    YouTubeClient,
    YouTubeAPIError,
    YouTubeVideoNotFoundError,
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
    YouTubeAuthError,
    YouTubeCommentData,
    VideoMetadata,
)
from ml.preprocessing.detector import analyze_script_and_language


class IngestionService:
    """Orchestrates YouTube video metadata and comment ingestion into PostgreSQL."""

    def __init__(self, youtube_client: Optional[YouTubeClient] = None):
        self.youtube_client = youtube_client or YouTubeClient()

    async def ingest_job_comments(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
    ) -> Tuple[Video, List[Comment]]:
        """Executes comment thread retrieval and persists records to database."""
        # Retrieve target job
        job_stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
        job_result = await db.execute(job_stmt)
        job = job_result.scalars().first()

        if not job:
            raise ValueError(f"Analysis job with ID {job_id} not found.")

        if not job.video_id:
            raise ValueError(f"Job {job_id} has no associated video_id.")

        logger.info(f"Starting ingestion for job {job.id} (video: {job.video_id})")
        job.status = "running"
        await db.commit()

        try:
            # 1. Fetch official YouTube video metadata
            video_meta: VideoMetadata = await self.youtube_client.fetch_video_metadata(job.video_id)

            # Update or create Video record
            vid_stmt = select(Video).where(Video.video_id == job.video_id)
            vid_result = await db.execute(vid_stmt)
            video = vid_result.scalars().first()

            if not video:
                video = Video(
                    video_id=video_meta.video_id,
                    title=video_meta.title,
                    channel_title=video_meta.channel_title,
                    published_at=video_meta.published_at,
                    view_count=video_meta.view_count,
                )
                db.add(video)
            else:
                video.title = video_meta.title
                video.channel_title = video_meta.channel_title
                video.published_at = video_meta.published_at
                video.view_count = video_meta.view_count

            await db.flush()

            # 2. Fetch comments with pagination up to requested sample size
            sample_size = None if job.sample_size_requested == 0 else job.sample_size_requested
            raw_comments: List[YouTubeCommentData] = await self.youtube_client.fetch_comments(
                video_id=job.video_id,
                sample_size=sample_size,
                sort_mode=job.sort_mode,
            )

            # 3. Process script detection and persist Comments
            saved_comments: List[Comment] = []
            for item in raw_comments:
                script_info = analyze_script_and_language(item.original_text)

                comment_entity = Comment(
                    comment_id=item.comment_id,
                    job_id=job.id,
                    video_id=job.video_id,
                    original_text=item.original_text,
                    author_display_name=item.author_display_name,
                    like_count=item.like_count,
                    reply_count=item.reply_count,
                    published_at=item.published_at,
                    detected_language=script_info["language"],
                    detected_script=script_info["script"],
                    translated_text=None,
                )
                db.add(comment_entity)
                saved_comments.append(comment_entity)

            # Update job telemetry
            job.total_comments = len(saved_comments)
            job.error_message = None
            await db.commit()

            logger.info(
                f"Ingestion completed for job {job.id}: {len(saved_comments)} comments saved."
            )
            return video, saved_comments

        except (
            YouTubeCommentsDisabledError,
            YouTubeVideoNotFoundError,
            YouTubeQuotaExceededError,
            YouTubeAuthError,
            YouTubeAPIError,
        ) as api_err:
            logger.error(f"Ingestion failed for job {job.id}: {api_err}")
            job.status = "failed"
            job.error_message = str(api_err)
            await db.commit()
            raise

        except Exception as exc:
            logger.exception(f"Unexpected error during comment ingestion for job {job.id}: {exc}")
            job.status = "failed"
            job.error_message = f"Ingestion error: {exc}"
            await db.commit()
            raise


def get_ingestion_service() -> IngestionService:
    """Dependency provider for IngestionService."""
    return IngestionService()
