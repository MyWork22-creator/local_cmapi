# FastAPI RBAC System 🔐

A comprehensive FastAPI application demonstrating Role-Based Access Control (RBAC) with authentication, authorization, and modern Python practices.

## ✨ Features

- **🔐 Complete RBAC System**: Users, Roles, Permissions with many-to-many relationships
- **🔑 JWT Authentication**: Access & refresh tokens with secure cookie handling
- **⚡ Rate Limiting**: Built-in request rate limiting with SlowAPI
- **🗄️ Flexible Database**: Support for both SQLite (development) and MySQL (production)
- **📚 Auto-Generated Docs**: Interactive API documentation with Swagger UI
- **🔄 Database Migrations**: Alembic integration for schema management

## 🏗️ Project Structure

```
fastapi-learn/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── users.py         # User management
│   │   │   └── roles.py         # Role management
│   ├── core/
│   │   ├── config.py            # Application configuration
│   │   └── security.py          # Security utilities
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   └── main.py                  # FastAPI application
├── alembic/                     # Database migrations
└── requirements.txt             # Python dependencies
```

## 🚀 Quick Start

```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
# Windows:
env\Scripts\activate
# Unix/Linux/macOS:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

## 🔧 Configuration

### Database Configuration

The application supports both SQLite and MySQL. Configure via `.env` file:

**For SQLite (Development):**

```env
DB_TYPE=sqlite
DB_NAME=rbac.db
```

**For MySQL (Production):**

```env
DB_TYPE=mysql
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database
```

### Environment Variables

Create a `.env` file with:

```env
# Application
APP_NAME=FastAPI RBAC System
ENV=dev

# Database (see above for options)
DB_TYPE=sqlite
DB_NAME=rbac.db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

## 📚 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📡 API Endpoints

### Authentication (`/api/v1/auth`)

- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `POST /register` - User registration
- `GET /me` - Get current user info

### User Management (`/api/v1/users`)

- `GET /users` - List all users
- `GET /users/{user_id}` - Get specific user
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Role Management (`/api/v1/roles`)

- `GET /roles` - List all roles
- `POST /roles` - Create new role
- `PUT /roles/{role_id}` - Update role
- `DELETE /roles/{role_id}` - Delete role

## 🔐 RBAC System

### Default Permissions

- `users:read`, `users:write`, `users:delete`
- `roles:read`, `roles:write`, `roles:delete`

### Permission Checking Examples

```python
# Single permission
@router.get("/protected")
async def protected_endpoint(
    _: bool = Depends(check_permissions(["users:read"]))
):
    return {"message": "Access granted"}

# Multiple permissions (AND logic)
@router.post("/admin-only")
async def admin_endpoint(
    _: bool = Depends(check_permissions(["users:write", "roles:write"]))
):
    return {"message": "Admin access"}

# Any permission (OR logic)
@router.get("/moderator")
async def moderator_endpoint(
    _: bool = Depends(check_any_permission(["users:write", "roles:read"]))
):
    return {"message": "Moderator access"}
```

## 🛠️ Development

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Adding New Permissions

1. Add to database via migration
2. Use in endpoints with `check_permissions()`
3. Assign to appropriate roles

## 📚 Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [JWT Documentation](https://jwt.io/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for educational purposes. Feel free to use and modify as needed.
