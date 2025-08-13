from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.services.user_service import UserService
from app.services.role_service import RoleService
from app.core.security import create_access_token, create_refresh_token, verify_token, verify_token_with_blacklist
from app.core.config import settings


class AuthService:
    """Service layer for authentication operations."""
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        return UserService.authenticate(db, username, password)
    
    @staticmethod
    def create_tokens(user: User) -> dict:
        """Create access and refresh tokens for a user."""
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[dict]:
        """Verify and decode access token."""
        return verify_token(token)
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[dict]:
        """Verify and decode refresh token."""
        return verify_token(token)
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """Get current user from access token."""
        payload = AuthService.verify_access_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return UserService.get_by_id(db, int(user_id))
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[dict]:
        """Create new access token from refresh token."""
        # Use blacklist-aware verification for refresh tokens
        payload = verify_token_with_blacklist(refresh_token, db)
        if not payload:
            return None

        # Verify it's a refresh token
        if payload.get("typ") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = UserService.get_by_id(db, int(user_id))
        if not user or user.status != "active":
            return None

        # Create new access token
        access_token = create_access_token(subject=str(user.id))

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    @staticmethod
    def blacklist_token(db: Session, token: str) -> bool:
        """Blacklist a token by adding it to the blacklist."""
        from app.services.token_blacklist_service import TokenBlacklistService

        # Verify token to get claims
        payload = verify_token(token)
        if not payload:
            return False

        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            return False

        # Convert exp timestamp to datetime
        expires_at = datetime.fromtimestamp(exp, tz=datetime.now().astimezone().tzinfo)

        return TokenBlacklistService.blacklist_token(db, jti, expires_at)
    
    @staticmethod
    def register_user(
        db: Session, 
        username: str, 
        password: str, 
        role_name: str = "user"
    ) -> Optional[User]:
        """Register a new user with default role."""
        # Check if username already exists
        existing_user = UserService.get_by_username(db, username)
        if existing_user:
            return None
        
        # Get default role
        default_role = RoleService.get_by_name(db, role_name)
        if not default_role:
            return None
        
        # Create user
        user = UserService.create(
            db=db,
            username=username,
            password=password,
            role_id=default_role.id
        )
        
        return user
