from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .core.config import settings
from .core.security_checks import validate_production_security, print_security_recommendations
from .database import Base, engine
from .middleware import SecurityHeadersMiddleware, InputValidationMiddleware, RequestSizeMiddleware, SecurityHeadersValidationMiddleware
from .models import User, Role, Permission, TokenBlacklist, AuditLog  # noqa: F401 (ensure models are imported so tables are created)
from .api.v1.auth import router as auth_router
from .api.v1.users import router as users_router
from .api.v1.roles import router as roles_router
from .api.v1.role_hierarchy import router as role_hierarchy_router
from .api.v1.audit import router as audit_router


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables (for demo; in prod use Alembic migrations)
    Base.metadata.create_all(bind=engine)

    # Run security validation checks
    validate_production_security()
    print_security_recommendations()

    yield
    # Shutdown: cleanup if needed
    pass

app = FastAPI(
    title="FastAPI RBAC System 🔐",
    version="1.0.0",
    description="A comprehensive FastAPI application with Role-Based Access Control (RBAC) authentication system",
    lifespan=lifespan
)

# Add Security Headers middleware (first)
app.add_middleware(SecurityHeadersMiddleware)

# Add Input Validation middleware
app.add_middleware(InputValidationMiddleware, enable_strict_validation=True)

# Add Request Size middleware
app.add_middleware(RequestSizeMiddleware, max_request_size=10 * 1024 * 1024)  # 10MB

# Add Security Headers Validation middleware
app.add_middleware(SecurityHeadersValidationMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(roles_router, prefix="/api/v1", tags=["roles"])
app.include_router(role_hierarchy_router, prefix="/api/v1", tags=["role-hierarchy"])
app.include_router(audit_router, prefix="/api/v1", tags=["audit"])



@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}
