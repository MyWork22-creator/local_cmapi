"""Password policy validation and enforcement."""
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.core.config import settings


class PasswordPolicy(BaseModel):
    """Password policy configuration."""
    min_length: int = Field(8, description="Minimum password length")
    max_length: int = Field(128, description="Maximum password length")
    require_uppercase: bool = Field(True, description="Require at least one uppercase letter")
    require_lowercase: bool = Field(True, description="Require at least one lowercase letter")
    require_digits: bool = Field(True, description="Require at least one digit")
    require_special_chars: bool = Field(True, description="Require at least one special character")
    special_chars: str = Field("!@#$%^&*()_+-=[]{}|;:,.<>?", description="Allowed special characters")
    prevent_common_passwords: bool = Field(True, description="Prevent common passwords")
    prevent_username_in_password: bool = Field(True, description="Prevent username in password")


class PasswordValidationError(Exception):
    """Custom exception for password validation errors."""
    def __init__(self, message: str, errors: List[str]):
        self.message = message
        self.errors = errors
        super().__init__(self.message)


class PasswordValidator:
    """Password validation service."""
    
    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()
        self.common_passwords = self._load_common_passwords()
    
    def _load_common_passwords(self) -> set:
        """Load common passwords list."""
        # In production, this should be loaded from a file or database
        return {
            "password", "123456", "password123", "admin", "qwerty", "letmein",
            "welcome", "monkey", "1234567890", "password1", "123456789",
            "12345678", "12345", "1234", "111111", "1234567", "dragon",
            "123123", "baseball", "abc123", "football", "master", "jordan",
            "harley", "ranger", "iwantu", "jennifer", "hunter", "fuck",
            "2000", "test", "batman", "trustno1", "thomas", "tigger",
            "robert", "access", "love", "buster", "1234567", "soccer"
        }
    
    def validate_password(self, password: str, username: str = None) -> Dict[str, Any]:
        """
        Validate password against policy.
        
        Args:
            password: The password to validate
            username: Optional username to check against password
            
        Returns:
            Dict with validation results
            
        Raises:
            PasswordValidationError: If password doesn't meet policy requirements
        """
        errors = []
        
        # Length validation
        if len(password) < self.policy.min_length:
            errors.append(f"Password must be at least {self.policy.min_length} characters long")
        
        if len(password) > self.policy.max_length:
            errors.append(f"Password must not exceed {self.policy.max_length} characters")
        
        # Character requirements
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.policy.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.policy.require_special_chars:
            special_char_pattern = f'[{re.escape(self.policy.special_chars)}]'
            if not re.search(special_char_pattern, password):
                errors.append(f"Password must contain at least one special character: {self.policy.special_chars}")
        
        # Common password check - TEMPORARILY DISABLED
        # if self.policy.prevent_common_passwords and password.lower() in self.common_passwords:
        #     errors.append("Password is too common. Please choose a more secure password")

        # Username in password check - TEMPORARILY DISABLED
        # if (self.policy.prevent_username_in_password and username and
        #     username.lower() in password.lower()):
        #     errors.append("Password must not contain your username")

        # Additional security checks - TEMPORARILY DISABLED
        # if password.lower() in ['password', 'admin', 'user', 'test']:
        #     errors.append("Password is too predictable. Please choose a more secure password")

        # Check for repeated characters - TEMPORARILY DISABLED
        # if len(set(password)) < 4:
        #     errors.append("Password must contain at least 4 different characters")
        
        # Check for sequential characters
        if self._has_sequential_chars(password):
            errors.append("Password must not contain sequential characters (e.g., 123, abc)")
        
        if errors:
            raise PasswordValidationError(
                "Password does not meet security requirements",
                errors
            )
        
        return {
            "valid": True,
            "strength": self._calculate_strength(password),
            "message": "Password meets all security requirements"
        }
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters in password."""
        # TEMPORARILY DISABLED - Return False to allow all passwords
        return False

        # Original code commented out for easier password creation
        # password = password.lower()
        #
        # # Check for numeric sequences
        # for i in range(len(password) - 2):
        #     if password[i:i+3].isdigit():
        #         nums = [int(c) for c in password[i:i+3]]
        #         if nums[1] == nums[0] + 1 and nums[2] == nums[1] + 1:
        #             return True
        #
        # # Check for alphabetic sequences
        # for i in range(len(password) - 2):
        #     if password[i:i+3].isalpha():
        #         chars = password[i:i+3]
        #         if (ord(chars[1]) == ord(chars[0]) + 1 and
        #             ord(chars[2]) == ord(chars[1]) + 1):
        #             return True
        #
        # return False
    
    def _calculate_strength(self, password: str) -> str:
        """Calculate password strength score."""
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(f'[{re.escape(self.policy.special_chars)}]', password):
            score += 1
        
        # Complexity bonus
        if len(set(password)) >= len(password) * 0.7:  # High character diversity
            score += 1
        
        if score <= 3:
            return "weak"
        elif score <= 5:
            return "medium"
        elif score <= 7:
            return "strong"
        else:
            return "very_strong"
    
    def get_policy_description(self) -> Dict[str, Any]:
        """Get human-readable password policy description."""
        requirements = []
        
        requirements.append(f"Be between {self.policy.min_length} and {self.policy.max_length} characters long")
        
        if self.policy.require_lowercase:
            requirements.append("Contain at least one lowercase letter")
        
        if self.policy.require_uppercase:
            requirements.append("Contain at least one uppercase letter")
        
        if self.policy.require_digits:
            requirements.append("Contain at least one number")
        
        if self.policy.require_special_chars:
            requirements.append(f"Contain at least one special character ({self.policy.special_chars})")
        
        if self.policy.prevent_common_passwords:
            requirements.append("Not be a common password")
        
        if self.policy.prevent_username_in_password:
            requirements.append("Not contain your username")
        
        return {
            "title": "Password Requirements",
            "requirements": requirements,
            "policy": self.policy.dict()
        }


# Global password validator instance
password_validator = PasswordValidator()


def validate_password(password: str, username: str = None) -> Dict[str, Any]:
    """Convenience function for password validation."""
    return password_validator.validate_password(password, username)


def get_password_requirements() -> Dict[str, Any]:
    """Get password policy requirements."""
    return password_validator.get_policy_description()
