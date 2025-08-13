"""Enhanced input validation and sanitization."""
import re
import html
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status


class InputValidationError(Exception):
    """Custom exception for input validation errors."""
    pass


class SecurityValidator:
    """Security-focused input validation utilities."""
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)",
        r"(\bxp_\w+|\bsp_\w+)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e\\",
        r"..%2f",
        r"..%5c",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\b(cat|ls|dir|type|copy|move|del|rm|mkdir|rmdir|cd|pwd)\b",
        r"(&&|\|\|)",
        r"(\$\(|\`)",
    ]
    
    @classmethod
    def validate_against_sql_injection(cls, value: str) -> str:
        """Validate input against SQL injection patterns."""
        if not isinstance(value, str):
            return value
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise InputValidationError(f"Potential SQL injection detected in input")
        
        return value
    
    @classmethod
    def validate_against_xss(cls, value: str) -> str:
        """Validate input against XSS patterns."""
        if not isinstance(value, str):
            return value
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise InputValidationError(f"Potential XSS attack detected in input")
        
        return value
    
    @classmethod
    def validate_against_path_traversal(cls, value: str) -> str:
        """Validate input against path traversal patterns."""
        if not isinstance(value, str):
            return value
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise InputValidationError(f"Potential path traversal detected in input")
        
        return value
    
    @classmethod
    def validate_against_command_injection(cls, value: str) -> str:
        """Validate input against command injection patterns."""
        if not isinstance(value, str):
            return value
        
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise InputValidationError(f"Potential command injection detected in input")
        
        return value
    
    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Sanitize HTML content."""
        if not isinstance(value, str):
            return value
        
        # HTML escape the content
        return html.escape(value)
    
    @classmethod
    def validate_username(cls, username: str, allow_reserved: bool = False) -> str:
        """Validate username format and security."""
        if not username:
            raise InputValidationError("Username cannot be empty")

        # Length check
        if len(username) < 3 or len(username) > 50:
            raise InputValidationError("Username must be between 3 and 50 characters")

        # Character validation - only alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            raise InputValidationError("Username can only contain letters, numbers, underscores, and hyphens")

        # Must start with letter or number
        if not re.match(r"^[a-zA-Z0-9]", username):
            raise InputValidationError("Username must start with a letter or number")

        # Check for reserved words (only if not explicitly allowed)
        if not allow_reserved:
            reserved_words = ["admin", "root", "system", "user", "test", "guest", "null", "undefined"]
            if username.lower() in reserved_words:
                raise InputValidationError("Username cannot be a reserved word")

        return username.lower()  # Normalize to lowercase

    @classmethod
    def validate_username_for_login(cls, username: str) -> str:
        """Validate username for login (less restrictive)."""
        if not username:
            raise InputValidationError("Username cannot be empty")

        # Length check
        if len(username) < 1 or len(username) > 50:
            raise InputValidationError("Username must be between 1 and 50 characters")

        # Basic security checks only
        cls.validate_against_sql_injection(username)
        cls.validate_against_xss(username)

        return username.lower()  # Normalize to lowercase
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email format."""
        if not email:
            raise InputValidationError("Email cannot be empty")
        
        # Basic email regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise InputValidationError("Invalid email format")
        
        # Length check
        if len(email) > 254:
            raise InputValidationError("Email address too long")
        
        return email.lower()
    
    @classmethod
    def validate_role_name(cls, role_name: str) -> str:
        """Validate role name format."""
        if not role_name:
            raise InputValidationError("Role name cannot be empty")
        
        # Length check
        if len(role_name) < 2 or len(role_name) > 50:
            raise InputValidationError("Role name must be between 2 and 50 characters")
        
        # Character validation - letters, numbers, underscore, space
        if not re.match(r"^[a-zA-Z0-9_ ]+$", role_name):
            raise InputValidationError("Role name can only contain letters, numbers, underscores, and spaces")
        
        return role_name.strip()
    
    @classmethod
    def validate_permission_name(cls, permission_name: str) -> str:
        """Validate permission name format."""
        if not permission_name:
            raise InputValidationError("Permission name cannot be empty")
        
        # Length check
        if len(permission_name) < 2 or len(permission_name) > 100:
            raise InputValidationError("Permission name must be between 2 and 100 characters")
        
        # Character validation - letters, numbers, underscore, colon
        if not re.match(r"^[a-zA-Z0-9_:]+$", permission_name):
            raise InputValidationError("Permission name can only contain letters, numbers, underscores, and colons")
        
        return permission_name.lower()
    
    @classmethod
    def validate_description(cls, description: str) -> str:
        """Validate description field."""
        if not description:
            return ""
        
        # Length check
        if len(description) > 500:
            raise InputValidationError("Description cannot exceed 500 characters")
        
        # Basic XSS protection
        cls.validate_against_xss(description)
        
        # Sanitize HTML
        return cls.sanitize_html(description.strip())
    
    @classmethod
    def validate_search_query(cls, query: str) -> str:
        """Validate search query input."""
        if not query:
            return ""
        
        # Length check
        if len(query) > 200:
            raise InputValidationError("Search query too long")
        
        # Security validations
        cls.validate_against_sql_injection(query)
        cls.validate_against_xss(query)
        cls.validate_against_command_injection(query)
        
        return query.strip()
    
    @classmethod
    def validate_all_string_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply basic security validation to all string fields in a dictionary."""
        validated_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    # Apply basic security checks
                    cls.validate_against_sql_injection(value)
                    cls.validate_against_xss(value)
                    cls.validate_against_path_traversal(value)
                    validated_data[key] = value
                except InputValidationError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid input in field '{key}': {str(e)}"
                    )
            else:
                validated_data[key] = value
        
        return validated_data


# Pydantic validators for common use cases
def validate_username_field(v: str) -> str:
    """Pydantic validator for username fields."""
    return SecurityValidator.validate_username(v)


def validate_email_field(v: str) -> str:
    """Pydantic validator for email fields."""
    return SecurityValidator.validate_email(v)


def validate_role_name_field(v: str) -> str:
    """Pydantic validator for role name fields."""
    return SecurityValidator.validate_role_name(v)


def validate_permission_name_field(v: str) -> str:
    """Pydantic validator for permission name fields."""
    return SecurityValidator.validate_permission_name(v)


def validate_description_field(v: str) -> str:
    """Pydantic validator for description fields."""
    return SecurityValidator.validate_description(v)


def validate_search_query_field(v: str) -> str:
    """Pydantic validator for search query fields."""
    return SecurityValidator.validate_search_query(v)
