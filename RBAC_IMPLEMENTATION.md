# Role-Based Access Control (RBAC) Implementation

## Overview

This FastAPI project now implements a comprehensive Role-Based Access Control (RBAC) system that provides fine-grained permission management and secure endpoint access control.

## 🏗️ Architecture

### Core Components

1. **Users** - Authentication and basic user information
2. **Roles** - User roles that group permissions
3. **Permissions** - Granular access rights
4. **Role-Permissions Association** - Many-to-many relationship between roles and permissions

### Database Schema

```
users (id, user_name, password_hash, role_id, status, created_at, updated_at)
roles (id, name, description, created_at, updated_at)
permissions (id, name, description, created_at, updated_at)
role_permissions (role_id, permission_id) - Association table
```

## 🔐 Permission System

### Default Permissions

The system comes with these pre-configured permissions:

- **`users:read`** - View user information
- **`users:write`** - Create/update user information
- **`users:delete`** - Delete users
- **`roles:read`** - View role information
- **`roles:write`** - Create/update roles
- **`roles:delete`** - Delete roles

### Default Roles

- **`admin`** - Has all permissions
- **`user`** - Has only `users:read` permission

## 🚀 API Endpoints

### Authentication (`/api/v1/auth`)

| Endpoint | Method | Permission Required | Description |
|-----------|--------|-------------------|-------------|
| `/login` | POST | None | User login |
| `/refresh` | POST | None | Refresh access token |
| `/register` | POST | None | User registration |
| `/me` | GET | `users:read` | Get current user info |

### User Management (`/api/v1/users`)

| Endpoint | Method | Permission Required | Description |
|-----------|--------|-------------------|-------------|
| `/users` | GET | `users:read` | List all users |
| `/users/{user_id}` | GET | `users:read` | Get specific user |
| `/users/{user_id}` | PUT | `users:write` | Update user |
| `/users/{user_id}` | DELETE | `users:delete` | Delete user |
| `/users/{user_id}/status` | PATCH | `users:write` | Update user status |
| `/users/{user_id}/with-role` | GET | `users:read` | Get user with role info |

### Role Management (`/api/v1/roles`)

| Endpoint | Method | Permission Required | Description |
|-----------|--------|-------------------|-------------|
| `/roles` | GET | `roles:read` | List all roles |
| `/roles/{role_id}` | GET | `roles:read` | Get specific role |
| `/roles` | POST | `roles:write` | Create new role |
| `/roles/{role_id}` | PUT | `roles:write` | Update role |
| `/roles/{role_id}` | DELETE | `roles:delete` | Delete role |
| `/roles/{role_id}/permissions` | POST | `roles:write` | Assign permissions to role |
| `/roles/{role_id}/users` | GET | `roles:read` | Get users with specific role |
| `/permissions` | GET | `roles:read` | List all permissions |

### RBAC Testing (`/api/v1/rbac`)

| Endpoint | Method | Permission Required | Description |
|-----------|--------|-------------------|-------------|
| `/rbac/current-user-info` | GET | None | Get current user's RBAC info |
| `/rbac/test-permission-check` | GET | `users:read` | Test permission checking |
| `/rbac/test-any-permission` | GET | `users:write` OR `roles:write` | Test OR logic permissions |
| `/rbac/test-admin-role` | GET | Admin role | Test admin role requirement |
| `/rbac/test-user-role` | GET | User role | Test user role requirement |
| `/rbac/test-multiple-permissions` | GET | `users:read` AND `roles:read` | Test AND logic permissions |
| `/rbac/permission-hierarchy` | GET | `roles:read` | Get complete RBAC hierarchy |
| `/rbac/user-permissions/{user_id}` | GET | `users:read` AND `roles:read` | Get user's RBAC details |
| `/rbac/role-permissions/{role_id}` | GET | `roles:read` | Get role's permission details |
| `/rbac/validate-access` | GET | None | Validate user access to permissions |

## 🛠️ Usage Examples

### 1. Basic Permission Check

```python
from app.api.deps import check_permissions

@router.get("/protected-endpoint")
async def protected_endpoint(
    _: bool = Depends(check_permissions(["users:read"]))
):
    return {"message": "Access granted"}
```

### 2. Multiple Permission Check (AND logic)

