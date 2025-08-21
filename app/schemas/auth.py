from __future__ import annotations
from typing import Optional, List

from pydantic import BaseModel, EmailStr, field_validator, computed_field, Field
from app.models.user import User # Import the User model

from datetime import datetime
from app.core.input_validation import SecurityValidator

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class UserLogin(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return SecurityValidator.validate_username_for_login(v)

class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return SecurityValidator.validate_username(v)

class AdminUserCreate(BaseModel):
    username: str
    password: str
    role_id: Optional[int] = None  # If not provided, defaults to 'user' role

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return SecurityValidator.validate_username(v)

from app.models.role import Role


class PermissionOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None  # Hierarchy support
    level: int = 0  # Hierarchy level
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    user_name: str
    status: str
    role: RoleOut
    created_at: datetime
    updated_at: datetime
    permissions: List[str] = Field(default_factory=list)

    @field_validator('permissions', mode='before')
    def get_all_permissions(cls, v, values):
        # Support both ORM objects and plain dicts during serialization
        user = getattr(values, 'data', None)

        if not user:
            return []

        # Extract role from either dict or object
        role = None
        if isinstance(user, dict):
            role = user.get('role')
        else:
            role = getattr(user, 'role', None)

        if not role:
            return []

        # If role exposes helper, use it
        if hasattr(role, 'get_permission_names') and callable(getattr(role, 'get_permission_names')):
            try:
                return role.get_permission_names()
            except Exception:
                pass

        # Otherwise, attempt to read permissions list and extract names
        permissions = None
        if isinstance(role, dict):
            permissions = role.get('permissions')
        else:
            permissions = getattr(role, 'permissions', None)

        if isinstance(permissions, list):
            names = []
            for p in permissions:
                if isinstance(p, dict):
                    name = p.get('name')
                    if name:
                        names.append(name)
                else:
                    name = getattr(p, 'name', None)
                    if name:
                        names.append(name)
            return names

        return []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[int] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return SecurityValidator.validate_username(v)
        return v


class UserStatusUpdate(BaseModel):
    status: str


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None  # Support for role hierarchy

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


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return SecurityValidator.validate_role_name(v)
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return SecurityValidator.validate_description(v)
        return v


class RolePermissionAssignment(BaseModel):
    permission_ids: List[int]

class UserWithRole(BaseModel):
    id: int
    user_name: str
    status: str
    role: RoleOut
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    new_password: str
