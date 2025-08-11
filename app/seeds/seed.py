from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.seeds.factories import (
    ensure_roles,
    ensure_permissions,
    attach_permissions_to_role,
    create_user,
)

def seed_data():
    db = SessionLocal()
    try:
        # Ensure roles and permissions (idempotent)
        admin_role, user_role = ensure_roles(db, ["admin", "user"])
        permissions = ensure_permissions(
            db,
            [
                "users:read",
                "users:write",
                "users:delete",
                "roles:read",
                "roles:write",
                "roles:delete",
            ],
        )

        # Assign permissions to roles (idempotent)
        attach_permissions_to_role(db, admin_role, permissions)
        # Basic read permission for user
        read_perm = [p for p in permissions if p.name == "users:read"]
        if read_perm:
            attach_permissions_to_role(db, user_role, read_perm)

        # Ensure default users exist (idempotent)
        create_user(db, "admin", "password123", admin_role)
        create_user(db, "user", "password123", user_role)

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
