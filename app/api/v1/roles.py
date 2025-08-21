from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.role import Role

from app.api.deps import get_db, check_permissions
from app.services import RoleService
from app.models.permission import Permission
from app.schemas.auth import RoleCreate, RoleUpdate, RoleOut, PermissionOut, RolePermissionAssignment

router = APIRouter()


@router.get("/roles", response_model=List[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:read"])),
) -> List[RoleOut]:
    """List all roles. Requires roles:read permission."""
    roles = RoleService.get_all(db)
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


@router.post(
    "/roles",
    response_model=RoleOut,
    summary="Create Role",
    description="Create a new role with name and optional description",
    responses={
        200: {
            "description": "Role created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 3,
                        "name": "moderator",
                        "description": "Content moderator role",
                        "created_at": "2025-08-12T10:30:00Z",
                        "updated_at": "2025-08-12T10:30:00Z",
                        "permissions": []
                    }
                }
            }
        },
        400: {"description": "Role name already exists"},
        403: {"description": "Insufficient permissions (requires roles:create)"}
    }
)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:create"])),
) -> RoleOut:
    """
    Create a new role.

    **Request Body:**
    - **name**: Unique role name (required)
    - **description**: Optional role description

    **Permissions Required:** `roles:create`

    **Example:**
    ```json
    {
        "name": "moderator",
        "description": "Content moderator with limited admin rights"
    }
    ```

    **Note:** New roles are created without any permissions. Use the assign permissions endpoint to add permissions.
    """
    # Check if role already exists
    existing_role = RoleService.get_by_name(db, role_data.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )

    try:
        role = RoleService.create(db, role_data.name, role_data.description, role_data.parent_id)
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/roles/{role_id}",
    response_model=RoleOut,
    summary="Update Role",
    description="Update role name and/or description",
    responses={
        200: {
            "description": "Role updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 3,
                        "name": "updated_moderator",
                        "description": "Updated moderator role description",
                        "created_at": "2025-08-12T10:30:00Z",
                        "updated_at": "2025-08-12T11:00:00Z",
                        "permissions": []
                    }
                }
            }
        },
        400: {"description": "Role name already exists"},
        403: {"description": "Insufficient permissions (requires roles:update)"},
        404: {"description": "Role not found"}
    }
)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:update"])),
) -> RoleOut:
    """
    Update an existing role.

    **Path Parameters:**
    - **role_id**: ID of the role to update

    **Request Body (all fields optional):**
    - **name**: New role name (must be unique)
    - **description**: New role description

    **Permissions Required:** `roles:update`

    **Example:**
    ```json
    {
        "name": "senior_moderator",
        "description": "Senior moderator with additional privileges"
    }
    ```
    """
    # Check if new name conflicts with existing role
    if role_data.name is not None:
        existing_role = RoleService.get_by_name(db, role_data.name)
        if existing_role and existing_role.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )

    role = RoleService.update(
        db=db,
        role_id=role_id,
        name=role_data.name,
        description=role_data.description
    )

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return role


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:delete"])),
):
    """Delete role. Requires roles:delete permission."""
    role = RoleService.get_by_id(db, role_id)
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

    success = RoleService.delete(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    return {"message": "Role deleted successfully"}


@router.post(
    "/roles/{role_id}/permissions",
    summary="Assign Permissions to Role",
    description="Assign one or more permissions to a role (replaces existing permissions)",
    responses={
        200: {
            "description": "Permissions assigned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Permissions assigned successfully",
                        "role_id": 3,
                        "assigned_permissions": [1, 2, 4]
                    }
                }
            }
        },
        400: {"description": "Invalid permission IDs"},
        403: {"description": "Insufficient permissions (requires roles:create)"},
        404: {"description": "Role not found"}
    }
)
def assign_permissions_to_role(
    role_id: int,
    permission_data: RolePermissionAssignment,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["roles:create"])),
):
    """
    Assign permissions to a role.

    **Path Parameters:**
    - **role_id**: ID of the role to assign permissions to

    **Request Body:**
    - **permission_ids**: List of permission IDs to assign to the role

    **Permissions Required:** `roles:create`

    **Example:**
    ```json
    {
        "permission_ids": [1, 2, 4]
    }
    ```

    **Note:** This replaces all existing permissions for the role with the provided list.
    """
    if not permission_data.permission_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission IDs are required"
        )

    success = RoleService.assign_permissions(db, role_id, permission_data.permission_ids)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role not found or some permissions not found"
        )

    return {
        "message": "Permissions assigned successfully",
        "role_id": role_id,
        "assigned_permissions": permission_data.permission_ids
    }





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
