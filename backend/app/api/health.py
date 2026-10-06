"""System Health Check Endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.app.core.config import settings
from backend.app.db.session import check_db_health
from backend.app.schemas.health import HealthResponse, HealthServices
from backend.app.services.sentiment_service import (
    SentimentService,
    get_sentiment_service,
)

router = APIRouter(tags=["Health"])


async def check_redis_health() -> str:
    """Checks Redis broker connectivity."""
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
        await client.ping()
        await client.aclose()
        return "connected"
    except Exception:
        return "disconnected"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check platform health and service readiness",
    description="Returns connectivity status for PostgreSQL, Redis broker, and ML sentiment predictor.",
)
async def get_health(
    sentiment_service: SentimentService = Depends(get_sentiment_service),
) -> HealthResponse:
    """Evaluates readiness of database, Redis, and ML inference components."""
    db_status = await check_db_health()
    redis_status = await check_redis_health()
    ml_status = "loaded" if sentiment_service.is_ready() else "not_loaded"

    # Overall system status
    overall_status = "healthy" if ml_status == "loaded" else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        services=HealthServices(
            database=db_status,
            redis=redis_status,
            ml_engine=ml_status,
        ),
        timestamp=datetime.now(timezone.utc),
    )
