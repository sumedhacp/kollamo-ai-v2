"""Sentiment service module for Kollamo.ai Backend."""

from backend.app.services.sentiment_service import (
    SentimentService,
    get_sentiment_service,
)

__all__ = ["SentimentService", "get_sentiment_service"]
