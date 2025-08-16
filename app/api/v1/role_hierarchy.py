"""Role hierarchy management endpoints."""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin, get_current_user
from app.services import RoleService, RoleHierarchyService
from app.models.user import User
from app.schemas.role_hierarchy import (
    RoleHierarchyCreate, RoleHierarchyUpdate, RoleWithHierarchy,
    RoleTreeNode, RolePermissionAnalysis, HierarchyValidationResult,
    EffectivePermissions, HierarchyStats
)

router = APIRouter()


@router.get(
    "/hierarchy/tree",
    response_model=List[RoleTreeNode],
    summary="Get Role Hierarchy Tree",
    description="Get the complete role hierarchy as a tree structure"
)
async def get_role_hierarchy_tree(
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> List[RoleTreeNode]:
    """
    Get the complete role hierarchy tree.
    
    **Admin Only Endpoint**
    
    **Returns:**
    - Tree structure showing all roles and their relationships
    - Each node includes direct and inherited permissions
    - Hierarchical organization from root to leaf roles
    """
    tree = RoleService.get_hierarchy_tree(db)
    return tree


@router.get(
    "/hierarchy/{role_id}",
    response_model=RoleWithHierarchy,
    summary="Get Role with Hierarchy Info",
    description="Get detailed role information including hierarchy and inherited permissions"
)
async def get_role_hierarchy_info(
    role_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> RoleWithHierarchy:
    """
    Get detailed role information with hierarchy context.
    
    **Admin Only Endpoint**
    
    **Path Parameters:**
    - **role_id**: ID of the role to get information for
    
    **Returns:**
    - Complete role information including:
      - Direct permissions (assigned to this role)
      - Inherited permissions (from parent roles)
      - All effective permissions
      - Hierarchy path from root to this role
      - Child roles
    """
    role_info = RoleService.get_role_with_hierarchy(db, role_id)
    if not role_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    return RoleWithHierarchy(**role_info)


@router.post(
    "/hierarchy",
    response_model=RoleWithHierarchy,
    summary="Create Role with Parent",
    description="Create a new role with optional parent role for hierarchy"
)
async def create_role_with_hierarchy(
    role_data: RoleHierarchyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_admin)
) -> RoleWithHierarchy:
    """
    Create a new role with optional parent role.
    
    **Admin Only Endpoint**
    
    **Request Body:**
    - **name**: Role name (unique)
    - **description**: Optional role description
    - **parent_id**: Optional parent role ID for hierarchy
    
    **Returns:**
    - Created role with complete hierarchy information
    
    **Notes:**
    - If parent_id is provided, the role will inherit all parent permissions
    - Role level is automatically calculated based on hierarchy depth
    - Circular references are prevented
    """
    try:
        role = RoleService.create(
            db=db,
            name=role_data.name,
            description=role_data.description,
            parent_id=role_data.parent_id
        )
        
        # Get complete hierarchy info
        role_info = RoleService.get_role_with_hierarchy(db, role.id)
        return RoleWithHierarchy(**role_info)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/hierarchy/{role_id}/parent",
    response_model=RoleWithHierarchy,
    summary="Update Role Parent",
    description="Change the parent role of an existing role"
)
async def update_role_parent(
    role_id: int,
    update_data: RoleHierarchyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_admin)
) -> RoleWithHierarchy:
    """
    Change the parent role of an existing role.
    
    **Admin Only Endpoint**
    
    **Path Parameters:**
    - **role_id**: ID of the role to update
    
    **Request Body:**
    - **parent_id**: New parent role ID (null to make it a root role)
    
    **Returns:**
    - Updated role with new hierarchy information
    
    **Notes:**
    - Prevents circular references
    - Automatically updates hierarchy levels
    - Cannot set a descendant as parent
    """
    try:
        role = RoleService.set_parent_role(db, role_id, update_data.parent_id)
        role_info = RoleService.get_role_with_hierarchy(db, role.id)
        return RoleWithHierarchy(**role_info)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/hierarchy/permission/{permission_name}",
    response_model=List[RolePermissionAnalysis],
    summary="Find Roles with Permission",
    description="Find all roles that have a specific permission (direct or inherited)"
)
async def find_roles_with_permission(
    permission_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> List[RolePermissionAnalysis]:
    """
    Find all roles that have a specific permission.
    
    **Admin Only Endpoint**
    
    **Path Parameters:**
    - **permission_name**: Name of the permission to search for
    
    **Returns:**
    - List of roles with the permission
    - Indicates whether permission is direct or inherited
    - Shows which ancestor role provides inherited permissions
    """
    roles = RoleHierarchyService.find_roles_with_permission(db, permission_name)
    return [RolePermissionAnalysis(**role) for role in roles]


@router.get(
    "/hierarchy/user/{user_id}/permissions",
    response_model=EffectivePermissions,
    summary="Get User Effective Permissions",
    description="Get all effective permissions for a user including inherited ones"
)
async def get_user_effective_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> EffectivePermissions:
    """
    Get all effective permissions for a user.
    
    **Admin Only Endpoint**
    
    **Path Parameters:**
    - **user_id**: ID of the user to get permissions for
    
    **Returns:**
    - User information with all effective permissions
    - Includes permissions inherited through role hierarchy
    """
    from app.models.user import User
    
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    permissions = RoleHierarchyService.get_effective_permissions_for_user(db, user_id)
    
    return EffectivePermissions(
        user_id=user.id,
        username=user.user_name,
        role_id=user.role_id,
        role_name=user.role.name if user.role else None,
        role_level=user.role.level if user.role else None,
        permissions=list(permissions),
        permission_count=len(permissions)
    )


@router.get(
    "/hierarchy/validate",
    response_model=HierarchyValidationResult,
    summary="Validate Hierarchy Integrity",
    description="Check the integrity of the role hierarchy"
)
async def validate_hierarchy_integrity(
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> HierarchyValidationResult:
    """
    Validate the integrity of the role hierarchy.
    
    **Admin Only Endpoint**
    
    **Returns:**
    - Validation results with any issues found
    - Issues include circular references, incorrect levels, etc.
    - Summary of total roles and issues
    """
    issues = RoleHierarchyService.validate_hierarchy_integrity(db)
    total_roles = len(RoleService.get_all(db))
    
    return HierarchyValidationResult(
        is_valid=len(issues) == 0,
        issues=issues,
        total_roles=total_roles,
        issues_count=len(issues)
    )


@router.post(
    "/hierarchy/fix-levels",
    summary="Fix Hierarchy Levels",
    description="Fix incorrect hierarchy levels in the role system"
)
async def fix_hierarchy_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_admin)
) -> Any:
    """
    Fix incorrect hierarchy levels.
    
    **Admin Only Endpoint**
    
    **Returns:**
    - Number of roles that were fixed
    
    **Warning:** This operation modifies role data. Use with caution.
    """
    fixed_count = RoleHierarchyService.fix_hierarchy_levels(db)

    return {
        "message": f"Fixed hierarchy levels for {fixed_count} roles",
        "fixed_count": fixed_count
    }
