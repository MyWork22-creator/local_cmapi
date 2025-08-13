"""
FastAPI dependencies for authentication and authorization.
"""
import jwt
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.core.security import verify_token, TokenData
from app.core.config import settings

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    try:
        # CORRECTED: Use credentials.credentials to access the token string
        payload = jwt.decode(
            credentials.credentials,  # Changed from credentials.token
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: int = payload.get("sub") 
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: 'sub' claim missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user (alias for get_current_user).
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Current active user
    """
    return current_user


def require_permissions(required_permissions: List[str]):
    """
    Dependency factory to require specific permissions.
    
    Args:
        required_permissions: List of required permission strings
        
    Returns:
        Dependency function that checks permissions
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """
        Check if current user has required permissions.
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            Current user if permissions are satisfied
            
        Raises:
            HTTPException: If user lacks required permissions
        """
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )
        
        # Get user permissions through role
        user_permissions = []
        for permission in current_user.role.permissions:
            permission_string = f"{permission.name}"
            user_permissions.append(permission_string)
        
        # Check if user has all required permissions
        missing_permissions = set(required_permissions) - set(user_permissions)
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    
    Args:
        required_role: Required role name
        
    Returns:
        Dependency function that checks role
    """
    def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Check if current user has required role.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Current user if role is satisfied
            
        Raises:
            HTTPException: If user lacks required role
        """
        if not current_user.role or current_user.role.name != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


def require_any_role(required_roles: List[str]):
    """
    Dependency factory to require any of the specified roles.
    
    Args:
        required_roles: List of acceptable role names
        
    Returns:
        Dependency function that checks roles
    """
    def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Check if current user has any of the required roles.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Current user if role is satisfied
            
        Raises:
            HTTPException: If user lacks any required role
        """
        if not current_user.role or current_user.role.name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    
    try:
        # CORRECTED: Pass credentials.credentials to verify_token
        payload = verify_token(credentials.credentials) 
        
        if not payload:
            return None
        
        # CORRECTED: Use .get('sub') to retrieve the user ID from the payload
        user_id = payload.get('sub')
        
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.status:
            return user
    except HTTPException:
        pass
    
    return None