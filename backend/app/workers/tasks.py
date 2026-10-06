"""Celery Background Tasks for Asynchronous Sentiment and Telemetry Pipelines."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.job import AnalysisJob
from backend.app.models.comment import Comment
from backend.app.models.prediction import Prediction
from backend.app.models.summary_metrics import SummaryMetric
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.sentiment_service import SentimentService
from backend.app.workers.celery_app import celery_app
from ml.data.dataset_loader import SENTIMENT_LABELS


def compute_summary_metrics(
    comments_with_predictions: List[tuple[Comment, Prediction]],
) -> Dict[str, Any]:
    """Calculates aggregated sentiment percentages and engagement metrics from predictions."""
    total = len(comments_with_predictions)
    counts = {label: 0 for label in SENTIMENT_LABELS}
    likes_by_sentiment = {label: 0 for label in SENTIMENT_LABELS}

    for comment, pred in comments_with_predictions:
        sentiment = pred.sentiment if pred.sentiment in counts else "unsupported"
        counts[sentiment] += 1
        likes_by_sentiment[sentiment] += (comment.like_count or 0)

    total_likes = sum(likes_by_sentiment.values())

    # Compute percentages
    percentages = {}
    for label in SENTIMENT_LABELS:
        pct = (counts[label] / total * 100.0) if total > 0 else 0.0
        percentages[label] = round(pct, 2)

    # Compute average likes per sentiment
    avg_likes = {}
    for label in SENTIMENT_LABELS:
        count = counts[label]
        avg = (likes_by_sentiment[label] / count) if count > 0 else 0.0
        avg_likes[label] = round(avg, 2)

    return {
        "sentiment_counts": counts,
        "sentiment_percentages": percentages,
        "engagement_metrics": {
            "total_likes": total_likes,
            "average_likes_per_sentiment": avg_likes,
        },
    }


async def run_analysis_pipeline(
    job_id: uuid.UUID,
    session: Optional[AsyncSession] = None,
    batch_size: int = 32,
    ingestion_service: Optional[IngestionService] = None,
) -> Dict[str, Any]:
    """Async pipeline orchestrating ingestion, micro-batch sentiment inference, and metric rollups."""
    owns_session = session is None
    db = session or AsyncSessionLocal()

    try:
        # 1. Retrieve job
        stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
        result = await db.execute(stmt)
        job = result.scalars().first()

        if not job:
            raise ValueError(f"Analysis job {job_id} not found.")

        logger.info(f"Worker claimed analysis job {job.id} for processing.")
        job.status = "running"
        await db.commit()

        # 2. Ingest comments if not already present
        comment_count_stmt = select(Comment).where(Comment.job_id == job_id)
        existing_comments = (await db.execute(comment_count_stmt)).scalars().all()

        if not existing_comments:
            ingestion = ingestion_service or IngestionService()
            logger.info(f"Comments not present for job {job.id}. Triggering ingestion.")
            _, existing_comments = await ingestion.ingest_job_comments(db=db, job_id=job_id)

        job.total_comments = len(existing_comments)
        await db.commit()

        # 3. Micro-batch Sentiment Inference
        sentiment_service = SentimentService.get_instance()
        if not sentiment_service.is_ready():
            raise RuntimeError("Sentiment model engine is not ready in worker.")

        # Find comments without predictions
        pred_stmt = select(Prediction.comment_id).join(Comment).where(Comment.job_id == job_id)
        existing_pred_comment_ids = set((await db.execute(pred_stmt)).scalars().all())

        comments_to_predict = [
            c for c in existing_comments if c.comment_id not in existing_pred_comment_ids
        ]

        logger.info(
            f"Processing sentiment for {len(comments_to_predict)} comments (batch_size={batch_size})"
        )

        # Process in micro-batches
        for i in range(0, len(comments_to_predict), batch_size):
            chunk = comments_to_predict[i : i + batch_size]
            texts = [c.original_text for c in chunk]
            batch_predictions = sentiment_service.predictor.predict_batch(texts)

            for comment, pred_data in zip(chunk, batch_predictions):
                pred_entity = Prediction(
                    id=uuid.uuid4(),
                    comment_id=comment.comment_id,
                    sentiment=pred_data["sentiment"],
                    confidence=pred_data["confidence"],
                    class_probabilities=pred_data["class_probabilities"],
                )
                db.add(pred_entity)

            job.processed_comments = min(job.processed_comments + len(chunk), job.total_comments)
            await db.commit()

        # 4. Fetch all predictions to compute summary metrics
        full_comments_stmt = (
            select(Comment)
            .options(selectinload(Comment.prediction))
            .where(Comment.job_id == job_id)
        )
        all_comments_res = await db.execute(full_comments_stmt)
        all_comments = all_comments_res.scalars().all()

        pairs = [(c, c.prediction) for c in all_comments if c.prediction is not None]
        summary_data = compute_summary_metrics(pairs)

        # Upsert SummaryMetric
        metric_stmt = select(SummaryMetric).where(SummaryMetric.job_id == job_id)
        existing_metric = (await db.execute(metric_stmt)).scalars().first()

        if existing_metric:
            existing_metric.sentiment_counts = summary_data["sentiment_counts"]
            existing_metric.sentiment_percentages = summary_data["sentiment_percentages"]
            existing_metric.engagement_metrics = summary_data["engagement_metrics"]
            existing_metric.calculated_at = datetime.now(timezone.utc)
        else:
            new_metric = SummaryMetric(
                id=uuid.uuid4(),
                job_id=job_id,
                sentiment_counts=summary_data["sentiment_counts"],
                sentiment_percentages=summary_data["sentiment_percentages"],
                engagement_metrics=summary_data["engagement_metrics"],
                calculated_at=datetime.now(timezone.utc),
            )
            db.add(new_metric)

        # 5. Mark Job as Completed
        job.status = "completed"
        job.processed_comments = job.total_comments
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None
        await db.commit()

        logger.info(f"Analysis job {job.id} completed successfully.")
        return {
            "job_id": str(job.id),
            "status": "completed",
            "total_comments": job.total_comments,
            "processed_comments": job.processed_comments,
            "summary": summary_data,
        }

    except Exception as exc:
        logger.exception(f"Analysis pipeline failed for job {job_id}: {exc}")
        # Rollback and mark failure in DB
        try:
            fail_stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
            fail_job = (await db.execute(fail_stmt)).scalars().first()
            if fail_job:
                fail_job.status = "failed"
                fail_job.error_message = str(exc)
                await db.commit()
        except Exception as db_err:
            logger.error(f"Failed to record failure status for job {job_id}: {db_err}")
        raise

    finally:
        if owns_session:
            await db.close()


@celery_app.task(bind=True, name="process_youtube_analysis_job", max_retries=3)
def process_youtube_analysis_job(self: Any, job_id_str: str) -> Dict[str, Any]:
    """Celery background task entrypoint."""
    job_uuid = uuid.UUID(job_id_str)
    try:
        return asyncio.run(run_analysis_pipeline(job_id=job_uuid, batch_size=settings.BATCH_SIZE))
    except Exception as exc:
        logger.error(f"Celery task {self.request.id} failed: {exc}")
        raise
