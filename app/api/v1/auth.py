from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.security import verify_password, create_access_token, create_refresh_token, get_password_hash, oauth2_scheme
from app.core.config import settings
from app.core.password_policy import get_password_requirements, PasswordValidationError
from app.core.rate_limiting import check_auth_rate_limit, record_auth_attempt
from app.api.deps import get_db, get_current_user, check_permissions
from app.services import AuthService, UserService, RoleService
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserOut, UserLogin, PasswordChangeRequest

router = APIRouter()
security = HTTPBearer()

@router.get("/help", summary="Authentication Help", description="Get help on how to authenticate and use the API")
async def get_auth_help():
    """Get help on how to authenticate and use the API."""
    return {
        "message": "FastAPI RBAC Authentication Guide",
        "steps": [
            "1. Login using POST /api/v1/auth/login with your credentials",
            "2. Copy the access_token from the response",
            "3. Click the 'Authorize' button at the top of this page",
            "4. Enter your token in the format: Bearer <your_access_token>",
            "5. Click 'Authorize' to enable authenticated endpoints",
            "6. You can now access protected endpoints that require authentication"
        ],
        "user_creation": {
            "note": "Self-registration is disabled. Only admin users can create new accounts.",
            "admin_endpoint": "POST /api/v1/users (requires admin role)",
            "process": [
                "1. Login as admin user",
                "2. Use POST /api/v1/users to create new user accounts",
                "3. Provide username, password, and optionally role_id",
                "4. New users can then login with their credentials"
            ]
        },
        "default_users": {
            "admin": {
                "username": "admin",
                "password": "password123",
                "permissions": "All permissions",
                "can_create_users": True
            },
            "user": {
                "username": "user",
                "password": "password123",
                "permissions": "users:read only",
                "can_create_users": False
            }
        },
        "note": "Make sure to run 'python -m app.seeds.seed' first to create default users"
    }

@router.post(
    "/login",
    response_model=Token,
    summary="User Login",
    description="Authenticate user and get access token",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        400: {"description": "Invalid credentials"},
        401: {"description": "Authentication failed"}
    }
)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Any:
    """
    Login with username and password to get an access token.

    **Request Body:**
    - **username**: Your username
    - **password**: Your password

    **Returns:**
    - **access_token**: JWT token for authentication
    - **token_type**: Always "bearer"

    **Rate Limiting:**
    - 5 attempts per 15 minutes per IP address
    - 3 attempts per 15 minutes per username
    - Stricter limits help prevent brute force attacks

    **Example:**
    ```json
    {
        "username": "admin",
        "password": "password123"
    }
    ```
    """
    # Check rate limits before attempting authentication
    check_auth_rate_limit(
        request,
        "login",
        max_attempts=5,
        window_minutes=15,
        username=credentials.username
    )

    user = AuthService.authenticate_user(db, credentials.username, credentials.password)
    if not user:
        # Record failed attempt in rate limiter
        record_auth_attempt(request, "login", credentials.username, success=False)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != "active":
        # Record failed attempt for inactive user
        record_auth_attempt(request, "login", credentials.username, success=False)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )

    # Record successful login attempt in rate limiter
    record_auth_attempt(request, "login", credentials.username, success=True)

    tokens = AuthService.create_tokens(user)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Set secure refresh token cookie with configurable security settings
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        domain="localhost",
        path="/",
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh Token",
    description="Get a new access token using the refresh token from cookies",
    responses={
        200: {
            "description": "New access token generated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Invalid or missing refresh token"}
    }
)
async def refresh(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Refresh access token using the refresh token stored in HTTP-only cookies.

    **Requirements:**
    - Must have a valid refresh token in cookies (set during login)
    - User account must be active

    **Returns:**
    - New access token with extended expiration

    **Note:** This endpoint reads the refresh token from HTTP-only cookies for security.
    """
    # Read refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    tokens = AuthService.refresh_access_token(db, refresh_token)
    if not tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    return tokens



@router.post(
    "/logout",
    summary="User Logout",
    description="Logout user by blacklisting current token and clearing refresh token cookie",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Invalid or missing token"}
    }
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout user by blacklisting the current access token and clearing refresh token cookie.

    **Requirements:**
    - Must be authenticated with a valid access token

    **Actions:**
    - Blacklists the current access token
    - Blacklists the refresh token from cookies (if present)
    - Clears the refresh token cookie

    **Returns:**
    - Success message confirming logout
    """
    # Get the token from the Authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    token = auth_header.split(" ")[1]

    # Blacklist the current access token
    blacklist_success = AuthService.blacklist_token(db, token)

    # Try to blacklist refresh token from cookies
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        AuthService.blacklist_token(db, refresh_token)

    # Clear the refresh token cookie with same security settings
    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE
    )



    return {
        "message": "Successfully logged out",
        "token_blacklisted": blacklist_success
    }


@router.get(
    "/password-policy",
    summary="Get Password Policy",
    description="Get password requirements and policy information"
)
async def get_password_policy() -> Any:
    """
    Get password policy requirements.

    **Returns:**
    - Password policy requirements and rules
    - Helpful information for creating secure passwords

    **Note:** This endpoint is public to help users create compliant passwords.
    """
    return get_password_requirements()


@router.post(
    "/change-password",
    summary="Change Password",
    description="Change current user's password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Password validation failed"},
        401: {"description": "Current password incorrect"}
    }
)
async def change_password(
    password_request: PasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Change the current user's password.

    **Requirements:**
    - Must be authenticated
    - Must provide correct current password
    - New password must meet policy requirements

    **Rate Limiting:**
    - 3 attempts per 30 minutes per user
    - Prevents password brute force attacks

    **Request Body:**
    - **current_password**: Current password for verification
    - **new_password**: New password meeting policy requirements

    **Returns:**
    - Success message confirming password change
    """
    # Check rate limits for password changes
    check_auth_rate_limit(
        request,
        "password_change",
        max_attempts=3,
        window_minutes=30,
        username=current_user.user_name
    )

    try:
        success = UserService.change_password(
            db, current_user.id, password_request.current_password, password_request.new_password
        )
        if success:
            # Record successful password change in rate limiter
            record_auth_attempt(request, "password_change", current_user.user_name, success=True)



            return {"message": "Password changed successfully"}
        else:
            # Record failed attempt in rate limiter
            record_auth_attempt(request, "password_change", current_user.user_name, success=False)



            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
    except ValueError as e:
        # Record failed attempt for validation errors in rate limiter
        record_auth_attempt(request, "password_change", current_user.user_name, success=False)



        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserOut, summary="Get Current User", description="Get current authenticated user information")
async def read_current_user(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(check_permissions(["users:read"])),
) -> Any:
    """Get current user."""
    return current_user
