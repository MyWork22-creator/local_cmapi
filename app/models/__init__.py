from app.database import Base

# Import all models so they register with Base.metadata
from . import associations  # role_permissions association table
from .user import User
from .role import Role
from .permission import Permission
from .token_blacklist import TokenBlacklist
from .banks import Bank  # Added this line
from .customers import Customer # Added this line

__all__ = ["Base", "User", "Role", "Permission", "TokenBlacklist", "associations", "Bank", "Customer"]
