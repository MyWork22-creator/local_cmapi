from __future__ import annotations
import random
from typing import Iterable
from faker import Faker
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User

fake = Faker()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def ensure_roles(db: Session, names: Iterable[str]) -> list[Role]:
    out = []
    for name in names:
        r = db.query(Role).filter(Role.name == name).first()
        if not r:
            r = Role(name=name, description=f"Role {name}")
            db.add(r)
        out.append(r)
    db.commit()
    return out

def ensure_permissions(db: Session, names: Iterable[str]) -> list[Permission]:
    out = []
    for name in names:
        p = db.query(Permission).filter(Permission.name == name).first()
        if not p:
            p = Permission(name=name, description=f"Permission {name}")
            db.add(p)
        out.append(p)
    db.commit()
    return out

def attach_permissions_to_role(db: Session, role: Role, permissions: list[Permission]) -> Role:
    # idempotent: add only missing
    to_add = [p for p in permissions if p not in role.permissions]
    if to_add:
        role.permissions.extend(to_add)
        db.add(role)
        db.commit()
        db.refresh(role)
    return role

def create_user(db: Session, user_name: str, password: str, role: Role, status: str = "active") -> User:
    existing = db.query(User).filter(User.user_name == user_name).first()
    if existing:
        return existing
    u = User(
        user_name=user_name,
        password_hash=pwd.hash(password),
        role_id=role.id,
        status=status,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def fake_user(db: Session, roles: list[Role]) -> User:
    role = random.choice(roles)
    uname = fake.unique.user_name()[:50]
    return create_user(db, uname, "password123", role)
