from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.permission import Permission
from app.models.associations import role_permissions


class RoleService:
    """Service layer for role operations."""
    
    @staticmethod
    def get_by_id(db: Session, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        return db.get(Role, role_id)
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Role]:
        """Get role by name."""
        stmt = select(Role).where(Role.name == name)
        return db.execute(stmt).scalars().first()
    
    @staticmethod
    def get_all(db: Session) -> List[Role]:
        """Get all roles."""
        return db.execute(select(Role)).scalars().all()
    
    @staticmethod
    def create(db: Session, name: str, description: Optional[str] = None, parent_id: Optional[int] = None) -> Role:
        """Create a new role with optional parent."""
        # Use hierarchy service for creation with parent
        if parent_id:
            from app.services.role_hierarchy_service import RoleHierarchyService
            return RoleHierarchyService.create_role_with_parent(
                db=db, name=name, description=description, parent_id=parent_id
            )

        # Create root role (no parent)
        role = Role(name=name, description=description, level=0)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def get_role_with_hierarchy(db: Session, role_id: int) -> Optional[dict]:
        """Get role with hierarchy information and inherited permissions."""
        from app.services.role_hierarchy_service import RoleHierarchyService
        return RoleHierarchyService.get_role_with_inherited_permissions(db, role_id)

    @staticmethod
    def get_hierarchy_tree(db: Session) -> List[dict]:
        """Get the complete role hierarchy tree."""
        from app.services.role_hierarchy_service import RoleHierarchyService
        return RoleHierarchyService.get_role_hierarchy_tree(db)

    @staticmethod
    def set_parent_role(db: Session, role_id: int, parent_id: Optional[int]) -> Role:
        """Set or change the parent of a role."""
        from app.services.role_hierarchy_service import RoleHierarchyService
        return RoleHierarchyService.set_role_parent(db, role_id, parent_id)
    
    @staticmethod
    def update(
        db: Session,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Role]:
        """Update role information."""
        role = db.get(Role, role_id)
        if not role:
            return None
        
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def delete(db: Session, role_id: int) -> bool:
        """Delete a role."""
        role = db.get(Role, role_id)
        if not role:
            return False
        
        db.delete(role)
        db.commit()
        return True
    
    @staticmethod
    def assign_permissions(db: Session, role_id: int, permission_ids: List[int]) -> bool:
        """Assign permissions to a role (replaces existing permissions)."""
        role = db.get(Role, role_id)
        if not role:
            return False
        
        # Verify all permission IDs exist
        permissions = db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        ).scalars().all()
        
        if len(permissions) != len(permission_ids):
            return False
        
        # Remove existing permissions
        db.execute(
            delete(role_permissions).where(role_permissions.c.role_id == role_id)
        )
        
        # Add new permissions
        for permission_id in permission_ids:
            db.execute(
                role_permissions.insert().values(
                    role_id=role_id, 
                    permission_id=permission_id
                )
            )
        
        db.commit()
        return True
    
    @staticmethod
    def get_permissions(db: Session, role_id: int) -> List[Permission]:
        """Get all permissions for a role."""
        role = db.get(Role, role_id)
        if not role:
            return []
        
        return role.permissions
    
    @staticmethod
    def remove_permission(db: Session, role_id: int, permission_id: int) -> bool:
        """Remove a specific permission from a role."""
        result = db.execute(
            delete(role_permissions).where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id
            )
        )
        db.commit()
        return result.rowcount > 0
