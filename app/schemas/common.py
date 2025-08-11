"""
Common Pydantic schemas used across multiple endpoints.

This module contains reusable schemas for standard API responses,
error handling, and pagination.
"""
from typing import Generic, List, Optional, TypeVar, Any, Dict
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """
    Standard error response schema.

    Used for all API error responses to ensure consistency.
    """
    detail: str = Field(
        ...,
        example="Resource not found",
        description="Human-readable error message"
    )
    error_code: Optional[str] = Field(
        None,
        example="NOT_FOUND_ERROR",
        description="Machine-readable error code"
    )
    path: Optional[str] = Field(
        None,
        example="/api/v1/banks/999",
        description="API path where the error occurred"
    )
    method: Optional[str] = Field(
        None,
        example="GET",
        description="HTTP method used"
    )
    timestamp: Optional[str] = Field(
        None,
        example="2024-01-01T12:00:00Z",
        description="Error timestamp"
    )
    errors: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Detailed validation errors (for validation failures)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "detail": "Bank with ID 999 not found",
                "error_code": "NOT_FOUND_ERROR",
                "path": "/api/v1/banks/999",
                "method": "GET",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class MessageResponse(BaseModel):
    """
    Standard success message response schema.

    Used for operations that don't return specific data.
    """
    message: str = Field(
        ...,
        example="Operation completed successfully",
        description="Success message"
    )
    timestamp: Optional[str] = Field(
        None,
        example="2024-01-01T12:00:00Z",
        description="Response timestamp"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "message": "Bank deleted successfully",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ListResponse(BaseModel, Generic[T]):
    """
    Generic paginated list response schema.

    Used for all list endpoints to provide consistent pagination.

    Type Parameters:
        T: The type of items in the list
    """
    items: List[T] = Field(
        ...,
        description="List of items for the current page"
    )
    total: int = Field(
        ...,
        ge=0,
        example=150,
        description="Total number of items across all pages"
    )
    limit: int = Field(
        ...,
        ge=1,
        le=1000,
        example=50,
        description="Maximum number of items per page"
    )
    offset: int = Field(
        ...,
        ge=0,
        example=0,
        description="Number of items skipped"
    )
    page: Optional[int] = Field(
        None,
        ge=1,
        example=1,
        description="Current page number (1-based)"
    )
    pages: Optional[int] = Field(
        None,
        ge=1,
        example=3,
        description="Total number of pages"
    )
    has_next: Optional[bool] = Field(
        None,
        example=True,
        description="Whether there are more pages"
    )
    has_prev: Optional[bool] = Field(
        None,
        example=False,
        description="Whether there are previous pages"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "limit": 50,
                "offset": 0,
                "page": 1,
                "pages": 3,
                "has_next": True,
                "has_prev": False
            }
        }


class HealthCheckResponse(BaseModel):
    """
    Health check response schema.

    Used for health monitoring endpoints.
    """
    status: str = Field(
        ...,
        example="healthy",
        description="Overall health status (healthy, degraded, unhealthy)"
    )
    timestamp: str = Field(
        ...,
        example="2024-01-01T12:00:00Z",
        description="Health check timestamp"
    )
    version: str = Field(
        ...,
        example="1.0.0",
        description="Application version"
    )
    environment: str = Field(
        ...,
        example="production",
        description="Environment name"
    )
    uptime_seconds: float = Field(
        ...,
        example=3600.5,
        description="Application uptime in seconds"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0.0",
                "environment": "production",
                "uptime_seconds": 3600.5
            }
        }


class ValidationErrorDetail(BaseModel):
    """
    Detailed validation error information.

    Used within ErrorResponse for validation failures.
    """
    field: str = Field(
        ...,
        example="bank_name",
        description="Field that failed validation"
    )
    message: str = Field(
        ...,
        example="Bank name must be at least 2 characters long",
        description="Validation error message"
    )
    type: str = Field(
        ...,
        example="value_error.any_str.min_length",
        description="Validation error type"
    )
    input_value: Optional[Any] = Field(
        None,
        example="A",
        description="The value that failed validation"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "field": "bank_name",
                "message": "Bank name must be at least 2 characters long",
                "type": "value_error.any_str.min_length",
                "input_value": "A"
            }
        }

