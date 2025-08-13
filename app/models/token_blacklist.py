from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class TokenBlacklist(Base):
    """Model for storing blacklisted JWT tokens."""
    __tablename__ = "token_blacklist"

    jti = Column(String(32), primary_key=True, index=True)  # JWT ID claim
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Index for efficient cleanup of expired tokens
    __table_args__ = (
        Index('idx_token_blacklist_expires_at', 'expires_at'),
    )

    def __repr__(self):
        return f"<TokenBlacklist(jti={self.jti}, expires_at={self.expires_at})>"
