# Role Hierarchy System

## Overview

The Role Hierarchy System provides a flexible and powerful way to manage roles and permissions through parent-child relationships. This system allows roles to inherit permissions from their parent roles, creating a hierarchical structure that simplifies permission management and reduces redundancy.

## Key Features

### 🏗️ Hierarchical Structure
- **Parent-Child Relationships**: Roles can have parent roles, creating a tree-like hierarchy
- **Automatic Level Calculation**: System automatically calculates and maintains hierarchy levels
- **Circular Reference Prevention**: Built-in protection against invalid hierarchy configurations

### 🔐 Permission Inheritance
- **Automatic Inheritance**: Child roles automatically inherit all permissions from parent roles
- **Additive Permissions**: Child roles can have additional permissions beyond inherited ones
- **Efficient Permission Checking**: Fast permission validation using inherited permissions

### 🛡️ Security & Integrity
- **Hierarchy Validation**: Built-in integrity checking and validation
- **Audit Logging**: All hierarchy changes are logged for security tracking
- **Safe Operations**: Prevents operations that would break hierarchy integrity

## Database Schema

### Role Model Updates

```sql
-- New columns added to roles table
ALTER TABLE roles ADD COLUMN parent_id INTEGER REFERENCES roles(id) ON DELETE SET NULL;
ALTER TABLE roles ADD COLUMN level INTEGER NOT NULL DEFAULT 0;

-- Indexes for efficient hierarchy queries
CREATE INDEX idx_role_parent_level ON roles(parent_id, level);
CREATE INDEX idx_role_hierarchy ON roles(level, parent_id);
```

### Role Model Methods

```python
class Role(Base):
    # ... existing fields ...
    parent_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    level = Column(Integer, default=0, nullable=False)
    
    # Hierarchy relationships
    parent = relationship("Role", remote_side=[id], back_populates="children")
    children = relationship("Role", back_populates="parent")
    
    def get_all_permissions(self):
        """Get all permissions including inherited ones."""
        
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has permission (including inherited)."""
        
    def get_ancestors(self):
        """Get all parent roles up the hierarchy."""
        
    def get_descendants(self):
        """Get all child roles down the hierarchy."""
```

## API Endpoints

### Hierarchy Management

#### `GET /api/v1/hierarchy/tree`
Get the complete role hierarchy as a tree structure.

**Response:**
```json
[
  {
    "id": 1,
    "name": "admin",
    "description": "System administrator",
    "level": 0,
    "direct_permissions": ["users:write", "roles:write"],
    "all_permissions": ["users:write", "roles:write", "users:read", "roles:read"],
    "children": [
      {
        "id": 2,
        "name": "manager",
        "level": 1,
        "direct_permissions": ["users:read"],
        "all_permissions": ["users:read", "users:write", "roles:write", "roles:read"],
        "children": []
      }
    ]
  }
]
```

#### `GET /api/v1/hierarchy/{role_id}`
Get detailed role information with hierarchy context.

**Response:**
```json
{
  "id": 2,
  "name": "manager",
  "description": "Department manager",
  "level": 1,
  "parent_id": 1,
  "parent_name": "admin",
  "direct_permissions": [
    {"id": 3, "name": "users:read", "description": "Read user data"}
  ],
  "inherited_permissions": [
    {"id": 1, "name": "users:write", "description": "Write user data"},
    {"id": 2, "name": "roles:write", "description": "Write role data"}
  ],
  "all_permissions": [
    {"id": 1, "name": "users:write", "description": "Write user data"},
    {"id": 2, "name": "roles:write", "description": "Write role data"},
    {"id": 3, "name": "users:read", "description": "Read user data"}
  ],
  "hierarchy_path": [
    {"id": 1, "name": "admin", "level": 0},
    {"id": 2, "name": "manager", "level": 1}
  ],
  "children": []
}
```

#### `POST /api/v1/hierarchy`
Create a new role with optional parent.

**Request:**
```json
{
  "name": "supervisor",
  "description": "Team supervisor",
  "parent_id": 2
}
```

#### `PUT /api/v1/hierarchy/{role_id}/parent`
Change the parent of an existing role.

**Request:**
```json
{
  "parent_id": 1
}
```

### Permission Analysis

#### `GET /api/v1/hierarchy/permission/{permission_name}`
Find all roles that have a specific permission.

**Response:**
```json
[
  {
    "id": 1,
    "name": "admin",
    "level": 0,
    "has_direct": true,
    "has_inherited": false,
    "inherited_from": null
  },
  {
    "id": 2,
    "name": "manager",
    "level": 1,
    "has_direct": false,
    "has_inherited": true,
    "inherited_from": "admin"
  }
]
```

