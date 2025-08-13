"""Role hierarchy management service."""
from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.role import Role
from app.models.permission import Permission
from app.services.audit_service import AuditService


class RoleHierarchyService:
    """Service for managing role hierarchy and permission inheritance."""
    
    @staticmethod
    def create_role_with_parent(
        db: Session,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[int] = None,
        admin_user_id: Optional[int] = None
    ) -> Role:
        """Create a new role with optional parent."""
        # Validate parent exists if provided
        parent_role = None
        if parent_id:
            parent_role = db.get(Role, parent_id)
            if not parent_role:
                raise ValueError(f"Parent role with ID {parent_id} not found")
        
        # Calculate level
        level = 0 if not parent_role else parent_role.level + 1
        
        # Create role
        role = Role(
            name=name,
            description=description,
            parent_id=parent_id,
            level=level
        )
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        # Log the creation
        AuditService.log_event(
            db=db,
            action="create_role",
            user_id=admin_user_id,
            resource="role",
            resource_id=str(role.id),
            details={
                "role_name": name,
                "parent_id": parent_id,
                "level": level
            },
            status="success"
        )
        
        return role
    
    @staticmethod
    def set_role_parent(
        db: Session,
        role_id: int,
        parent_id: Optional[int],
        admin_user_id: Optional[int] = None
    ) -> Role:
        """Set or change the parent of a role."""
        role = db.get(Role, role_id)
        if not role:
            raise ValueError(f"Role with ID {role_id} not found")
        
        # Validate parent if provided
        if parent_id:
            parent_role = db.get(Role, parent_id)
            if not parent_role:
                raise ValueError(f"Parent role with ID {parent_id} not found")
            
            # Prevent circular references
            if RoleHierarchyService._would_create_cycle(role, parent_role):
                raise ValueError("Setting this parent would create a circular reference")
            
            # Prevent setting a descendant as parent
            if role.is_ancestor_of(parent_role):
                raise ValueError("Cannot set a descendant role as parent")
        
        old_parent_id = role.parent_id
        role.parent_id = parent_id
        
        # Update levels for this role and all descendants
        RoleHierarchyService._update_hierarchy_levels(db, role)
        
        db.commit()
        
        # Log the change
        AuditService.log_event(
            db=db,
            action="update_role_hierarchy",
            user_id=admin_user_id,
            resource="role",
            resource_id=str(role_id),
            details={
                "role_name": role.name,
                "old_parent_id": old_parent_id,
                "new_parent_id": parent_id
            },
            status="success"
        )
        
        return role
    
    @staticmethod
    def _would_create_cycle(role: Role, potential_parent: Role) -> bool:
        """Check if setting potential_parent as parent would create a cycle."""
        current = potential_parent
        while current:
            if current.id == role.id:
                return True
            current = current.parent
        return False
    
    @staticmethod
    def _update_hierarchy_levels(db: Session, role: Role) -> None:
        """Update levels for a role and all its descendants."""
        role.update_level()
        
        # Recursively update children
        for child in role.children:
            RoleHierarchyService._update_hierarchy_levels(db, child)
    
    @staticmethod
    def get_role_hierarchy_tree(db: Session) -> List[Dict[str, Any]]:
        """Get the complete role hierarchy as a tree structure."""
        # Get all root roles (no parent)
        root_roles = db.query(Role).filter(Role.parent_id.is_(None)).all()
        
        def build_tree(role: Role) -> Dict[str, Any]:
            return {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "level": role.level,
                "direct_permissions": [p.name for p in role.permissions],
                "all_permissions": role.get_permission_names(),
                "children": [build_tree(child) for child in role.children]
            }
        
        return [build_tree(role) for role in root_roles]
    
    @staticmethod
    def get_role_with_inherited_permissions(db: Session, role_id: int) -> Optional[Dict[str, Any]]:
        """Get role details with all inherited permissions."""
        role = db.get(Role, role_id)
        if not role:
            return None
        
        all_permissions = role.get_all_permissions()
        direct_permissions = set(role.permissions)
        inherited_permissions = all_permissions - direct_permissions
        
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "level": role.level,
            "parent_id": role.parent_id,
            "parent_name": role.parent.name if role.parent else None,
            "direct_permissions": [
                {"id": p.id, "name": p.name, "description": p.description}
                for p in direct_permissions
            ],
            "inherited_permissions": [
                {"id": p.id, "name": p.name, "description": p.description}
                for p in inherited_permissions
            ],
            "all_permissions": [
                {"id": p.id, "name": p.name, "description": p.description}
                for p in all_permissions
            ],
            "hierarchy_path": [
                {"id": r.id, "name": r.name, "level": r.level}
                for r in role.get_hierarchy_path()
            ],
            "children": [
                {"id": child.id, "name": child.name, "level": child.level}
                for child in role.children
            ]
        }
    
    @staticmethod
    def get_effective_permissions_for_user(db: Session, user_id: int) -> Set[str]:
        """Get all effective permissions for a user including inherited ones."""
        from app.models.user import User
        
        user = db.get(User, user_id)
        if not user or not user.role:
            return set()
        
        return set(user.role.get_permission_names())
    
    @staticmethod
    def find_roles_with_permission(db: Session, permission_name: str) -> List[Dict[str, Any]]:
        """Find all roles that have a specific permission (direct or inherited)."""
        all_roles = db.query(Role).all()
        roles_with_permission = []
        
        for role in all_roles:
            if role.has_permission(permission_name):
                # Determine if permission is direct or inherited
                direct_permission_names = [p.name for p in role.permissions]
                is_direct = permission_name in direct_permission_names
                
                roles_with_permission.append({
                    "id": role.id,
                    "name": role.name,
                    "level": role.level,
                    "has_direct": is_direct,
                    "has_inherited": not is_direct,
                    "inherited_from": None if is_direct else RoleHierarchyService._find_permission_source(role, permission_name)
                })
        
        return roles_with_permission
    
    @staticmethod
    def _find_permission_source(role: Role, permission_name: str) -> Optional[str]:
        """Find which ancestor role provides a specific permission."""
        current = role.parent
        while current:
            direct_permissions = [p.name for p in current.permissions]
            if permission_name in direct_permissions:
                return current.name
            current = current.parent
        return None
    
    @staticmethod
    def validate_hierarchy_integrity(db: Session) -> List[Dict[str, Any]]:
        """Validate the integrity of the role hierarchy."""
        issues = []
        all_roles = db.query(Role).all()
        
        for role in all_roles:
            # Check for circular references
            visited = set()
            current = role
            while current:
                if current.id in visited:
                    issues.append({
                        "type": "circular_reference",
                        "role_id": role.id,
                        "role_name": role.name,
                        "description": "Role has circular reference in hierarchy"
                    })
                    break
                visited.add(current.id)
                current = current.parent
            
            # Check level consistency
            expected_level = 0
            if role.parent:
                expected_level = role.parent.level + 1
            
            if role.level != expected_level:
                issues.append({
                    "type": "incorrect_level",
                    "role_id": role.id,
                    "role_name": role.name,
                    "current_level": role.level,
                    "expected_level": expected_level,
                    "description": f"Role level {role.level} doesn't match expected {expected_level}"
                })
        
        return issues
    
    @staticmethod
    def fix_hierarchy_levels(db: Session) -> int:
        """Fix incorrect hierarchy levels."""
        fixed_count = 0
        root_roles = db.query(Role).filter(Role.parent_id.is_(None)).all()
        
        def fix_role_and_children(role: Role, expected_level: int):
            nonlocal fixed_count
            if role.level != expected_level:
                role.level = expected_level
                fixed_count += 1
            
            for child in role.children:
                fix_role_and_children(child, expected_level + 1)
        
        # Fix all root roles and their descendants
        for root_role in root_roles:
            fix_role_and_children(root_role, 0)
        
        db.commit()
        return fixed_count
