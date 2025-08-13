from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from .associations import role_permissions



class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))

    # Hierarchy support
    parent_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)
    level = Column(Integer, default=0, nullable=False, index=True)  # Hierarchy level for efficient queries

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Self-referential relationships for hierarchy
    parent = relationship("Role", remote_side=[id], back_populates="children")
    children = relationship("Role", back_populates="parent", cascade="all, delete-orphan")

    # Existing relationships
    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )

    # Indexes for efficient hierarchy queries
    __table_args__ = (
        Index('idx_role_parent_level', 'parent_id', 'level'),
        Index('idx_role_hierarchy', 'level', 'parent_id'),
    )

    def get_all_permissions(self, visited_roles=None):
        """
        Get all permissions including inherited ones from parent roles.
        Uses visited_roles to prevent infinite loops in case of circular references.
        """
        if visited_roles is None:
            visited_roles = set()

        # Prevent infinite loops
        if self.id in visited_roles:
            return set()

        visited_roles.add(self.id)

        # Start with direct permissions
        all_permissions = set(self.permissions)

        # Add inherited permissions from parent
        if self.parent:
            parent_permissions = self.parent.get_all_permissions(visited_roles.copy())
            all_permissions.update(parent_permissions)

        return all_permissions

    def get_permission_names(self):
        """Get all permission names including inherited ones."""
        permissions = self.get_all_permissions()
        return [perm.name for perm in permissions]

    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission (including inherited)."""
        permission_names = self.get_permission_names()
        return permission_name in permission_names

    def get_ancestors(self):
        """Get all ancestor roles in the hierarchy."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all descendant roles in the hierarchy."""
        descendants = []

        def collect_descendants(role):
            for child in role.children:
                descendants.append(child)
                collect_descendants(child)

        collect_descendants(self)
        return descendants

    def is_ancestor_of(self, other_role) -> bool:
        """Check if this role is an ancestor of another role."""
        current = other_role.parent
        while current:
            if current.id == self.id:
                return True
            current = current.parent
        return False

    def is_descendant_of(self, other_role) -> bool:
        """Check if this role is a descendant of another role."""
        return other_role.is_ancestor_of(self)

    def get_hierarchy_path(self):
        """Get the full hierarchy path from root to this role."""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    def update_level(self):
        """Update the level based on hierarchy depth."""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', level={self.level}, parent_id={self.parent_id})>"
