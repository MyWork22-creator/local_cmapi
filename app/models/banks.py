"""
Bank model with enhanced validation and business logic.
"""
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Index, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base
from app.core.validators import BankValidators, CommonValidators
from app.core.exceptions import ValidationError


class Bank(Base):
    """
    Bank model representing financial institutions.

    Attributes:
        bank_id: Primary key
        bank_name: Unique bank name
        logo: URL to bank logo
        description: Bank description
        created_by_user_id: User who created this bank
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = 'banks'

    # Table arguments for indexes and constraints
    __table_args__ = (
        Index('idx_bank_name', 'bank_name'),
        Index('idx_bank_created_at', 'created_at'),
        Index('idx_bank_created_by', 'created_by_user_id'),
    )

    bank_id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Bank ID"
    )
    bank_name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique bank name"
    )
    logo = Column(
        String(500),
        nullable=True,
        comment="URL to bank logo"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Bank description"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )
    created_by_user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete="SET NULL"),
        nullable=True,
        comment="User who created this bank"
    )

    # Relationships
    customers = relationship("Customer", back_populates="bank", lazy="select")
    created_by_user = relationship("User", back_populates="banks_created")

    @validates('bank_name')
    def validate_bank_name(self, key: str, bank_name: str) -> str:
        """Validate bank name format."""
        return BankValidators.validate_bank_name(bank_name)

    @validates('description')
    def validate_description(self, key: str, description: Optional[str]) -> Optional[str]:
        """Validate and sanitize description."""
        if description:
            return CommonValidators.sanitize_string(description, max_length=1000)
        return description

    @hybrid_property
    def customer_count(self) -> int:
        """Get the number of customers associated with this bank."""
        return len(self.customers)

    @hybrid_property
    def has_logo(self) -> bool:
        """Check if bank has a logo."""
        return self.logo is not None and self.logo.strip() != ""


    def update_info(self, name: Optional[str] = None, logo: Optional[str] = None,
                   description: Optional[str] = None) -> None:
        """
        Update bank information.

        Args:
            name: New bank name
            logo: New logo URL
            description: New description
        """
        if name is not None:
            self.bank_name = name
        if logo is not None:
            self.logo = logo
        if description is not None:
            self.description = description

    def __repr__(self) -> str:
        """String representation of the bank."""
        return f"<Bank(id={self.bank_id}, name='{self.bank_name}')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.bank_name


