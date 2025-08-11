from datetime import datetime, timedelta, timezone
from typing import Optional, Literal, Dict, Any
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    claims = _build_claims(
        subject=subject,
        token_type="refresh",
        expires_in_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
