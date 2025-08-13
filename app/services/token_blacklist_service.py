from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete
from app.models.token_blacklist import TokenBlacklist


class TokenBlacklistService:
    """Service layer for token blacklist operations."""
    
    @staticmethod
    def blacklist_token(db: Session, jti: str, expires_at: datetime) -> bool:
        """Add a token to the blacklist."""
        try:
            blacklisted_token = TokenBlacklist(
                jti=jti,
                expires_at=expires_at
            )
            db.add(blacklisted_token)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def is_token_blacklisted(db: Session, jti: str) -> bool:
        """Check if a token is blacklisted."""
        blacklisted_token = db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti
        ).first()
        return blacklisted_token is not None
    
    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Remove expired tokens from blacklist to keep the table clean."""
        now = datetime.now(timezone.utc)
        result = db.execute(
            delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
        )
        db.commit()
        return result.rowcount
    
    @staticmethod
    def get_blacklisted_token(db: Session, jti: str) -> Optional[TokenBlacklist]:
        """Get a blacklisted token by JTI."""
        return db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti
        ).first()
