"""Central API Router for Kollamo.ai Backend."""

from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.sentiment import router as sentiment_router
from backend.app.api.analyze import router as analyze_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(sentiment_router)
api_router.include_router(analyze_router)
