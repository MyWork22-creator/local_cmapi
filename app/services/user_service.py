from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.core.password_policy import validate_password, PasswordValidationError


class UserService:
    """Service layer for user operations."""
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.user_name == username)
        return db.execute(stmt).scalars().first()
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.get(User, user_id)
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return db.execute(select(User).offset(skip).limit(limit)).scalars().all()
    
    @staticmethod
    def create(db: Session, username: str, password: str, role_id: Optional[int] = None) -> User:
        """Create a new user with password validation."""
        # Validate password against policy
        try:
            validate_password(password, username)
        except PasswordValidationError as e:
            # Re-raise with more context
            raise ValueError(f"Password validation failed: {'; '.join(e.errors)}")

        hashed_password = get_password_hash(password)
        user = User(
            user_name=username,
            password_hash=hashed_password,
            role_id=role_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update(
        db: Session,
        user_id: int,
        username: Optional[str] = None,
        status: Optional[str] = None,
        role_id: Optional[int] = None,
    ) -> Optional[User]:
        """Update user information."""
        user = db.get(User, user_id)
        if not user:
            return None
        
        if username is not None:
            user.user_name = username
        if status is not None:
            user.status = status
        if role_id is not None:
            user.role_id = role_id
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """Delete a user."""
        user = db.get(User, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True
    
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = UserService.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def update_status(db: Session, user_id: int, status: str) -> Optional[User]:
        """Update only user status."""
        user = db.get(User, user_id)
        if not user:
            return None
        
        user.status = status
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password with validation."""
        user = db.get(User, user_id)
        if not user:
            return False

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Validate new password
        try:
            validate_password(new_password, user.user_name)
        except PasswordValidationError as e:
            raise ValueError(f"New password validation failed: {'; '.join(e.errors)}")

        # Check if new password is different from current
        if verify_password(new_password, user.password_hash):
            raise ValueError("New password must be different from current password")

        # Update password
        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True

    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> bool:
        """Reset user password (admin function) with validation."""
        user = db.get(User, user_id)
        if not user:
            return False

        # Validate new password
        try:
            validate_password(new_password, user.user_name)
        except PasswordValidationError as e:
            raise ValueError(f"Password validation failed: {'; '.join(e.errors)}")

        # Update password
        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True
