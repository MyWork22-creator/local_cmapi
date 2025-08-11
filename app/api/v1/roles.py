from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, check_permissions
from app.models.role import Role
from app.models.permission import Permission
from app.models.associations import role_permissions
from app.schemas.auth import RoleCreate, RoleUpdate, RoleOut, PermissionOut, RolePermissionAssignment

router = APIRouter()


@router.get("/roles", response_model=List[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:read"])),
) -> List[RoleOut]:
    """List all roles. Requires roles:read permission."""
    roles = db.query(Role).all()
    return roles


@router.get("/roles/{role_id}", response_model=RoleOut)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:read"])),
) -> RoleOut:
    """Get specific role by ID. Requires roles:read permission."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    return role


@router.post("/roles", response_model=RoleOut)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:write"])),
) -> RoleOut:
    """Create new role. Requires roles:write permission."""
    # Check if role already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )
    
    role = Role(name=role_data.name, description=role_data.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return role


@router.put("/roles/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:write"])),
) -> RoleOut:
    """Update role. Requires roles:write permission."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    if role_data.name is not None:
        # Check if new name conflicts with existing role
        existing_role = db.query(Role).filter(Role.name == role_data.name, Role.id != role_id).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )
        role.name = role_data.name
    
    if role_data.description is not None:
        role.description = role_data.description
    
    db.commit()
    db.refresh(role)
    
    return role


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:delete"])),
):
    """Delete role. Requires roles:delete permission."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Check if role is assigned to any users
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role that is assigned to users"
        )
    
    db.delete(role)
    db.commit()
    
    return {"message": "Role deleted successfully"}


@router.post("/roles/{role_id}/permissions")
def assign_permissions_to_role(
    role_id: int,
    permission_data: RolePermissionAssignment,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:write"])),
):
    """Assign permissions to role. Requires roles:write permission."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    if not permission_data.permission_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission IDs are required"
        )
    
    permissions = db.query(Permission).filter(Permission.id.in_(permission_data.permission_ids)).all()
    if len(permissions) != len(permission_data.permission_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some permissions not found"
        )
    
    # Clear existing permissions and assign new ones
    role.permissions = permissions
    db.commit()
    db.refresh(role)
    
    return {"message": "Permissions assigned successfully", "role_id": role_id}


@router.get("/permissions", response_model=List[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:read"])),
) -> List[PermissionOut]:
    """List all permissions. Requires roles:read permission."""
    permissions = db.query(Permission).all()
    return permissions


@router.get("/roles/{role_id}/users")
def get_role_users(
    role_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:read"])),
):
    """Get all users assigned to a specific role. Requires roles:read permission."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    users = [
        {
            "id": user.id,
            "user_name": user.user_name,
            "status": user.status,
            "created_at": user.created_at
        }
        for user in role.users
    ]
    
    return {
        "role_id": role_id,
        "role_name": role.name,
        "users": users,
        "user_count": len(users)
    }
