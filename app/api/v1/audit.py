"""Audit log endpoints for security monitoring."""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.services import AuditService
from app.schemas.audit import AuditLogOut, SecuritySummary

router = APIRouter()


@router.get(
    "/audit-logs",
    response_model=List[AuditLogOut],
    summary="Get Audit Logs",
    description="Get audit logs for security monitoring (admin only)"
)
async def get_audit_logs(
    limit: int = Query(100, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    status: Optional[str] = Query(None, description="Filter by status (success/failure)"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    days_back: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> List[AuditLogOut]:
    """
    Get audit logs for security monitoring.
    
    **Admin Only Endpoint**
    
    **Query Parameters:**
    - **limit**: Maximum number of logs (1-1000)
    - **offset**: Number of logs to skip for pagination
    - **action**: Filter by action type (login, logout, password_change, etc.)
    - **status**: Filter by status (success, failure, error)
    - **ip_address**: Filter by specific IP address
    - **days_back**: Number of days to look back (1-90)
    
    **Returns:**
    - List of audit log entries matching the criteria
    """
    logs = AuditService.get_security_events(
        db=db,
        limit=limit,
        offset=offset,
        action_filter=action,
        status_filter=status,
        ip_filter=ip_address,
        days_back=days_back
    )
    return logs


@router.get(
    "/failed-logins",
    response_model=List[AuditLogOut],
    summary="Get Failed Login Attempts",
    description="Get recent failed login attempts for security analysis"
)
async def get_failed_logins(
    hours_back: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    limit: int = Query(100, le=500, description="Maximum number of attempts to return"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> List[AuditLogOut]:
    """
    Get recent failed login attempts.
    
    **Admin Only Endpoint**
    
    **Query Parameters:**
    - **hours_back**: Hours to look back (1-168, default 24)
    - **limit**: Maximum number of attempts (1-500)
    
    **Returns:**
    - List of failed login attempts
    """
    failed_attempts = AuditService.get_failed_login_attempts(
        db=db,
        hours_back=hours_back,
        limit=limit
    )
    return failed_attempts


@router.get(
    "/security-summary",
    response_model=SecuritySummary,
    summary="Get Security Summary",
    description="Get security analysis and suspicious activity summary"
)
async def get_security_summary(
    hours_back: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> SecuritySummary:
    """
    Get security analysis and suspicious activity summary.
    
    **Admin Only Endpoint**
    
    **Query Parameters:**
    - **hours_back**: Hours to analyze (1-168, default 24)
    
    **Returns:**
    - Security summary with suspicious activity analysis
    - Failed login statistics
    - IP address analysis
    - Password change activity
    """
    summary = AuditService.get_suspicious_activity(db=db, hours_back=hours_back)
    return SecuritySummary(**summary)


@router.get(
    "/user-activity/{user_id}",
    response_model=List[AuditLogOut],
    summary="Get User Activity",
    description="Get audit logs for a specific user"
)
async def get_user_activity(
    user_id: int,
    limit: int = Query(100, le=500, description="Maximum number of logs"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    days_back: int = Query(30, ge=1, le=90, description="Days to look back"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> List[AuditLogOut]:
    """
    Get audit logs for a specific user.
    
    **Admin Only Endpoint**
    
    **Path Parameters:**
    - **user_id**: ID of the user to get activity for
    
    **Query Parameters:**
    - **limit**: Maximum number of logs (1-500)
    - **offset**: Number of logs to skip
    - **action**: Filter by action type
    - **days_back**: Days to look back (1-90)
    
    **Returns:**
    - List of audit logs for the specified user
    """
    logs = AuditService.get_user_audit_logs(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        action_filter=action,
        days_back=days_back
    )
    return logs


@router.post(
    "/cleanup-logs",
    summary="Cleanup Old Audit Logs",
    description="Remove old audit logs to manage database size"
)
async def cleanup_audit_logs(
    days_to_keep: int = Query(90, ge=30, le=365, description="Days of logs to keep"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
) -> Any:
    """
    Clean up old audit logs to manage database size.
    
    **Admin Only Endpoint**
    
    **Query Parameters:**
    - **days_to_keep**: Number of days of logs to keep (30-365)
    
    **Returns:**
    - Number of logs deleted
    
    **Warning:** This action is irreversible. Deleted logs cannot be recovered.
    """
    deleted_count = AuditService.cleanup_old_logs(db=db, days_to_keep=days_to_keep)
    
    # Log the cleanup action
    AuditService.log_event(
        db=db,
        action="audit_cleanup",
        resource="audit_log",
        details={"days_to_keep": days_to_keep, "deleted_count": deleted_count},
        status="success"
    )
    
    return {
        "message": f"Successfully deleted {deleted_count} old audit logs",
        "deleted_count": deleted_count,
        "days_kept": days_to_keep
    }
