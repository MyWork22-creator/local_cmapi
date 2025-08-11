# Import Base from database so Alembic and SQLAlchemy can access metadata
from app.database import Base

# Import models so they register with Base.metadata
from . import associations  # role_permissions association table
from .user import User
from .role import Role
from .permission import Permission

__all__ = ["Base", "User", "Role", "Permission","associations"]
