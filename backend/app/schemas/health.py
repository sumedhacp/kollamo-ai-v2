"""Health Check Schemas."""

from datetime import datetime
from typing import Dict
from pydantic import BaseModel, Field


class HealthServices(BaseModel):
    """Status of core platform backing services."""

    database: str = Field(..., description="Status of the PostgreSQL database connection")
    redis: str = Field(..., description="Status of the Redis broker connection")
    ml_engine: str = Field(..., description="Status of the ML sentiment predictor engine")


class HealthResponse(BaseModel):
    """Response returned by GET /api/health."""

    status: str = Field(..., description="Overall platform health: healthy or degraded")
    version: str = Field(..., description="Application version")
    services: HealthServices = Field(..., description="Status breakdown of dependencies")
    timestamp: datetime = Field(..., description="Timestamp of the health check evaluation")
