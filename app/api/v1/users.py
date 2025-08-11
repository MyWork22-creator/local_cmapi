from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, check_permissions
from app.models.user import User
from app.schemas.auth import UserOut, UserUpdate, UserStatusUpdate, UserWithRole

router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:read"])),
) -> List[UserOut]:
    """List all users. Requires users:read permission."""
    users = db.query(User).all()
    return users


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:read"])),
) -> UserOut:
    """Get specific user by ID. Requires users:read permission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:write"])),
) -> UserOut:
    """Update user information. Requires users:write permission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update user fields
    if user_update.username is not None:
        # Check if new username conflicts with existing user
        existing_user = db.query(User).filter(User.user_name == user_update.username, User.id != user_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.user_name = user_update.username
    
    if user_update.status is not None:
        if user_update.status not in ["active", "inactive", "suspended"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be 'active', 'inactive', or 'suspended'"
            )
        user.status = user_update.status
    
    if user_update.role_id is not None:
        # Verify role exists
        from app.models.role import Role
        role = db.query(Role).filter(Role.id == user_update.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not found"
            )
        user.role_id = user_update.role_id
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:delete"])),
):
    """Delete user. Requires users:delete permission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:write"])),
):
    """Update user status. Requires users:write permission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if status_update.status not in ["active", "inactive", "suspended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'active', 'inactive', or 'suspended'"
        )
    
    user.status = status_update.status
    db.commit()
    db.refresh(user)
    return {"message": f"User status updated to {status_update.status}", "user_id": user_id}


@router.get("/users/{user_id}/with-role", response_model=UserWithRole)
def get_user_with_role(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:read"])),
) -> UserWithRole:
    """Get user with full role information. Requires users:read permission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


