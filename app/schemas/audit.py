"""Schemas for audit logging."""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class AuditLogOut(BaseModel):
    """Schema for audit log output."""
    id: int
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SecuritySummary(BaseModel):
    """Schema for security analysis summary."""
    failed_login_count: int
    suspicious_ips: Dict[str, int]
    password_change_attempts: int
    analysis_period_hours: int
    timestamp: str


class AuditLogCreate(BaseModel):
    """Schema for creating audit logs."""
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "success"
