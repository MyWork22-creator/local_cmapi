from typing import List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import oauth2_scheme, verify_token_with_blacklist
from app.database import SessionLocal
from app.models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token with blacklist checking
    payload = verify_token_with_blacklist(token, db)
    if not payload:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    token_type: str = payload.get("typ")
    if user_id_str is None:
        raise credentials_exception
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert user_id from string to int
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    return user

def check_permissions(required_permissions: List[str]):
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )

        # Get all permissions including inherited ones from role hierarchy
        user_permissions = set(current_user.role.get_permission_names())

        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {', '.join(required_permissions)}"
            )
        return current_user
    return permission_checker

def require_admin(current_user: User = Depends(get_current_user)) -> bool:
    """Allow access only to users with role name 'admin'."""
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return True

def require_role(role_name: str):
    """Allow access only to users with a specific role."""
    def role_checker(current_user: User = Depends(get_current_user)) -> bool:
        if not current_user.role or current_user.role.name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required",
            )
        return True
    return role_checker

def check_any_permission(required_permissions: List[str]):
    """Allow access if user has ANY of the required permissions (OR logic)."""
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> bool:
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )

        # Get all permissions including inherited ones from role hierarchy
        user_permissions = set(current_user.role.get_permission_names())

        if not any(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required one of: {', '.join(required_permissions)}"
            )
        return True
    return permission_checker

def get_user_permissions(current_user: User = Depends(get_current_user)) -> List[str]:
    """Get all permissions for the current user."""
    return [
        permission.name 
        for role in [current_user.role] 
        for permission in role.permissions
    ]

def get_user_role(current_user: User = Depends(get_current_user)) -> str:
    """Get the role name for the current user."""
    return current_user.role.name if current_user.role else "no_role"
