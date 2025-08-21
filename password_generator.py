#!/usr/bin/env python3
"""
Password Generator for CRM System
Generates passwords that comply with the strict password policy.
"""

import random
import string
import re


class PasswordGenerator:
    """Generate passwords that comply with the CRM password policy."""
    
    def __init__(self):
        # Characters that won't form sequences
        self.safe_digits = ['0', '2', '4', '6', '8', '9']  # Avoid 1,3,5,7 to prevent sequences
        self.safe_lowercase = ['a', 'c', 'e', 'g', 'i', 'k', 'm', 'o', 'q', 's', 'u', 'w', 'y']
        self.safe_uppercase = ['A', 'C', 'E', 'G', 'I', 'K', 'M', 'O', 'Q', 'S', 'U', 'W', 'Y']
        self.special_chars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '-', '=', 
                             '[', ']', '{', '}', '|', ';', ':', ',', '.', '<', '>', '?']
        
        # Common passwords to avoid
        self.common_passwords = {
            "password", "123456", "password123", "admin", "qwerty", "letmein",
            "welcome", "monkey", "1234567890", "password1", "123456789",
            "12345678", "12345", "1234", "111111", "1234567", "dragon",
            "123123", "baseball", "abc123", "football", "master", "jordan"
        }
    
    def has_sequential_chars(self, password: str) -> bool:
        """Check if password has sequential characters."""
        password = password.lower()
        
        # Check for numeric sequences
        for i in range(len(password) - 2):
            if password[i:i+3].isdigit():
                nums = [int(c) for c in password[i:i+3]]
                if nums[1] == nums[0] + 1 and nums[2] == nums[1] + 1:
                    return True
        
        # Check for alphabetic sequences
        for i in range(len(password) - 2):
            if password[i:i+3].isalpha():
                chars = password[i:i+3]
                if (ord(chars[1]) == ord(chars[0]) + 1 and 
                    ord(chars[2]) == ord(chars[1]) + 1):
                    return True
        
        return False
    
    def validate_password(self, password: str, username: str = None) -> tuple[bool, list[str]]:
        """Validate password against all rules."""
        errors = []
        
        # Length validation
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if len(password) > 128:
            errors.append("Password must not exceed 128 characters")
        
        # Character requirements
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password check
        if password.lower() in self.common_passwords:
            errors.append("Password is too common")
        
        # Username check
        if username and username.lower() in password.lower():
            errors.append("Password must not contain username")
        
        # Predictable passwords
        if password.lower() in ['password', 'admin', 'user', 'test']:
            errors.append("Password is too predictable")
        
        # Character diversity
        if len(set(password)) < 4:
            errors.append("Password must contain at least 4 different characters")
        
        # Sequential characters
        if self.has_sequential_chars(password):
            errors.append("Password must not contain sequential characters")
        
        return len(errors) == 0, errors
    
    def generate_password(self, length: int = 12, username: str = None) -> str:
        """Generate a valid password."""
        max_attempts = 100
        
        for _ in range(max_attempts):
            # Build password with required components
            password_chars = []
            
            # Add required character types
            password_chars.append(random.choice(self.safe_uppercase))
            password_chars.append(random.choice(self.safe_lowercase))
            password_chars.append(random.choice(self.safe_digits))
            password_chars.append(random.choice(self.special_chars))
            
            # Fill remaining length with safe characters
            remaining_length = length - 4
            all_safe_chars = (self.safe_uppercase + self.safe_lowercase + 
                            self.safe_digits + self.special_chars)
            
            for _ in range(remaining_length):
                password_chars.append(random.choice(all_safe_chars))
            
            # Shuffle the characters
            random.shuffle(password_chars)
            password = ''.join(password_chars)
            
            # Validate the generated password
            is_valid, errors = self.validate_password(password, username)
            if is_valid:
                return password
        
        raise Exception("Could not generate valid password after maximum attempts")
    
    def generate_multiple_passwords(self, count: int = 5, length: int = 12, username: str = None) -> list[str]:
        """Generate multiple valid passwords."""
        passwords = []
        for _ in range(count):
            passwords.append(self.generate_password(length, username))
        return passwords


def main():
    """Main function to demonstrate password generation."""
    generator = PasswordGenerator()
    
    print("🔐 CRM Password Generator")
    print("=" * 50)
    
    # Generate some example passwords
    print("\n✅ Valid Password Examples:")
    passwords = generator.generate_multiple_passwords(count=10, length=12)
    
    for i, password in enumerate(passwords, 1):
        is_valid, errors = generator.validate_password(password)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{i:2d}. {password:<15} - {status}")
        if errors:
            for error in errors:
                print(f"    ❌ {error}")
    
    print("\n" + "=" * 50)
    print("💡 Password Rules Summary:")
    print("• 8-128 characters long")
    print("• At least one uppercase letter")
    print("• At least one lowercase letter") 
    print("• At least one digit")
    print("• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
    print("• No common passwords")
    print("• No sequential characters (123, abc)")
    print("• At least 4 different characters")
    print("• Must not contain username")
    
    print("\n❌ Examples of INVALID passwords:")
    invalid_examples = [
        "password123",  # Common + sequential
        "SecureAbc!",   # Sequential abc
        "Strong123!",   # Sequential 123
        "MyPass456@",   # Sequential 456
        "Test789#",     # Sequential 789
        "admin",        # Too predictable
        "Aa1!",         # Too short
    ]
    
    for password in invalid_examples:
        is_valid, errors = generator.validate_password(password)
        print(f"• {password:<15} - {errors[0] if errors else 'Valid'}")


if __name__ == "__main__":
    main()
