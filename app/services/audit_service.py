"""Audit logging service for tracking security events."""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from fastapi import Request
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """Service for audit logging and security event tracking."""
    
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log a security or audit event.
        
        Args:
            db: Database session
            action: Action performed (login, logout, password_change, etc.)
            user_id: ID of the user performing the action
            resource: Type of resource affected (user, role, permission, etc.)
            resource_id: ID of the affected resource
            details: Additional details as a dictionary
            ip_address: Client IP address
            user_agent: Client user agent
            status: Event status (success, failure, error)
            request: FastAPI request object (for extracting IP and user agent)
            
        Returns:
            Created AuditLog instance
        """
        # Extract IP and user agent from request if provided
        if request:
            if not ip_address:
                ip_address = AuditService._get_client_ip(request)
            if not user_agent:
                user_agent = request.headers.get("user-agent", "")
        
        # Convert details to JSON string
        details_json = None
        if details:
            try:
                details_json = json.dumps(details, default=str)
            except Exception:
                details_json = str(details)
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def log_authentication_event(
        db: Session,
        action: str,  # login, logout, password_change, etc.
        username: Optional[str] = None,
        user_id: Optional[int] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log authentication-related events."""
        auth_details = details or {}
        if username:
            auth_details["username"] = username
        
        return AuditService.log_event(
            db=db,
            action=action,
            user_id=user_id,
            resource="authentication",
            details=auth_details,
            status=status,
            request=request
        )
    
    @staticmethod
    def log_user_management_event(
        db: Session,
        action: str,  # create_user, update_user, delete_user, etc.
        target_user_id: int,
        admin_user_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        status: str = "success",
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log user management events."""
        details = changes or {}
        details["target_user_id"] = target_user_id
        
        return AuditService.log_event(
            db=db,
            action=action,
            user_id=admin_user_id,
            resource="user",
            resource_id=str(target_user_id),
            details=details,
            status=status,
            request=request
        )
    
    @staticmethod
    def log_permission_event(
        db: Session,
        action: str,  # assign_role, revoke_permission, etc.
        user_id: Optional[int] = None,
        role_id: Optional[int] = None,
        permission_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log permission and role management events."""
        perm_details = details or {}
        if role_id:
            perm_details["role_id"] = role_id
        if permission_id:
            perm_details["permission_id"] = permission_id
        
        return AuditService.log_event(
            db=db,
            action=action,
            user_id=user_id,
            resource="permission",
            details=perm_details,
            status=status,
            request=request
        )
    
    @staticmethod
    def get_user_audit_logs(
        db: Session,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[str] = None,
        days_back: Optional[int] = None
    ) -> List[AuditLog]:
        """Get audit logs for a specific user."""
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        
        if days_back:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = query.filter(AuditLog.timestamp >= cutoff_date)
        
        return query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_security_events(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        status_filter: Optional[str] = None,
        action_filter: Optional[str] = None,
        ip_filter: Optional[str] = None,
        days_back: int = 7
    ) -> List[AuditLog]:
        """Get security events for monitoring."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff_date)
        
        if status_filter:
            query = query.filter(AuditLog.status == status_filter)
        
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        
        if ip_filter:
            query = query.filter(AuditLog.ip_address == ip_filter)
        
        return query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_failed_login_attempts(
        db: Session,
        hours_back: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent failed login attempts for security monitoring."""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours_back)
        
        return db.query(AuditLog).filter(
            and_(
                AuditLog.action == "login",
                AuditLog.status == "failure",
                AuditLog.timestamp >= cutoff_date
            )
        ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_suspicious_activity(
        db: Session,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Analyze recent activity for suspicious patterns."""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Get failed login attempts
        failed_logins = db.query(AuditLog).filter(
            and_(
                AuditLog.action == "login",
                AuditLog.status == "failure",
                AuditLog.timestamp >= cutoff_date
            )
        ).all()
        
        # Analyze by IP address
        ip_failures = {}
        for log in failed_logins:
            if log.ip_address:
                ip_failures[log.ip_address] = ip_failures.get(log.ip_address, 0) + 1
        
        # Find IPs with many failures
        suspicious_ips = {ip: count for ip, count in ip_failures.items() if count >= 5}
        
        # Get password change attempts
        password_changes = db.query(AuditLog).filter(
            and_(
                AuditLog.action == "password_change",
                AuditLog.timestamp >= cutoff_date
            )
        ).count()
        
        return {
            "failed_login_count": len(failed_logins),
            "suspicious_ips": suspicious_ips,
            "password_change_attempts": password_changes,
            "analysis_period_hours": hours_back,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def cleanup_old_logs(db: Session, days_to_keep: int = 90) -> int:
        """Clean up old audit logs to manage database size."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        return deleted_count
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
