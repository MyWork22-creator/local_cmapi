from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_db, 
    get_current_user, 
    check_permissions, 
    check_any_permission,
    get_user_permissions,
    get_user_role,
    require_role
)
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission

router = APIRouter()


@router.get("/rbac/current-user-info")
async def get_current_user_rbac_info(
    current_user: User = Depends(get_current_user),
    permissions: List[str] = Depends(get_user_permissions),
    role: str = Depends(get_user_role),
) -> Dict[str, Any]:
    """Get current user's RBAC information. No permissions required."""
    return {
        "user_id": current_user.id,
        "username": current_user.user_name,
        "status": current_user.status,
        "role": role,
        "permissions": permissions,
        "permission_count": len(permissions)
    }


@router.get("/rbac/test-permission-check")
async def test_permission_check(
    _: bool = Depends(check_permissions(["users:read"])),
) -> Dict[str, str]:
    """Test endpoint that requires users:read permission."""
    return {"message": "Permission check passed! You have users:read permission."}


@router.get("/rbac/test-any-permission")
async def test_any_permission(
    _: bool = Depends(check_any_permission(["users:write", "roles:write"])),
) -> Dict[str, str]:
    """Test endpoint that requires ANY of the specified permissions (OR logic)."""
    return {"message": "Any permission check passed! You have at least one of the required permissions."}


@router.get("/rbac/test-admin-role")
async def test_admin_role(
    _: bool = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Test endpoint that requires admin role specifically."""
    return {"message": "Admin role check passed! You are an admin."}


@router.get("/rbac/test-user-role")
async def test_user_role(
    _: bool = Depends(require_role("user")),
) -> Dict[str, str]:
    """Test endpoint that requires user role specifically."""
    return {"message": "User role check passed! You are a regular user."}


@router.get("/rbac/test-multiple-permissions")
async def test_multiple_permissions(
    _: bool = Depends(check_permissions(["users:read", "roles:read"])),
) -> Dict[str, str]:
    """Test endpoint that requires multiple permissions (AND logic)."""
    return {"message": "Multiple permissions check passed! You have all required permissions."}


@router.get("/rbac/permission-hierarchy")
async def get_permission_hierarchy(
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:read"])),
) -> Dict[str, Any]:
    """Get the complete RBAC hierarchy. Requires roles:read permission."""
    roles = db.query(Role).all()
    
    hierarchy = {}
    for role in roles:
        hierarchy[role.name] = {
            "id": role.id,
            "description": role.description,
            "permissions": [p.name for p in role.permissions],
            "user_count": len(role.users)
        }
    
    return {
        "total_roles": len(roles),
        "hierarchy": hierarchy
    }


@router.get("/rbac/user-permissions/{user_id}")
async def get_user_permissions_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:read", "roles:read"])),
) -> Dict[str, Any]:
    """Get detailed RBAC information for a specific user. Requires users:read and roles:read permissions."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = user.role
    permissions = [p.name for p in role.permissions] if role else []
    
    return {
        "user_id": user.id,
        "username": user.user_name,
        "status": user.status,
        "role": {
            "id": role.id if role else None,
            "name": role.name if role else None,
            "description": role.description if role else None
        } if role else None,
        "permissions": permissions,
        "permission_count": len(permissions)
    }


@router.get("/rbac/role-permissions/{role_id}")
async def get_role_permissions_by_id(
    role_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:read"])),
) -> Dict[str, Any]:
    """Get detailed permission information for a specific role. Requires roles:read permission."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    permissions = [{"id": p.id, "name": p.name, "description": p.description} for p in role.permissions]
    users = [{"id": u.id, "username": u.user_name, "status": u.status} for u in role.users]
    
    return {
        "role_id": role.id,
        "role_name": role.name,
        "description": role.description,
        "permissions": permissions,
        "permission_count": len(permissions),
        "users": users,
        "user_count": len(users)
    }


@router.get("/rbac/validate-access")
async def validate_user_access(
    required_permissions: str,  # Query parameter: "users:read,roles:write"
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Validate if current user has access to specific permissions. No permissions required."""
    required_perms = [p.strip() for p in required_permissions.split(",") if p.strip()]
    user_permissions = [p.name for p in current_user.role.permissions] if current_user.role else []
    
    has_all = all(perm in user_permissions for perm in required_perms)
    has_any = any(perm in user_permissions for perm in required_perms)
    
    return {
        "user_id": current_user.id,
        "username": current_user.user_name,
        "role": current_user.role.name if current_user.role else None,
        "user_permissions": user_permissions,
        "required_permissions": required_perms,
        "has_all_permissions": has_all,
        "has_any_permission": has_any,
        "missing_permissions": [p for p in required_perms if p not in user_permissions]
    }
