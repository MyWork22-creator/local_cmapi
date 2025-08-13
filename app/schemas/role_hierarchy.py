"""Schemas for role hierarchy management."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.core.input_validation import SecurityValidator


class RoleHierarchyCreate(BaseModel):
    """Schema for creating a role with hierarchy."""
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return SecurityValidator.validate_role_name(v)
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return SecurityValidator.validate_description(v)
        return v


class RoleHierarchyUpdate(BaseModel):
    """Schema for updating role hierarchy."""
    parent_id: Optional[int] = None


class PermissionInfo(BaseModel):
    """Schema for permission information."""
    id: int
    name: str
    description: Optional[str] = None


class RoleHierarchyInfo(BaseModel):
    """Schema for role hierarchy path information."""
    id: int
    name: str
    level: int


class RoleWithHierarchy(BaseModel):
    """Schema for role with complete hierarchy information."""
    id: int
    name: str
    description: Optional[str]
    level: int
    parent_id: Optional[int]
    parent_name: Optional[str]
    direct_permissions: List[PermissionInfo]
    inherited_permissions: List[PermissionInfo]
    all_permissions: List[PermissionInfo]
    hierarchy_path: List[RoleHierarchyInfo]
    children: List[RoleHierarchyInfo]


class RoleTreeNode(BaseModel):
    """Schema for role hierarchy tree node."""
    id: int
    name: str
    description: Optional[str]
    level: int
    direct_permissions: List[str]
    all_permissions: List[str]
    children: List['RoleTreeNode'] = []


class RolePermissionAnalysis(BaseModel):
    """Schema for role permission analysis."""
    id: int
    name: str
    level: int
    has_direct: bool
    has_inherited: bool
    inherited_from: Optional[str] = None


class HierarchyIntegrityIssue(BaseModel):
    """Schema for hierarchy integrity issues."""
    type: str
    role_id: int
    role_name: str
    description: str
    current_level: Optional[int] = None
    expected_level: Optional[int] = None


class HierarchyValidationResult(BaseModel):
    """Schema for hierarchy validation results."""
    is_valid: bool
    issues: List[HierarchyIntegrityIssue]
    total_roles: int
    issues_count: int


class EffectivePermissions(BaseModel):
    """Schema for user's effective permissions."""
    user_id: int
    username: str
    role_id: Optional[int]
    role_name: Optional[str]
    role_level: Optional[int]
    permissions: List[str]
    permission_count: int


class HierarchyStats(BaseModel):
    """Schema for hierarchy statistics."""
    total_roles: int
    root_roles: int
    max_depth: int
    total_permissions: int
    roles_by_level: Dict[int, int]
    permission_distribution: Dict[str, int]


# Update forward references
RoleTreeNode.model_rebuild()
