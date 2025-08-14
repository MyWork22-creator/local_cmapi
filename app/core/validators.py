"""
Input validation utilities and custom validators.
"""
import re
from typing import Any, Optional
from pydantic import field_validator, ValidationInfo
from app.core.exceptions import ValidationError
from urllib.parse import urlparse


class CommonValidators:
    """Common validation utilities."""
    
    @staticmethod
    def validate_username(username: str) -> str:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            Validated username
            
        Raises:
            ValidationError: If username format is invalid
        """
        if not username:
            raise ValidationError("Username cannot be empty")
        
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise ValidationError("Username cannot exceed 50 characters")
        
        # Allow alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens")
        
        return username.lower()
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            Validated email
            
        Raises:
            ValidationError: If email format is invalid
        """
        if not email:
            raise ValidationError("Email cannot be empty")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
        
        return email.lower()
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Validated phone number
            
        Raises:
            ValidationError: If phone format is invalid
        """
        if not phone:
            raise ValidationError("Phone number cannot be empty")
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) < 10:
            raise ValidationError("Phone number must have at least 10 digits")
        
        if len(digits_only) > 15:
            raise ValidationError("Phone number cannot exceed 15 digits")
        
        return digits_only
    
    @staticmethod
    def validate_currency_code(currency: str) -> str:
        """
        Validate currency code format.
        
        Args:
            currency: Currency code to validate
            
        Returns:
            Validated currency code
            
        Raises:
            ValidationError: If currency format is invalid
        """
        if not currency:
            raise ValidationError("Currency code cannot be empty")
        
        currency = currency.upper()
        
        # Common currency codes
        valid_currencies = {
            'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD',
            'MXN', 'SGD', 'HKD', 'NOK', 'TRY', 'ZAR', 'BRL', 'INR', 'KRW', 'THB',
            'KHR', 'VND', 'LAK', 'MMK'  # Southeast Asian currencies
        }
        
        if currency not in valid_currencies:
            raise ValidationError(f"Unsupported currency code: {currency}")
        
        return currency
    
    @staticmethod
    def validate_amount(amount: str) -> str:
        """
        Validate monetary amount format.
        
        Args:
            amount: Amount to validate
            
        Returns:
            Validated amount
            
        Raises:
            ValidationError: If amount format is invalid
        """
        if not amount:
            raise ValidationError("Amount cannot be empty")
        
        # Remove whitespace
        amount = amount.strip()
        
        # Check for valid decimal format
        if not re.match(r'^\d+(\.\d{1,2})?$', amount):
            raise ValidationError("Amount must be a valid decimal number with up to 2 decimal places")
        
        # Convert to float to check range
        try:
            amount_float = float(amount)
            if amount_float < 0:
                raise ValidationError("Amount cannot be negative")
            if amount_float > 999999999.99:
                raise ValidationError("Amount exceeds maximum allowed value")
        except ValueError:
            raise ValidationError("Invalid amount format")
        
        return amount
    
    @staticmethod
    def validate_url(url: str) -> str:
        if not url:
            raise ValidationError("URL cannot be empty")
    
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError("Invalid URL format")
    
        return url
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input by removing dangerous characters.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If string is invalid
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        if max_length and len(sanitized) > max_length:
            raise ValidationError(f"String exceeds maximum length of {max_length} characters")
        
        return sanitized


class BankValidators:
    """Bank-specific validators."""
    
    @staticmethod
    def validate_bank_name(name: str) -> str:
        """
        Validate bank name.
        
        Args:
            name: Bank name to validate
            
        Returns:
            Validated bank name
        """
        if not name:
            raise ValidationError("Bank name cannot be empty")
        
        name = CommonValidators.sanitize_string(name, max_length=255)
        
        if len(name) < 2:
            raise ValidationError("Bank name must be at least 2 characters long")
        
        # Allow letters, numbers, spaces, and common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-&.,()]+$', name):
            raise ValidationError("Bank name contains invalid characters")
        
        return name.title()  # Title case

def url_validator(cls, v: str) -> str:
    """Pydantic field validator for URL."""
    return CommonValidators.validate_url(v)


def bank_name_validator(cls, v: str) -> str:
    """Pydantic field validator for bank name."""
    return BankValidators.validate_bank_name(v)