#### `GET /api/v1/hierarchy/user/{user_id}/permissions`
Get all effective permissions for a user.

**Response:**
```json
{
  "user_id": 123,
  "username": "john_doe",
  "role_id": 2,
  "role_name": "manager",
  "role_level": 1,
  "permissions": ["users:read", "users:write", "roles:write", "roles:read"],
  "permission_count": 4
}
```

### Validation & Maintenance

#### `GET /api/v1/hierarchy/validate`
Validate hierarchy integrity.

**Response:**
```json
{
  "is_valid": true,
  "issues": [],
  "total_roles": 5,
  "issues_count": 0
}
```

#### `POST /api/v1/hierarchy/fix-levels`
Fix incorrect hierarchy levels.

**Response:**
```json
{
  "message": "Fixed hierarchy levels for 2 roles",
  "fixed_count": 2
}
```

## Usage Examples

### Creating a Role Hierarchy

```python
# Create root role (admin)
admin_role = RoleService.create(db, "admin", "System administrator")

# Create child role (manager)
manager_role = RoleService.create(db, "manager", "Department manager", parent_id=admin_role.id)

# Create grandchild role (user)
user_role = RoleService.create(db, "user", "Regular user", parent_id=manager_role.id)
```

### Permission Inheritance Example

```python
# Admin role has: ["users:write", "roles:write"]
# Manager role has: ["users:read"] + inherited from admin
# User role has: ["profile:read"] + inherited from manager + admin

# Check permissions
user_role.has_permission("users:write")  # True (inherited from admin)
user_role.has_permission("users:read")   # True (inherited from manager)
user_role.has_permission("profile:read") # True (direct permission)

# Get all permissions
all_perms = user_role.get_all_permissions()
# Returns: users:write, roles:write, users:read, profile:read
```

### Hierarchy Navigation

```python
# Get ancestors (parent roles)
ancestors = user_role.get_ancestors()
# Returns: [manager_role, admin_role]

# Get descendants (child roles)
descendants = admin_role.get_descendants()
# Returns: [manager_role, user_role]

# Check relationships
admin_role.is_ancestor_of(user_role)  # True
user_role.is_descendant_of(admin_role)  # True
```

## Migration Guide

### Existing Database Migration

1. **Run Migration Script:**
   ```bash
   python app/scripts/migrate_role_hierarchy.py
   ```

2. **Create Sample Hierarchy (Optional):**
   ```bash
   python app/scripts/migrate_role_hierarchy.py --sample
   ```

3. **Validate Migration:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/hierarchy/validate" \
        -H "Authorization: Bearer YOUR_TOKEN"
   ```

### Code Updates Required

1. **Permission Checking**: The system automatically uses hierarchy-aware permission checking
2. **Role Creation**: Update role creation to optionally specify `parent_id`
3. **Permission Queries**: Use `role.get_all_permissions()` instead of `role.permissions`

## Best Practices

### Hierarchy Design

1. **Keep It Simple**: Avoid deep hierarchies (max 4-5 levels)
2. **Logical Structure**: Design hierarchy to match organizational structure
3. **Permission Granularity**: Assign broad permissions to parent roles, specific ones to children

### Security Considerations

1. **Regular Validation**: Periodically run hierarchy validation
2. **Audit Changes**: Monitor hierarchy changes through audit logs
3. **Test Permissions**: Verify permission inheritance works as expected

### Performance Optimization

1. **Use Levels**: Leverage the `level` field for efficient queries
2. **Cache Permissions**: Consider caching effective permissions for frequently accessed roles
3. **Batch Operations**: Use batch operations for bulk hierarchy changes

## Troubleshooting

### Common Issues

1. **Circular References**: Use validation endpoint to detect and fix
2. **Incorrect Levels**: Run fix-levels endpoint to correct
3. **Missing Permissions**: Check inheritance chain and parent permissions

### Validation Commands

```bash
# Check hierarchy integrity
GET /api/v1/hierarchy/validate

# Fix level issues
POST /api/v1/hierarchy/fix-levels

# View complete hierarchy
GET /api/v1/hierarchy/tree
```

## Future Enhancements

- **Role Templates**: Predefined role hierarchies for common use cases
- **Permission Conflicts**: Detection and resolution of conflicting permissions
- **Dynamic Hierarchies**: Runtime hierarchy modifications based on conditions
- **Performance Caching**: Advanced caching for large hierarchies
