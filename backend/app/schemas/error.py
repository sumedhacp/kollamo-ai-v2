"""Standardized Error Schemas for API Error Responses."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured details of an error."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(None, description="Optional diagnostic details or validation issues")


class ErrorResponse(BaseModel):
    """Consistent error envelope returned across all failed API endpoints."""

    error: ErrorDetail
