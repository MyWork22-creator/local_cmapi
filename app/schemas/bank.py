"""
Bank-related Pydantic schemas for request/response validation.

This module contains Pydantic models for bank-related API endpoints,
refactored to follow the DRY principle using inheritance.
"""
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from app.core.validators import bank_name_validator, url_validator


class BankBase(BaseModel):
    """
    Base bank schema with common fields and validation logic.
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
    
    # Validators are defined here and are inherited by all child schemas.
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
    Used for POST /banks/ endpoint.
    """
    #created_by_user_id: int = Field(...)

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "bank_name": "First National Bank",
                "logo": "https://example.com/fnb-logo.png",
                "description": "A trusted financial partner since 1950",
                
            }
        }

class BankUpdate(BaseModel):
    """
    Schema for updating an existing bank.
    All fields are optional to support partial updates.
    Used for PUT /banks/{bank_id} endpoint.
    """
    bank_name: Optional[str] = Field(None, min_length=2, max_length=255, example="Updated Bank Name")
    logo: Optional[str] = Field(None, max_length=500, example="https://example.com/new-logo.png")
    description: Optional[str] = Field(None, max_length=1000, example="Updated bank description")

    @field_validator('bank_name')
    @classmethod
    def validate_bank_name(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return bank_name_validator(cls, v)
        return v

    @field_validator('logo')
    @classmethod
    def validate_logo_url(cls, v: Optional[str]) -> Optional[str]:
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
    """
    Schema for a full bank response from the database.
    
    Inherits all fields and adds auto-generated fields from the database model.
    """
    bank_id: int = Field(..., description="Unique identifier for the bank")
    created_by_user_id: Optional[int] = Field(None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    model_config = {
        "from_attributes": True
    }
    

class BankSummary(BaseModel):
    """
    Schema for bank summary information.
    A lightweight version of bank data for list views and references.
    """
    bank_id: int = Field(..., example=1, description="Unique identifier for the bank")
    bank_name: str = Field(..., example="ABC Bank", description="Name of the bank")
    logo: Optional[str] = Field(None, example="https://example.com/logo.png", description="URL to the bank's logo")
    
    model_config = {
        "from_attributes": True
    }