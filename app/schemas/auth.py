from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    permissions: List[str] = []

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    user_name: str
    status: str
    role_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[int] = None

class UserStatusUpdate(BaseModel):
    status: str

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    permissions: List[dict] = []

    class Config:
        from_attributes = True

class PermissionOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

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
