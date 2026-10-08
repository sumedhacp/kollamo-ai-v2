"""Celery Background Tasks for Asynchronous Sentiment and Telemetry Pipelines."""

import asyncio
import time
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


@celery_app.task(bind=True, name="process_analysis_job", max_retries=3)
def process_analysis_job(self: Any, job_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Celery background task orchestrating YouTube ingestion and ML sentiment analysis (Phase 5)."""
    try:
        from app.services.jobs import get_job_state_service
        from app.services.sentiment import get_sentiment_service
        from app.services.youtube.service import get_youtube_service
        from app.services.youtube.errors import YouTubeError
    except ImportError:
        from backend.app.services.jobs import get_job_state_service
        from backend.app.services.sentiment import get_sentiment_service
        from backend.app.services.youtube.service import get_youtube_service
        from backend.app.services.youtube.errors import YouTubeError

    job_service = get_job_state_service()
    start_time = time.perf_counter()
    logger.info(f"Worker claimed analysis job {job_id} for processing.")

    # 1. Update job to PROCESSING with stage FETCHING_VIDEO
    job_service.update_job(
        job_id=job_id,
        status="PROCESSING",
        progress={
            "stage": "FETCHING_VIDEO",
            "completed": 0,
            "total": None,
            "percentage": None,
        },
    )

    # 2. Check model readiness (Phase 2 boundary, Section 23/84)
    sentiment_service = get_sentiment_service()
    readiness = sentiment_service.get_model_readiness()
    if readiness.status == "MODEL_NOT_READY":
        logger.warning(f"Analysis job {job_id} failed: model is MODEL_NOT_READY")
        job_service.update_job(
            job_id=job_id,
            status="FAILED",
            error={
                "code": "MODEL_NOT_READY",
                "message": "The sentiment model is not ready.",
                "details": None,
            },
            progress={
                "stage": "SENTIMENT_ANALYSIS",
                "completed": 0,
                "total": None,
                "percentage": None,
            },
        )
        return {"job_id": job_id, "status": "FAILED", "error": "MODEL_NOT_READY"}
    elif readiness.status == "MODEL_UNAVAILABLE":
        logger.error(f"Analysis job {job_id} failed: model is MODEL_UNAVAILABLE")
        job_service.update_job(
            job_id=job_id,
            status="FAILED",
            error={
                "code": "MODEL_UNAVAILABLE",
                "message": "The sentiment model is currently unavailable.",
                "details": None,
            },
            progress={
                "stage": "SENTIMENT_ANALYSIS",
                "completed": 0,
                "total": None,
                "percentage": None,
            },
        )
        return {"job_id": job_id, "status": "FAILED", "error": "MODEL_UNAVAILABLE"}

    # 3. YouTube Ingestion (Phase 4 boundary)
    job_service.update_job(
        job_id=job_id,
        progress={
            "stage": "FETCHING_COMMENTS",
            "completed": 0,
            "total": None,
            "percentage": None,
        },
    )

    try:
        youtube_service = get_youtube_service()
        ingestion_result = asyncio.run(
            youtube_service.ingest(
                video_url=request_data.get("video_url"),
                comment_limit=request_data.get("comment_limit", 100),
                sort_by=request_data.get("sort_by", "newest"),
            )
        )
    except YouTubeError as yt_err:
        logger.error(f"YouTube ingestion error for job {job_id}: {yt_err}")
        job_service.update_job(
            job_id=job_id,
            status="FAILED",
            error={
                "code": yt_err.code,
                "message": yt_err.message,
                "details": yt_err.details,
            },
            progress={
                "stage": "FETCHING_COMMENTS",
                "completed": 0,
                "total": None,
                "percentage": None,
            },
        )
        return {"job_id": job_id, "status": "FAILED", "error": yt_err.code}
    except Exception as yt_exc:
        # Transient network error -> deliberate bounded retry (Section 32/33)
        if hasattr(self, "request") and getattr(self.request, "retries", 0) < self.max_retries:
            logger.warning(
                f"Transient error ingesting YouTube for job {job_id}, retrying ({self.request.retries + 1}/{self.max_retries}): {yt_exc}"
            )
            raise self.retry(exc=yt_exc, countdown=2 ** self.request.retries)
        logger.error(f"YouTube ingestion failed permanently for job {job_id}: {yt_exc}")
        job_service.update_job(
            job_id=job_id,
            status="FAILED",
            error={
                "code": "YOUTUBE_API_ERROR",
                "message": f"Failed to ingest YouTube comments: {yt_exc}",
                "details": None,
            },
        )
        return {"job_id": job_id, "status": "FAILED", "error": "YOUTUBE_API_ERROR"}

    # 4. Sentiment Inference (Phase 2 boundary)
    comments = ingestion_result.comments
    total_comments = len(comments)
    comment_results = []

    if total_comments == 0:
        empty_counts = {
            "Positive": 0,
            "Negative": 0,
            "Neutral": 0,
            "Mixed": 0,
            "Unsupported": 0,
        }
        job_service.update_job(
            job_id=job_id,
            status="COMPLETED",
            progress={
                "stage": "COMPLETED",
                "completed": 0,
                "total": 0,
                "percentage": 100,
            },
            result={
                "video": ingestion_result.video.model_dump(),
                "total_comments": 0,
                "processed_comments": 0,
                "comments": [],
                "sentiment_counts": empty_counts,
                "model_name": getattr(sentiment_service.ml_service, "model_name", "kollamo-muril-5class"),
                "model_version": getattr(sentiment_service.ml_service, "model_version", "v1"),
                "analysis": {
                    "requested_comment_limit": request_data.get("comment_limit", 100),
                    "returned_comment_count": 0,
                    "sort_by": request_data.get("sort_by", "newest"),
                    "sentiment_counts": empty_counts,
                    "comments": [],
                },
                "model": {
                    "name": getattr(sentiment_service.ml_service, "model_name", "kollamo-muril-5class"),
                    "version": getattr(sentiment_service.ml_service, "model_version", "v1"),
                },
                "processing": {
                    "processing_time_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                },
            },
        )
        return {"job_id": job_id, "status": "COMPLETED"}

    # Initial progress at start of sentiment analysis
    job_service.update_job(
        job_id=job_id,
        progress={
            "stage": "SENTIMENT_ANALYSIS",
            "completed": 0,
            "total": total_comments,
            "percentage": 0,
        },
    )

    for i, comment in enumerate(comments):
        try:
            pred = sentiment_service.ml_service.analyze(comment.text)
            probs = (
                pred.probabilities.model_dump()
                if hasattr(pred.probabilities, "model_dump")
                else pred.probabilities
            )
            comment_results.append({
                "comment_id": comment.comment_id,
                "text": comment.text,
                "author_name": comment.author_name,
                "author_display_name": comment.author_name,
                "like_count": comment.like_count,
                "published_at": comment.published_at.isoformat() if comment.published_at else None,
                "sentiment": pred.sentiment,
                "confidence": pred.confidence,
                "probabilities": probs,
            })
        except Exception as infer_err:
            logger.error(f"Inference error on comment {comment.comment_id} for job {job_id}: {infer_err}")
            job_service.update_job(
                job_id=job_id,
                status="FAILED",
                error={
                    "code": "INFERENCE_ERROR",
                    "message": "Sentiment inference failed during comment processing.",
                    "details": None,
                },
                progress={
                    "stage": "SENTIMENT_ANALYSIS",
                    "completed": i,
                    "total": total_comments,
                    "percentage": int((i / total_comments) * 100),
                },
            )
            return {"job_id": job_id, "status": "FAILED", "error": "INFERENCE_ERROR"}

        completed = i + 1
        pct = int((completed / total_comments) * 100)
        # Update progress periodically and at milestones
        job_service.update_job(
            job_id=job_id,
            progress={
                "stage": "SENTIMENT_ANALYSIS",
                "completed": completed,
                "total": total_comments,
                "percentage": pct,
            },
        )
        if (
            hasattr(self, "update_state")
            and getattr(self, "request", None)
            and getattr(self.request, "id", None)
        ):
            self.update_state(
                state="PROGRESS",
                meta={
                    "stage": "SENTIMENT_ANALYSIS",
                    "completed": completed,
                    "total": total_comments,
                    "percentage": pct,
                },
            )

    # 5. Finalizing and Mark COMPLETED
    sentiment_counts = {
        "Positive": sum(1 for c in comment_results if c["sentiment"] == "Positive"),
        "Negative": sum(1 for c in comment_results if c["sentiment"] == "Negative"),
        "Neutral": sum(1 for c in comment_results if c["sentiment"] == "Neutral"),
        "Mixed": sum(1 for c in comment_results if c["sentiment"] == "Mixed"),
        "Unsupported": sum(1 for c in comment_results if c["sentiment"] == "Unsupported"),
    }
    processing_duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    job_service.update_job(
        job_id=job_id,
        status="COMPLETED",
        progress={
            "stage": "COMPLETED",
            "completed": total_comments,
            "total": total_comments,
            "percentage": 100,
        },
        result={
            "video": ingestion_result.video.model_dump(),
            "total_comments": total_comments,
            "processed_comments": total_comments,
            "comments": comment_results,
            "sentiment_counts": sentiment_counts,
            "model_name": getattr(sentiment_service.ml_service, "model_name", "kollamo-muril-5class"),
            "model_version": getattr(sentiment_service.ml_service, "model_version", "v1"),
            "analysis": {
                "requested_comment_limit": request_data.get("comment_limit", 100),
                "returned_comment_count": total_comments,
                "sort_by": request_data.get("sort_by", "newest"),
                "sentiment_counts": sentiment_counts,
                "comments": comment_results,
            },
            "model": {
                "name": getattr(sentiment_service.ml_service, "model_name", "kollamo-muril-5class"),
                "version": getattr(sentiment_service.ml_service, "model_version", "v1"),
            },
            "processing": {
                "processing_time_ms": processing_duration_ms,
            },
        },
    )
    logger.info(f"Analysis job {job_id} successfully completed {total_comments} comments in {processing_duration_ms}ms.")
    return {"job_id": job_id, "status": "COMPLETED"}

