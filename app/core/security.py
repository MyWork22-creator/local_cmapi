from datetime import datetime, timedelta, timezone
from typing import Optional, Literal, Dict, Any
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from pydantic import BaseModel
from fastapi import HTTPException, status

class TokenData(BaseModel):
    """Token data model for JWT payload."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[list[str]] = None

# Password hashing
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

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

def verify_token(token: str, token_type: str = "access") -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"Decoding token: {token[:10]}... with SECRET_KEY: {settings.SECRET_KEY}, ALGORITHM: {settings.ALGORITHM}")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"Decoded payload: {payload}")
        
        token_type_claim = payload.get("type") or payload.get("typ")
        if token_type_claim != token_type:
            print(f"Invalid token type: {token_type_claim}")
            raise credentials_exception
        
        user_id_str: str = payload.get("sub")
        print(f"User ID string: {user_id_str}")
        if user_id_str is None:
            print("No sub claim in token")
            raise credentials_exception

        # Handle both string and integer conversion
        try:
            user_id = int(user_id_str)  # Try to convert to int
        except (ValueError, TypeError):
            raise credentials_exception  # Fail if conversion fails
       
        token_data = TokenData(
            user_id=user_id,
            username=payload.get("username"),
            role=payload.get("role"),
            permissions=payload.get("permissions", [])
        )
        print(f"Token data: {token_data}")
        return token_data
        
    except JWTError as e:
        print(f"JWT decode error: {e}")
        raise credentials_exception