```python
@router.post("/admin-only")
async def admin_only_endpoint(
    _: bool = Depends(check_permissions(["users:write", "roles:write"]))
):
    return {"message": "Admin access granted"}
```

### 3. Any Permission Check (OR logic)

```python
from app.api.deps import check_any_permission

@router.get("/moderator-access")
async def moderator_endpoint(
    _: bool = Depends(check_any_permission(["users:write", "roles:read"]))
):
    return {"message": "Moderator access granted"}
```

### 4. Role-Based Access

```python
from app.api.deps import require_role

@router.get("/admin-panel")
async def admin_panel(
    _: bool = Depends(require_role("admin"))
):
    return {"message": "Admin panel access granted"}
```

### 5. Get User RBAC Information

```python
from app.api.deps import get_user_permissions, get_user_role

@router.get("/my-permissions")
async def get_my_permissions(
    permissions: List[str] = Depends(get_user_permissions),
    role: str = Depends(get_user_role)
):
    return {
        "role": role,
        "permissions": permissions
    }
```

## 🔒 Security Features

### JWT Token Security
- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
- HTTP-only cookies for refresh tokens
- Token type validation (access vs refresh)

### Permission Validation
- Granular permission checking
- Role-based access control
- Support for AND/OR logic in permissions
- Comprehensive error messages

### Database Security
- Password hashing with bcrypt
- Foreign key constraints with CASCADE
- Proper indexing for performance
- Audit timestamps

## 🧪 Testing the RBAC System

### 1. Start the Application

```bash
uvicorn app.main:app --reload
```

### 2. Seed the Database

```bash
python -m app.seeds.seed
```

### 3. Test with Default Users

**Admin User:**
- Username: `admin`
- Password: `password123`
- Permissions: All permissions

**Regular User:**
- Username: `user`
- Password: `password123`
- Permissions: `users:read` only

### 4. Test Permission Scenarios

1. **Login as admin** → Get access token
2. **Test admin endpoints** → Should work with all permissions
3. **Login as user** → Get access token
4. **Test restricted endpoints** → Should fail with permission errors
5. **Test RBAC testing endpoints** → Verify permission logic

## 📊 Permission Matrix

| Permission | Admin Role | User Role |
|------------|------------|-----------|
| `users:read` | ✅ | ✅ |
| `users:write` | ✅ | ❌ |
| `users:delete` | ✅ | ❌ |
| `roles:read` | ✅ | ❌ |
| `roles:write` | ✅ | ❌ |
| `roles:delete` | ✅ | ❌ |

## 🔧 Customization

### Adding New Permissions

1. Add permission to database:
```sql
INSERT INTO permissions (name, description) VALUES ('products:read', 'View products');
```

2. Assign to roles:
```sql
INSERT INTO role_permissions (role_id, permission_id) VALUES (1, 7); -- admin role
```

3. Use in endpoints:
```python
@router.get("/products")
async def list_products(
    _: bool = Depends(check_permissions(["products:read"]))
):
    return {"products": []}
```

### Adding New Roles

1. Create role:
```sql
INSERT INTO roles (name, description) VALUES ('moderator', 'Content moderator');
```

2. Assign permissions:
```sql
INSERT INTO role_permissions (role_id, permission_id) VALUES (3, 1); -- users:read
INSERT INTO role_permissions (role_id, permission_id) VALUES (3, 2); -- users:write
```

## 🚨 Error Handling

The system provides clear error messages for different scenarios:

- **401 Unauthorized** - Invalid or missing authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **400 Bad Request** - Invalid input data

## 📈 Performance Considerations

- **Lazy Loading** - Role permissions loaded on demand
- **Database Indexes** - Optimized queries for user lookups
- **Caching** - JWT tokens reduce database queries
- **Efficient Joins** - Optimized role-permission relationships

## 🔮 Future Enhancements

1. **Permission Groups** - Group related permissions
2. **Dynamic Permissions** - Runtime permission assignment
3. **Audit Logging** - Track permission usage
4. **Permission Inheritance** - Hierarchical permission structure
5. **Time-based Permissions** - Temporary access grants

## 📝 Conclusion

This RBAC implementation provides a robust, scalable, and secure foundation for access control in your FastAPI application. It supports complex permission scenarios while maintaining simplicity and performance.

The system is production-ready and can be easily extended to meet specific business requirements.
