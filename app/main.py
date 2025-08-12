from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from . import models, database
from .api.v1 import auth
from .api.v1 import users as users_router
from .api.v1 import roles as roles_router
from .api.v1 import bank  as banks_router
#from .api.v1 import rbac_test as rbac_test_router
from .core.config import settings

app = FastAPI(
    title="FastAPI RBAC Demo",
    description="""
    ## FastAPI Role-Based Access Control (RBAC) System
    
    This is a comprehensive demonstration of implementing RBAC in FastAPI with:
    
    * **JWT Authentication** - Secure token-based authentication
    * **Role-Based Access Control** - Fine-grained permission management
    * **User Management** - Complete CRUD operations with RBAC protection
    * **Role Management** - Dynamic role and permission assignment
    
    ## Getting Started
    
    1. **Seed the database**: `python -m app.seeds.seed`
    2. **Get authentication help**: Visit `/api/v1/auth/help`
    3. **Login**: Use POST `/api/v1/auth/login` with default credentials
    4. **Authorize**: Click the 'Authorize' button and enter your Bearer token
    
    ## Default Users
    
    * **Admin**: `admin` / `password123` (all permissions)
    * **User**: `user` / `password123` (limited permissions)
    
    ## API Documentation
    
    * **Auth**: Authentication and user management
    * **Users**: User CRUD operations with RBAC protection
    * **Roles**: Role and permission management
    * **RBAC Testing**: Comprehensive RBAC validation endpoints
    """,
    version="1.0.0",
    contact={
        "name": "FastAPI RBAC Demo",
        "url": "https://github.com/your-repo/fastapi-rbac-demo",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication operations. Login, register, and token management.",
            "externalDocs": {
                "description": "Authentication Help",
                "url": "/api/v1/auth/help",
            },
        },
        {
            "name": "users",
            "description": "User management operations. CRUD operations for users with RBAC protection.",
        },
        {
            "name": "roles",
            "description": "Role management operations. CRUD operations for roles and permissions.",
        },
        {
            "name": "rbac-testing",
            "description": "RBAC testing and validation endpoints for debugging and testing permissions.",
        }
    ]
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables at startup
@app.on_event("startup")
def startup():
    if settings.CREATE_ALL_ON_STARTUP:
        models.Base.metadata.create_all(bind=database.engine)

# Custom OpenAPI schema to include security schemes
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: Bearer <token>"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {
            "BearerAuth": []
        }
    ]
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/api/v1", tags=["users"])
app.include_router(roles_router.router, prefix="/api/v1", tags=["roles"])
app.include_router(banks_router.router, prefix="/api/v1", tags=["banks"])
#app.include_router(rbac_test_router.router, prefix="/api/v1", tags=["rbac-testing"])
