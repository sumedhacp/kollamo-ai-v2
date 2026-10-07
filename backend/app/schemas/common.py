"""Common and standardized schemas for Kollamo.ai Backend."""

from typing import Any, Optional, Literal, List, Union
from pydantic import BaseModel, Field


class ValidationFieldError(BaseModel):
    """Specific field validation error."""

    field: str = Field(..., description="Field name that failed validation")
    code: str = Field(..., description="Validation error code (REQUIRED, INVALID_TYPE, EMPTY_TEXT)")
    message: str = Field(..., description="Human-readable field error message")


class ValidationDetails(BaseModel):
    """Validation details envelope."""

    fields: List[ValidationFieldError] = Field(..., description="List of field-level validation errors")


class ErrorDetail(BaseModel):
    """Structured details of an error."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Union[ValidationDetails, Any]] = Field(
        None, description="Optional diagnostic details or validation issues"
    )


class ErrorResponse(BaseModel):
    """Consistent RFC-compliant error envelope returned across all failed API endpoints."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    """Minimal health response payload indicating API process liveness."""

    status: Literal["ok"] = "ok"


class RootMetadataResponse(BaseModel):
    """Root metadata payload."""

    project: str = Field(..., description="Project name")
    version: str = Field(..., description="Project version")
    status: str = Field(..., description="Service status")
    docs: str = Field(..., description="Path to interactive API documentation")
