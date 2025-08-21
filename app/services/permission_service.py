from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.permission import Permission


class PermissionService:
    """Service layer for permission operations."""
    
    @staticmethod
    def get_all(db: Session) -> List[Permission]:
        """Get all permissions."""
        return db.execute(select(Permission)).scalars().all()
