from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .core.config import settings
from .database import Base, engine
from .middleware import SecurityHeadersMiddleware, InputValidationMiddleware, RequestSizeMiddleware, SecurityHeadersValidationMiddleware
from .models import User, Role, Permission, TokenBlacklist  # noqa: F401 (ensure models are imported so tables are created)
from .api.v1.auth import router as auth_router
from .api.v1.users import router as users_router
from .api.v1.roles import router as roles_router
from .api.v1.permissions import router as permissions_router
from .api.v1.role_hierarchy import router as role_hierarchy_router
from .api.v1 import bank  as banks_router
from .api.v1 import customers as customer_router


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables (for demo; in prod use Alembic migrations)
    Base.metadata.create_all(bind=engine)

    yield
    # Shutdown: cleanup if needed
    pass

app = FastAPI(
    title="FastAPI RBAC System 🔐",
    version="1.0.0",
    description="A comprehensive FastAPI application with Role-Based Access Control (RBAC) authentication system",
    lifespan=lifespan
)

# IMPORTANT: Add CORS middleware FIRST so headers are present on all responses (including errors)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

# Add Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add Input Validation middleware
app.add_middleware(InputValidationMiddleware, enable_strict_validation=True)

# Add Request Size middleware
app.add_middleware(RequestSizeMiddleware, max_request_size=10 * 1024 * 1024)  # 10MB

# Add Security Headers Validation middleware
app.add_middleware(SecurityHeadersValidationMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

import os

os.makedirs("app/static/logos", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(roles_router, prefix="/api/v1", tags=["roles"])
app.include_router(permissions_router, prefix="/api/v1", tags=["permissions"])
app.include_router(role_hierarchy_router, prefix="/api/v1", tags=["role-hierarchy"])
app.include_router(banks_router.router, prefix="/api/v1", tags=["banks"])
app.include_router(customer_router.router, prefix="/api/v1", tags=["customers"])



@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}
