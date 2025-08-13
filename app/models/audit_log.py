from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    """Model for storing audit logs of security events."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # login, logout, password_change, etc.
    resource = Column(String(100), nullable=True, index=True)  # user, role, permission, etc.
    resource_id = Column(String(50), nullable=True)  # ID of the affected resource
    details = Column(Text, nullable=True)  # JSON string with additional details
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)  # Browser/client information
    status = Column(String(20), nullable=False, index=True)  # success, failure, error
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", backref="audit_logs", lazy="select")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_timestamp_action', 'timestamp', 'action'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'timestamp'),
        Index('idx_audit_status_timestamp', 'status', 'timestamp'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, status={self.status})>"
