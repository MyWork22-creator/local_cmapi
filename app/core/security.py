from datetime import datetime, timedelta, timezone
from typing import Optional, Literal, Dict, Any
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from pydantic import BaseModel
from fastapi import HTTPException, status

class TokenData(BaseModel):
    """Token data model for JWT payload."""
    user_id: int | None = None
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[list[str]] = None

# Password hashing (prefer bcrypt for performance/compatibility on Windows)
pwd_context = CryptContext(
    schemes=["bcrypt", "argon2"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# OAuth2 scheme (strict OAuth2 password flow uses form data)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _build_claims(
    subject: str,
    token_type: Literal["access", "refresh"],
    expires_in_minutes: int,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    now = _now()
    payload: Dict[str, Any] = {
        "sub": subject,
        "iss": settings.JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
        "jti": uuid.uuid4().hex,
        "typ": token_type,
    }
    if settings.JWT_AUDIENCE:
        payload["aud"] = settings.JWT_AUDIENCE
    if extra:
        payload.update(extra)
    return payload

def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    claims = _build_claims(
        subject=subject,
        token_type="access",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        extra=extra,
    )
    signing_key = settings.get_signing_key()
    return jwt.encode(claims, signing_key, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    claims = _build_claims(
        subject=subject,
        token_type="refresh",
        expires_in_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    signing_key = settings.get_signing_key()
    return jwt.encode(claims, signing_key, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token (without blacklist checking)."""
    try:
        verification_key = settings.get_verification_key()
        payload = jwt.decode(
            token,
            verification_key,
            algorithms=[settings.ALGORITHM],
            audience=(settings.JWT_AUDIENCE if settings.JWT_AUDIENCE else None),
            issuer=settings.JWT_ISSUER,
        )
        return payload
    except JWTError:
        return None
    except ValueError:
        # Handle key configuration errors
        return None


def verify_token_with_blacklist(token: str, db: Session) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token with blacklist checking."""
    # First verify the token structure and signature
    payload = verify_token(token)
    if not payload:
        return None

    # Check if token is blacklisted
    jti = payload.get("jti")
    if jti:
        # Import here to avoid circular imports
        from app.services.token_blacklist_service import TokenBlacklistService
        if TokenBlacklistService.is_token_blacklisted(db, jti):
            return None

    return payload
