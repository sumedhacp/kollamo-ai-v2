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
from backend.app.schemas.common import ErrorDetail, ErrorResponse, HealthResponse
from backend.app.schemas.sentiment import (
    SentimentAnalyzeRequest,
    SentimentAnalyzeResponse,
)
from backend.app.services.sentiment_service import (
    SentimentService,
    get_sentiment_service,
)
from ml.exceptions import (
    ModelNotTrainedError,
    ModelLoadingError,
    InferenceError,
    KollamoMLException,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup warm-up and graceful shutdown."""
    logger.info(f"Starting {settings.PROJECT_NAME} API v{settings.VERSION} [{settings.ENVIRONMENT}]")

    # Warm-up ML Sentiment Service on startup
    try:
        service = SentimentService.get_instance()
        if service.is_ready():
            logger.info("ML Sentiment Service warmed up and ready for inference.")
        else:
            logger.warning("ML Sentiment Service initialized with degraded readiness.")
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


# Standardized RFC-Compliant Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Formats validation errors into the standard RFC-compliant error envelope."""
    formatted_errors = []
    for err in exc.errors():
        formatted_errors.append({
            "loc": [str(loc_item) for loc_item in err.get("loc", [])],
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        })

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed. Please check the payload parameters.",
            details=formatted_errors,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


@app.exception_handler(ModelNotTrainedError)
async def model_not_trained_exception_handler(
    request: Request, exc: ModelNotTrainedError
) -> JSONResponse:
    """Handles requests when a fine-tuned model checkpoint is missing without returning fake sentiment."""
    logger.warning(f"ModelNotTrainedError on {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="MODEL_NOT_TRAINED",
            message="The Kollamo sentiment model is not available for inference.",
            details=getattr(exc, "details", None),
        )
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(),
    )


@app.exception_handler(ModelLoadingError)
async def model_loading_exception_handler(
    request: Request, exc: ModelLoadingError
) -> JSONResponse:
    """Handles model initialization and loading errors."""
    logger.error(f"ModelLoadingError on {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="MODEL_UNAVAILABLE",
            message="The configured model cannot currently be loaded or accessed.",
            details=getattr(exc, "details", None),
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
    """Handles ML inference computation failures securely without leaking internals."""
    logger.error(f"InferenceError on {request.method} {request.url.path}: {exc}")
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INFERENCE_ERROR",
            message="Sentiment inference computation failed.",
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
    """Handles general ML pipeline exceptions."""
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


# Health Endpoint (Section 21: GET /health returns {"status": "ok"})
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Minimal API health check",
    description="Returns a lightweight, machine-readable status indicating the API process is alive.",
)
async def root_health() -> HealthResponse:
    """Minimal health check endpoint indicating that the API process is alive."""
    return HealthResponse(status="ok")


# Mount Versioned /api/v1 Sentiment Endpoint (Section 8: POST /api/v1/sentiment)
from backend.app.api.routes.sentiment import router as v1_sentiment_router

app.include_router(v1_sentiment_router, prefix="/api/v1")

# Mount Primary API Router under /api (supports /api/health, /api/sentiment legacy, /api/analyze)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
