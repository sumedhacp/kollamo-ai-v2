"""Common and standardized schemas for Kollamo.ai Backend."""

from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured details of an error."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(None, description="Optional diagnostic details or validation issues")


class ErrorResponse(BaseModel):
    """Consistent RFC-compliant error envelope returned across all failed API endpoints."""

    error: ErrorDetail


class HealthStatus(BaseModel):
    """Basic health status payload."""

    status: str = Field(..., description="Health status string (e.g. 'ok', 'healthy')")
    project: str = Field(..., description="Project name")
    version: str = Field(..., description="Project version")


class RootMetadataResponse(BaseModel):
    """Root metadata payload."""

    project: str = Field(..., description="Project name")
    version: str = Field(..., description="Project version")
    status: str = Field(..., description="Service status")
    docs: str = Field(..., description="Path to interactive API documentation")
