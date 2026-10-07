"""FastAPI Main Application Entrypoint for Kollamo.ai."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, APIRouter, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import engine
from backend.app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    ValidationDetails,
    ValidationFieldError,
)
from backend.app.schemas.sentiment import (
    SentimentAnalyzeRequest,
    SentimentAnalyzeResponse,
)
from backend.app.services.sentiment import (
    SentimentService,
    get_sentiment_service,
)
from backend.ml.exceptions import (
    ModelNotReadyError,
    ModelUnavailableError,
    InferenceError,
    KollamoMLException,
)
from ml.exceptions import (
    ModelNotTrainedError,
    ModelLoadingError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup warm-up and graceful shutdown."""
    logger.info(f"Starting {settings.PROJECT_NAME} API v{settings.VERSION} [{settings.ENVIRONMENT}]")

    # Warm-up ML Sentiment Service on startup
    try:
        service = SentimentService.get_instance()
        readiness = service.get_model_readiness()
        if readiness.status == "MODEL_READY":
            logger.info("ML Sentiment Service warmed up and ready for inference.")
        else:
            logger.warning(f"ML Sentiment Service initialized with status: {readiness.status}")
    except Exception as exc:
        logger.error(f"Error during ML service warmup: {exc}")

    yield

    # Graceful shutdown: dispose of DB engine pool
    logger.info("Shutting down database engine connections...")
    await engine.dispose()
    logger.info(f"{settings.PROJECT_NAME} API shutdown complete.")


app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    description="Malayalam-English Sentiment & Audience Intelligence Platform API",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

from backend.app.core.rate_limiter import RateLimitMiddleware, InMemoryRateLimiter

global_rate_limiter = InMemoryRateLimiter(requests_per_minute=120, window_seconds=60)
app.add_middleware(RateLimitMiddleware, limiter=global_rate_limiter)

# Configure CORS middleware safely (configurable origins, no wildcard in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Standardized RFC-Compliant Exception Handlers (Sections 17-24)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Formats validation errors into the exact Section 21/22 error envelope."""
    fields: list[ValidationFieldError] = []
    for err in exc.errors():
        loc = err.get("loc", [])
        field_name = str(loc[-1]) if loc else "text"
        err_type = err.get("type", "")
        msg = err.get("msg", "")

        if err_type == "missing":
            code = "REQUIRED"
            message = "Text is required." if field_name == "text" else f"{field_name.capitalize()} is required."
        elif "empty" in msg.lower() or "whitespace" in msg.lower() or "EMPTY_TEXT" in msg:
            code = "EMPTY_TEXT"
            message = "Text cannot be empty or contain only whitespace."
        elif err_type in ("string_type", "type_error") or "string" in msg.lower():
            code = "INVALID_TYPE"
            message = "Text must be a string."
        else:
            code = "INVALID_TYPE"
            message = msg

        fields.append(
            ValidationFieldError(
                field=field_name,
                code=code,
                message=message,
            )
        )

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details=ValidationDetails(fields=fields),
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


@app.exception_handler(ModelNotReadyError)
@app.exception_handler(ModelNotTrainedError)
async def model_not_ready_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handles requests when fine-tuned checkpoint is missing (HTTP 503 MODEL_NOT_READY)."""
    logger.warning(f"ModelNotReady on {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="MODEL_NOT_READY",
            message="The Kollamo sentiment model is not ready for inference.",
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(),
    )


@app.exception_handler(ModelUnavailableError)
@app.exception_handler(ModelLoadingError)
async def model_unavailable_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handles model unavailable errors (HTTP 503 MODEL_UNAVAILABLE)."""
    logger.error(f"ModelUnavailable on {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="MODEL_UNAVAILABLE",
            message="The Kollamo sentiment model is currently unavailable.",
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(),
    )


@app.exception_handler(InferenceError)
async def inference_exception_handler(
    request: Request, exc: InferenceError
) -> JSONResponse:
    """Handles ML inference computation failures securely without leaking internals (HTTP 500 INFERENCE_ERROR)."""
    logger.error(f"InferenceError on {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INFERENCE_ERROR",
            message="Sentiment inference failed.",
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


@app.exception_handler(KollamoMLException)
async def ml_generic_exception_handler(
    request: Request, exc: KollamoMLException
) -> JSONResponse:
    """Handles general ML pipeline exceptions (HTTP 500 INTERNAL_ERROR)."""
    logger.error(f"KollamoMLException on {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="A machine learning pipeline error occurred.",
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


try:
    from app.services.youtube.errors import YouTubeError
except ImportError:
    from backend.app.services.youtube.errors import YouTubeError

@app.exception_handler(YouTubeError)
async def youtube_exception_handler(
    request: Request, exc: YouTubeError
) -> JSONResponse:
    """Formats YouTube exceptions into the standard error envelope (Section 23 & 24)."""
    logger.warning(
        f"YouTubeError ({exc.code}) on {request.method} {request.url.path}: {exc.message}"
    )
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


try:
    from app.services.jobs import JobNotFoundError, JobQueueUnavailableError
except ImportError:
    from backend.app.services.jobs import JobNotFoundError, JobQueueUnavailableError

@app.exception_handler(JobNotFoundError)
async def job_not_found_exception_handler(
    request: Request, exc: JobNotFoundError
) -> JSONResponse:
    """Formats JobNotFoundError into RFC-compliant error envelope."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="JOB_NOT_FOUND",
            message=str(exc),
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.model_dump(),
    )


@app.exception_handler(JobQueueUnavailableError)
async def job_queue_unavailable_exception_handler(
    request: Request, exc: JobQueueUnavailableError
) -> JSONResponse:
    """Formats JobQueueUnavailableError into RFC-compliant error envelope."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="JOB_QUEUE_UNAVAILABLE",
            message=str(exc),
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(),
    )



@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Formats Starlette/FastAPI HTTP exceptions into standard error envelope."""
    error_code = "INTERNAL_ERROR"
    if exc.status_code == 400:
        error_code = "INVALID_REQUEST"
    elif exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 405:
        error_code = "METHOD_NOT_ALLOWED"
    elif exc.status_code == 422:
        error_code = "VALIDATION_ERROR"
    elif exc.status_code == 429:
        error_code = "RATE_LIMIT_EXCEEDED"
    elif exc.status_code == 503:
        error_code = "MODEL_UNAVAILABLE"

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=error_code,
            message=str(exc.detail),
            details=None,
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catches unhandled exceptions, logs them securely, and prevents information leakage."""
    logger.exception(f"Unhandled server error processing {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected server error occurred. Please try again later.",
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


# Root Metadata Endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root metadata endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
    }


# Mount Health Endpoint Router (GET /health)
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.sentiment import router as v1_sentiment_router

try:
    from app.api.routes.youtube import router as v1_youtube_router
    from app.api.routes.analysis import router as v1_analysis_router
except ImportError:
    from backend.app.api.routes.youtube import router as v1_youtube_router
    from backend.app.api.routes.analysis import router as v1_analysis_router

app.include_router(health_router)
app.include_router(v1_sentiment_router, prefix="/api/v1")
app.include_router(v1_youtube_router, prefix="/api/v1")
app.include_router(v1_analysis_router, prefix="/api/v1")

# Mount Primary API Router under /api (supports /api/health, /api/sentiment legacy, /api/analyze)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
