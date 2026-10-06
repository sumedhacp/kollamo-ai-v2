"""FastAPI Main Application Entrypoint for Kollamo.ai."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import engine
from backend.app.schemas.error import ErrorDetail, ErrorResponse
from backend.app.services.sentiment_service import SentimentService


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

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standardized Error Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Formats validation errors into the standard RFC-compliant error envelope."""
    # Convert error list to JSON serializable objects
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


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Formats Starlette/FastAPI HTTP exceptions into standard error envelope."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="HTTP_ERROR",
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
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please try again later.",
            details=None,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


# Root Endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root metadata endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
    }


# Mount API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
