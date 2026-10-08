"""Sentiment routes module conforming to Section 6 & 8."""

from fastapi import APIRouter, Depends, status
from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.sentiment import (
    SentimentAnalyzeRequest,
    SentimentAnalyzeResponse,
)
from backend.app.services.sentiment import (
    SentimentService,
    get_sentiment_service,
)

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.post(
    "",
    response_model=SentimentAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronously classify sentiment of a single comment",
    description="Accepts a single social media comment and returns a 5-class sentiment distribution with model and processing metadata.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Validation error (missing, empty, or malformed)"},
        500: {"model": ErrorResponse, "description": "Inference or internal server error"},
        503: {"model": ErrorResponse, "description": "Model unavailable / Model not trained"},
    },
)
@router.post(
    "/analyze",
    response_model=SentimentAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronously classify sentiment of a single comment (canonical alias)",
    description="Accepts a single social media comment and returns a 5-class sentiment distribution with model and processing metadata.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Validation error (missing, empty, or malformed)"},
        500: {"model": ErrorResponse, "description": "Inference or internal server error"},
        503: {"model": ErrorResponse, "description": "Model unavailable / Model not trained"},
    },
)
async def analyze_sentiment(
    request: SentimentAnalyzeRequest,
    sentiment_service: SentimentService = Depends(get_sentiment_service),
) -> SentimentAnalyzeResponse:
    """Classifies sentiment using Phase 2 ML engine according to Section 10/15 schema."""
    return sentiment_service.analyze_v1(request)
