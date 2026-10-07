"""Health routes module conforming to Section 6 & 21."""

from fastapi import APIRouter, status
from backend.app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Minimal API health check",
    description="Returns a lightweight, machine-readable status indicating the API process is alive.",
)
async def health() -> HealthResponse:
    """Minimal health check endpoint indicating that the API process is alive."""
    return HealthResponse(status="ok")
