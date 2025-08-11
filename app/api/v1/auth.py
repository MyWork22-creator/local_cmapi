from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from app.core.config import settings
from app.api.deps import get_db, get_current_user, check_permissions
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import Token, UserCreate, UserOut, UserLogin

router = APIRouter()
security = HTTPBearer()

@router.get("/help", summary="Authentication Help", description="Get help on how to authenticate and use the API")
async def get_auth_help():
    """Get help on how to authenticate and use the API."""
    return {
        "message": "FastAPI RBAC Authentication Guide",
        "steps": [
            "1. Register a new user using POST /api/v1/auth/register",
            "2. Login using POST /api/v1/auth/login with your credentials",
            "3. Copy the access_token from the response",
            "4. Click the 'Authorize' button at the top of this page",
            "5. Enter your token in the format: Bearer <your_access_token>",
            "6. Click 'Authorize' to enable authenticated endpoints",
            "7. You can now access protected endpoints that require authentication"
        ],
        "default_users": {
            "admin": {
                "username": "admin",
                "password": "password123",
                "permissions": "All permissions"
            },
            "user": {
                "username": "user", 
                "password": "password123",
                "permissions": "users:read only"
            }
        },
        "note": "Make sure to run 'python -m app.seeds.seed' first to create default users"
    }

@router.post("/login", response_model=Token, summary="User Login", description="Authenticate user and get access token")
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Any:
    """Login with either JSON or form-encoded credentials."""
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    username: Optional[str] = None
    password: Optional[str] = None

    if content_type == "application/json":
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
    elif content_type in ("application/x-www-form-urlencoded", "multipart/form-data"):
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
    else:
        # Best-effort fallback
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except Exception:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No credentials provided"
        )

    user = db.query(User).filter(User.user_name == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    # For production, set secure, samesite as needed
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path="/api/v1/auth",
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token, summary="Refresh Token", description="Get new access token using refresh token")
async def refresh(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    # Read refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=(settings.JWT_AUDIENCE if settings.JWT_AUDIENCE else None),
            issuer=settings.JWT_ISSUER,
        )
        if payload.get("typ") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.user_name == username).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    access_token = create_access_token(subject=user.user_name)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut, summary="User Registration", description="Register new user account")
async def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """Register new user."""
    # Check if user exists
    user = db.query(User).filter(User.user_name == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Get the default user role
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user role not found"
        )

    # Create new user with default role
    user = User(
        user_name=user_in.username,
        password_hash=get_password_hash(user_in.password),
        role_id=user_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UserOut, summary="Get Current User", description="Get current authenticated user information")
async def read_current_user(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(check_permissions(["users:read"])),
) -> Any:
    """Get current user."""
    return current_user
