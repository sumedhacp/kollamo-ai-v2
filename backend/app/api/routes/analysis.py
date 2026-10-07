"""FastAPI Router for Asynchronous Analysis Jobs (Phase 5)."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

try:
    from app.core.logging import logger
    from app.schemas.common import ErrorResponse, ErrorDetail
    from app.schemas.analysis import (
        AnalysisJobRequest,
        JobCreatedResponse,
        JobStatusResponse,
        JobProgress,
        AnalysisResult,
    )
    from app.services.jobs import (
        JobStateService,
        JobNotFoundError,
        JobQueueUnavailableError,
        get_job_state_service,
    )
    from app.workers.tasks import process_analysis_job
except ImportError:
    from backend.app.core.logging import logger
    from backend.app.schemas.common import ErrorResponse, ErrorDetail
    from backend.app.schemas.analysis import (
        AnalysisJobRequest,
        JobCreatedResponse,
        JobStatusResponse,
        JobProgress,
        AnalysisResult,
    )
    from backend.app.services.jobs import (
        JobStateService,
        JobNotFoundError,
        JobQueueUnavailableError,
        get_job_state_service,
    )
    from backend.app.workers.tasks import process_analysis_job

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "/jobs",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create asynchronous YouTube sentiment analysis job",
    description=(
        "Accepts a video URL, generates a unique job ID, enqueues background processing "
        "via Celery/Redis, and immediately returns HTTP 202 Accepted with status QUEUED."
    ),
    responses={
        202: {
            "model": JobCreatedResponse,
            "description": "Job accepted and queued for asynchronous execution",
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation failure for input parameters (VALIDATION_ERROR)",
        },
        503: {
            "model": ErrorResponse,
            "description": "Asynchronous task queue is unavailable (JOB_QUEUE_UNAVAILABLE)",
        },
        500: {
            "model": ErrorResponse,
            "description": "Unexpected internal error (INTERNAL_ERROR)",
        },
    },
)
async def create_analysis_job(
    request: AnalysisJobRequest,
    job_service: JobStateService = Depends(get_job_state_service),
) -> JobCreatedResponse:
    """Enqueues an asynchronous analysis job."""
    job_id = str(uuid.uuid4())
    request_data = request.model_dump()

    # 1. Record initial state in JobStateService
    job_service.create_job(job_id=job_id, request_data=request_data)

    # 2. Enqueue Celery task
    try:
        process_analysis_job.delay(job_id, request_data)
        logger.info(f"Successfully enqueued analysis job {job_id} for URL {request.video_url}")
    except Exception as exc:
        logger.error(f"Failed to submit task for job {job_id} to broker: {exc}")
        job_service.delete_job(job_id)
        raise JobQueueUnavailableError("The asynchronous task queue is currently unavailable.")

    return JobCreatedResponse(job_id=job_id, status="QUEUED")


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Query asynchronous analysis job status and results",
    description="Polls current execution status, live progress indicators, and normalized results or error.",
    responses={
        200: {
            "model": JobStatusResponse,
            "description": "Job status retrieved successfully",
        },
        404: {
            "model": ErrorResponse,
            "description": "Job ID was not found or expired (JOB_NOT_FOUND)",
        },
        500: {
            "model": ErrorResponse,
            "description": "Unexpected internal error (INTERNAL_ERROR)",
        },
    },
)
async def get_analysis_job(
    job_id: str,
    job_service: JobStateService = Depends(get_job_state_service),
) -> JobStatusResponse:
    """Retrieves current job status, progress, and results."""
    record = job_service.get_job(job_id)
    if not record:
        raise JobNotFoundError(job_id)

    progress_data = record.get("progress")
    progress_obj = JobProgress(**progress_data) if progress_data else None

    result_data = record.get("result")
    result_obj = AnalysisResult(**result_data) if result_data else None

    error_data = record.get("error")
    error_obj = ErrorDetail(**error_data) if error_data else None

    return JobStatusResponse(
        job_id=record["job_id"],
        status=record["status"],
        progress=progress_obj,
        result=result_obj,
        error=error_obj,
    )
