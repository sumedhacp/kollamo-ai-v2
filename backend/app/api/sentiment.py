"""Single-Comment Sentiment Analysis Endpoint."""

from fastapi import APIRouter, Depends, status
from backend.app.schemas.sentiment import SentimentRequest, SentimentResponse
from backend.app.schemas.error import ErrorResponse
from backend.app.services.sentiment_service import (
    SentimentService,
    get_sentiment_service,
)

router = APIRouter(tags=["Sentiment"])


@router.post(
    "/sentiment",
    response_model=SentimentResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronously classify sentiment of a single comment",
    description="Accepts a Malayalam, Manglish, English, or code-mixed comment and returns a 5-class sentiment distribution.",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error (empty, oversized, or malformed)"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def analyze_sentiment(
    request: SentimentRequest,
    sentiment_service: SentimentService = Depends(get_sentiment_service),
) -> SentimentResponse:
    """Classifies sentiment using Google MuRIL or trained baseline classifier."""
    return sentiment_service.analyze_comment(request)
