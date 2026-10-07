"""YouTube Ingestion and Batch Analysis Job Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path as FastApiPath, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import get_db
from backend.app.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponse,
    JobStatusResponse,
    CommentItem,
)
from backend.app.schemas.error import ErrorResponse
from backend.app.services.job_service import JobService
from backend.app.services.ingestion_service import (
    IngestionService,
    get_ingestion_service,
)
from backend.app.services.youtube_client import (
    YouTubeAPIError,
    YouTubeAuthError,
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
    YouTubeVideoNotFoundError,
)

router = APIRouter(prefix="/analyze", tags=["YouTube Analysis"])


@router.post(
    "",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a YouTube video ingestion and sentiment analysis job",
    description="Validates the YouTube URL and queues an asynchronous job for comment retrieval and sentiment classification.",
    responses={
        422: {"model": ErrorResponse, "description": "Invalid YouTube URL or sample size"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_analysis_job(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    """Dispatches a YouTube comment ingestion and classification job."""
    job = await JobService.create_analysis_job(db=db, request=request)

    # Dispatch to Celery worker queue if not in testing without active broker
    if settings.ENVIRONMENT != "test":
        try:
            from backend.app.workers.tasks import process_youtube_analysis_job
            process_youtube_analysis_job.delay(str(job.id))
            logger.info(f"Enqueued Celery background task for job {job.id}")
        except Exception as exc:
            logger.warning(
                f"Could not dispatch Celery task for job {job.id} (broker may be offline): {exc}"
            )

    return AnalyzeResponse(
        job_id=str(job.id),
        status=job.status,
        message="Analysis job queued successfully",
        created_at=job.created_at,
    )


@router.post(
    "/{job_id}/process",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Process analysis pipeline directly (synchronous worker fallback)",
    description="Executes sentiment batch classification and summary metric generation directly.",
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        422: {"model": ErrorResponse, "description": "Invalid job ID"},
        500: {"model": ErrorResponse, "description": "Processing failure"},
    },
)
async def process_job_pipeline_endpoint(
    job_id: str = FastApiPath(..., description="The UUID of the analysis job"),
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    """Synchronously executes sentiment processing and metrics generation for a job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid job ID format: '{job_id}'. Expected a valid UUID.",
        )

    from backend.app.workers.tasks import run_analysis_pipeline

    try:
        await run_analysis_pipeline(job_id=job_uuid, session=db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    job = await JobService.get_job_by_id(db=db, job_id=job_uuid)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")

    return JobService.format_job_status_response(job)



@router.post(
    "/{job_id}/ingest",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger comment ingestion for an analysis job",
    description="Fetches YouTube video metadata and comments, persists them to the database, and updates job status.",
    responses={
        401: {"model": ErrorResponse, "description": "YouTube API key missing or invalid"},
        403: {"model": ErrorResponse, "description": "Comments are disabled on this video"},
        404: {"model": ErrorResponse, "description": "Video or job not found"},
        422: {"model": ErrorResponse, "description": "Invalid job ID format"},
        429: {"model": ErrorResponse, "description": "YouTube API quota exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def ingest_job_comments_endpoint(
    job_id: str = FastApiPath(..., description="The UUID of the analysis job"),
    db: AsyncSession = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> JobStatusResponse:
    """Performs video metadata and comment ingestion for a queued job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid job ID format: '{job_id}'. Expected a valid UUID.",
        )

    try:
        await ingestion_service.ingest_job_comments(db=db, job_id=job_uuid)
    except YouTubeCommentsDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Comments are disabled on this video.",
        )
    except YouTubeVideoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video was not found or is private.",
        )
    except YouTubeQuotaExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="YouTube Data API quota exceeded. Please try again tomorrow.",
        )
    except YouTubeAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"YouTube authentication failed: {exc}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except YouTubeAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"YouTube Data API error: {exc}",
        )

    # Return updated job status
    job = await JobService.get_job_by_id(db=db, job_id=job_uuid)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job with ID '{job_id}' not found.",
        )

    return JobService.format_job_status_response(job)


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get status, telemetry, and audience intelligence results for a job",
    description="Returns real-time progress, processed counts, and aggregated audience metrics for a given job UUID.",
    responses={
        404: {"model": ErrorResponse, "description": "Analysis job not found"},
        422: {"model": ErrorResponse, "description": "Invalid job ID format"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_analysis_job_status(
    job_id: str = FastApiPath(..., description="The UUID of the analysis job"),
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    """Retrieves current job status, progress, and computed metrics."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid job ID format: '{job_id}'. Expected a valid UUID.",
        )

    job = await JobService.get_job_by_id(db=db, job_id=job_uuid)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job with ID '{job_id}' not found.",
        )

    return JobService.format_job_status_response(job)


@router.get(
    "/{job_id}/comments",
    response_model=List[CommentItem],
    status_code=status.HTTP_200_OK,
    summary="Get classified comments for an analysis job",
    description="Returns comment threads, script detection, and MuRIL classifications with optional filtering.",
    responses={
        404: {"model": ErrorResponse, "description": "Analysis job not found"},
        422: {"model": ErrorResponse, "description": "Invalid job ID format"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_job_comments(
    job_id: str = FastApiPath(..., description="The UUID of the analysis job"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment label"),
    script: Optional[str] = Query(None, description="Filter by script type"),
    search: Optional[str] = Query(None, description="Search comment text"),
    limit: int = Query(250, ge=1, le=1000, description="Max comments to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> List[CommentItem]:
    """Retrieves individual analyzed comments for an existing job with filtering."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid job ID format: '{job_id}'. Expected a valid UUID.",
        )

    job = await JobService.get_job_by_id(db=db, job_id=job_uuid)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job with ID '{job_id}' not found.",
        )

    formatted = JobService.format_job_status_response(job)
    comments = formatted.comments or []

    # Apply sentiment filter
    if sentiment and sentiment.lower() != "all":
        comments = [c for c in comments if c.sentiment.lower() == sentiment.lower()]

    # Apply script filter
    if script and script.lower() != "all":
        comments = [c for c in comments if c.detected_script.lower() == script.lower()]

    # Apply search filter
    if search:
        s_lower = search.lower()
        comments = [
            c
            for c in comments
            if s_lower in c.original_text.lower()
            or (c.translated_text and s_lower in c.translated_text.lower())
        ]
    return comments[offset : offset + limit]


@router.get(
    "/{job_id}/report",
    summary="Generate comprehensive audience intelligence report payload",
    description="Assembles a complete academic report with video metadata, 5-class metrics, net approval index, linguistic breakdown, top comments, and methodology.",
)
async def get_job_report(
    job_id: str = FastApiPath(..., description="The unique UUID of the analysis job"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full structured report data for export."""
    from backend.app.services.report_service import ReportService
    from backend.app.schemas.report import AnalysisReportResponse

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid job ID format: '{job_id}'. Expected a valid UUID.",
        )

    try:
        return await ReportService.generate_report_data(job_id=job_uuid, session=db)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Failed to generate report data for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(exc)}",
        )


@router.get(
    "/{job_id}/report/pdf",
    summary="Download compiled PDF audience intelligence report",
    description="Generates and streams a professional multi-page branded PDF report document.",
)
async def download_job_report_pdf(
    job_id: str = FastApiPath(..., description="The unique UUID of the analysis job"),
    db: AsyncSession = Depends(get_db),
):
    """Streams a compiled PDF document for the analysis job."""
    from backend.app.services.report_service import ReportService

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid job ID format: '{job_id}'. Expected a valid UUID.",
        )

    try:
        report_data = await ReportService.generate_report_data(job_id=job_uuid, session=db)
        pdf_bytes = ReportService.generate_pdf_bytes(report_data)
        filename = f"kollamo-audience-report-{job_id[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Failed to compile PDF report for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF report generation error: {str(exc)}",
        )


@router.post(
    "/{job_id}/translate-comments",
    summary="Translate comments for an analysis job",
    description="Executes translation for non-English comments in the job that do not yet have translations.",
)
async def translate_job_comments(
    job_id: str = FastApiPath(..., description="The unique UUID of the analysis job"),
    limit: int = Query(default=20, ge=1, le=100, description="Max comments to translate in this batch"),
    db: AsyncSession = Depends(get_db),
):
    """Translates regional comments in the job using the translation service."""
    from backend.app.models.comment import Comment
    from backend.app.services.translation_service import get_translation_service
    from sqlalchemy import select

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid job ID format: '{job_id}'. Expected a valid UUID.",
        )

    job = await JobService.get_job_by_id(db=db, job_id=job_uuid)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job with ID '{job_id}' not found.",
        )

    # Find comments lacking translation
    stmt = (
        select(Comment)
        .where(Comment.job_id == job_uuid)
        .where(Comment.translated_text.is_(None))
        .limit(limit)
    )
    comments_to_translate = (await db.execute(stmt)).scalars().all()

    translation_service = get_translation_service()
    translated_count = 0

    for comment in comments_to_translate:
        res = translation_service.translate_detailed(comment.original_text)
        if res.text and res.status in ("translated", "original"):
            comment.translated_text = res.text
            translated_count += 1

    await db.commit()
    return {
        "job_id": str(job_uuid),
        "translated_count": translated_count,
        "remaining_untranslated": max(0, len(job.comments) - translated_count),
    }
