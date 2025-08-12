"""
Bank-related Pydantic schemas for request/response validation.

This module contains all the Pydantic models used for bank-related API endpoints,
including request validation, response serialization, and documentation.
"""
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from app.core.validators import bank_name_validator,url_validator

class BankBase(BaseModel):
    """
    Base bank schema with common fields.

    This schema contains the core fields that are shared across
    different bank-related operations.
    """
    bank_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        example="ABC Bank",
        description="Name of the bank (2-255 characters)"
    )
    logo: Optional[str] = Field(
        None,
        max_length=500,
        example="https://example.com/logo.png",
        description="URL to the bank's logo image"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        example="A leading financial institution providing comprehensive banking services",
        description="Brief description of the bank"
    )

    @field_validator('bank_name')
    @classmethod
    def validate_bank_name(cls, v: str) -> str:
        """Validate bank name format and content."""
        return bank_name_validator(cls, v)

    @field_validator('logo')
    @classmethod
    def validate_logo_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate logo URL format."""
        if v:
            return url_validator(cls, v)
        return v


class BankCreate(BankBase):
    """
    Schema for creating a new bank.

    Inherits all fields from BankBase and makes bank_name required.
    Used for POST /banks/ endpoint.
    """
    
    bank_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        example="First National Bank",
        description="Name of the bank to create"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "bank_name": "First National Bank",
                "logo": "https://example.com/fnb-logo.png",
                "description": "A trusted financial partner since 1950"
            }
        }


class BankUpdate(BaseModel):
    """
    Schema for updating an existing bank.

    All fields are optional to support partial updates.
    Used for PUT /banks/{bank_id} endpoint.
    """
    
    bank_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        example="Updated Bank Name",
        description="New name for the bank"
    )
    logo: Optional[str] = Field(
        None,
        max_length=500,
        example="https://example.com/new-logo.png",
        description="New logo URL for the bank"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        example="Updated bank description",
        description="New description for the bank"
    )

    @field_validator('bank_name')
    @classmethod
    def validate_bank_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate bank name format and content."""
        if v:
            return bank_name_validator(cls, v)
        return v

    @field_validator('logo')
    @classmethod
    def validate_logo_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate logo URL format."""
        if v:
            return url_validator(cls, v)
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "bank_name": "Updated Bank Name",
                "logo": "https://example.com/updated-logo.png",
                "description": "Updated description with new services"
            }
        }

class BankDeletionResponse(BaseModel):
    """
    Schema for a detailed response after a bank has been deleted.
    """
    message: str = "Bank deleted successfully"
    bank_id: int
    bank_name: str
    created_by_user_id: Optional[int]
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        example="2025-08-12T07:06:45.547759Z",
        description="Response timestamp"
    )


class BankResponse(BankBase):
    bank_id: int 
    created_by_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }



class BankSummary(BaseModel):
    """
    Schema for bank summary information.

    Lightweight version of bank data for list views and references.
    """
    bank_id: int = Field(
        ...,
        example=1,
        description="Unique identifier for the bank"
    )
    bank_name: str = Field(
        ...,
        example="ABC Bank",
        description="Name of the bank"
    )
    logo: Optional[str] = Field(
        None,
        example="https://example.com/logo.png",
        description="URL to the bank's logo"
    )
    
    model_config = {
        "from_attributes": True
    }


# Import UserSummary for forward reference
from app.schemas.auth import UserWithRole

# Forward references for circular imports
BankResponse.model_rebuild()

