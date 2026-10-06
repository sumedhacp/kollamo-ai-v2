"""YouTube Ingestion and Batch Analysis Job Endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Path as FastApiPath, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponse,
    JobStatusResponse,
)
from backend.app.schemas.error import ErrorResponse
from backend.app.services.job_service import JobService

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
    return AnalyzeResponse(
        job_id=str(job.id),
        status=job.status,
        message="Analysis job queued successfully",
        created_at=job.created_at,
    )


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
