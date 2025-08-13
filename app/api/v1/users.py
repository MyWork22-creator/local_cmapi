from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, check_permissions, require_admin
from app.services import UserService
from app.schemas.auth import UserOut, UserUpdate, UserStatusUpdate, UserWithRole, AdminUserCreate

router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:read"])),
) -> List[UserOut]:
    """List all users. Requires users:read permission."""
    users = UserService.get_all(db)
    return users


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:read"])),
) -> UserOut:
    """Get specific user by ID. Requires users:read permission."""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put(
    "/users/{user_id}",
    response_model=UserOut,
    summary="Update User",
    description="Update user information (username, status, or role)",
    responses={
        200: {
            "description": "User updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_name": "updated_username",
                        "status": "active",
                        "role_id": 2,
                        "created_at": "2025-08-12T10:00:00Z",
                        "updated_at": "2025-08-12T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid data (username taken, invalid status, role not found)"},
        403: {"description": "Insufficient permissions (requires users:write)"},
        404: {"description": "User not found"}
    }
)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:write"])),
) -> UserOut:
    """
    Update user information.

    **Path Parameters:**
    - **user_id**: ID of the user to update

    **Request Body (all fields optional):**
    - **username**: New username (must be unique)
    - **status**: User status ('active', 'inactive', or 'suspended')
    - **role_id**: ID of the role to assign to the user

    **Permissions Required:** `users:write`

    **Example:**
    ```json
    {
        "username": "new_username",
        "status": "active",
        "role_id": 2
    }
    ```
    """
    # Check if username conflicts with existing user
    if user_update.username is not None:
        existing_user = UserService.get_by_username(db, user_update.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Validate status
    if user_update.status is not None:
        if user_update.status not in ["active", "inactive", "suspended"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be 'active', 'inactive', or 'suspended'"
            )

    # Verify role exists if provided
    if user_update.role_id is not None:
        from app.services import RoleService
        role = RoleService.get_by_id(db, user_update.role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not found"
            )

    user = UserService.update(
        db=db,
        user_id=user_id,
        username=user_update.username,
        status=user_update.status,
        role_id=user_update.role_id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.delete(
    "/users/{user_id}",
    summary="Delete User",
    description="Permanently delete a user account",
    responses={
        200: {
            "description": "User deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "User deleted successfully"}
                }
            }
        },
        403: {"description": "Insufficient permissions (requires users:delete)"},
        404: {"description": "User not found"}
    }
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:delete"])),
):
    """
    Permanently delete a user account.

    **Path Parameters:**
    - **user_id**: ID of the user to delete

    **Permissions Required:** `users:delete`

    **Warning:** This action is irreversible and will permanently remove the user and all associated data.
    """
    success = UserService.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User deleted successfully"}


@router.patch(
    "/users/{user_id}/status",
    summary="Update User Status",
    description="Update only the status of a user account",
    responses={
        200: {
            "description": "User status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User status updated to active",
                        "user_id": 1
                    }
                }
            }
        },
        400: {"description": "Invalid status value"},
        403: {"description": "Insufficient permissions (requires users:write)"},
        404: {"description": "User not found"}
    }
)
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:write"])),
):
    """
    Update only the status of a user account.

    **Path Parameters:**
    - **user_id**: ID of the user to update

    **Request Body:**
    - **status**: New status ('active', 'inactive', or 'suspended')

    **Permissions Required:** `users:write`

    **Example:**
    ```json
    {
        "status": "active"
    }
    ```
    """
    if status_update.status not in ["active", "inactive", "suspended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'active', 'inactive', or 'suspended'"
        )

    user = UserService.update_status(db, user_id, status_update.status)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"User status updated to {status_update.status}", "user_id": user_id}


@router.get("/users/{user_id}/with-role", response_model=UserWithRole)
def get_user_with_role(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["users:read"])),
) -> UserWithRole:
    """Get user with full role information. Requires users:read permission."""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post(
    "/users",
    response_model=UserOut,
    summary="Create User (Admin Only)",
    description="Create a new user account. Only admin users can create accounts.",
    responses={
        200: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 3,
                        "user_name": "newuser",
                        "status": "active",
                        "role_id": 2,
                        "created_at": "2025-08-12T10:30:00Z",
                        "updated_at": "2025-08-12T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Username already exists or role not found"},
        403: {"description": "Admin role required"},
        500: {"description": "Server error"}
    }
)
def create_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
) -> UserOut:
    """
    Create a new user account. Only admin users can perform this action.

    **Request Body:**
    - **username**: Unique username (required)
    - **password**: User password (required)
    - **role_id**: ID of the role to assign (optional, defaults to 'user' role)

    **Permissions Required:** Admin role

    **Example:**
    ```json
    {
        "username": "newuser",
        "password": "securepassword123",
        "role_id": 2
    }
    ```

    **Note:** If role_id is not provided, the user will be assigned the default 'user' role.
    """
    # Check if username already exists
    existing_user = UserService.get_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # If role_id is provided, verify it exists
    role_id = user_data.role_id
    if role_id is not None:
        from app.services import RoleService
        role = RoleService.get_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not found"
            )
    else:
        # Get default 'user' role
        from app.services import RoleService
        default_role = RoleService.get_by_name(db, "user")
        if not default_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default 'user' role not found. Please contact administrator."
            )
        role_id = default_role.id

    # Create the user
    user = UserService.create(
        db=db,
        username=user_data.username,
        password=user_data.password,
        role_id=role_id
    )

    return user


