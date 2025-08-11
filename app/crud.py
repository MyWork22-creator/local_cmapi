from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.orm import Session
from .models.models import Todo, User
from .core.security import get_password_hash, verify_password


# Users
def get_user_by_username(db: Session, *, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalars().first()


def create_user(db: Session, *, username: str, password: str) -> User:
    hashed = get_password_hash(password)
    user = User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def delete_user(db: Session, user_id: int) -> bool:
    user = db.get(User, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def update_user(
    db: Session,
    user_id: int,
    *,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Optional[User]:
    user = db.get(User, user_id)
    if not user:
        return None

    if username is not None:
        user.username = username
    if password is not None:
        hashed = get_password_hash(password)
        user.hashed_password = hashed

    db.commit()
    db.refresh(user)
    return user


def list_todos(
    db: Session,
    *,
    user_id: int,
    search: Optional[str] = None,
    completed: Optional[bool] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Todo], int]:
    query = select(Todo).where(Todo.user_id == user_id)
    
    if search:
        query = query.where(Todo.title.ilike(f"%{search}%"))
    if completed is not None:
        query = query.where(Todo.completed == completed)
    if due_before:
        query = query.where(Todo.due_date <= due_before)
    if due_after:
        query = query.where(Todo.due_date >= due_after)
    
    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()
    
    # Apply sorting and pagination
    sort_column = getattr(Todo, sort_by)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))
    query = query.offset(offset).limit(limit)
    
    items = db.execute(query).scalars().all()
    return items, total

def create_todo(
    db: Session, 
    *, 
    user_id: int,
    title: str, 
    description: Optional[str], 
    completed: bool, 
    priority: int, 
    due_date: Optional[date]
) -> Todo:
    todo = Todo(
        user_id=user_id,
        title=title,
        description=description,
        completed=completed,
        priority=priority,
        due_date=due_date,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def get_todo(db: Session, todo_id: int, user_id: int) -> Optional[Todo]:
    return db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == user_id).first()


def delete_todo(db: Session, todo_id: int, user_id: int) -> bool:
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == user_id).first()
    if not todo:
        return False
    db.delete(todo)
    db.commit()
    return True


def update_todo(
    db: Session,
    todo_id: int,
    *,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
    priority: Optional[int] = None,
    due_date: Optional[date] = None,
) -> Optional[Todo]:
    todo = db.get(Todo, todo_id)
    if not todo:
        return None

    if title is not None:
        todo.title = title
    if description is not None:
        todo.description = description
    if completed is not None:
        todo.completed = completed
    if priority is not None:
        todo.priority = priority
    if due_date is not None:
        todo.due_date = due_date

    db.commit()
    db.refresh(todo)
    return todo


def build_todo_query(
    *,
    search: Optional[str] = None,
    completed: Optional[bool] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
) -> Select:
    stmt = select(Todo)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(Todo.title.ilike(like))
    if completed is not None:
        stmt = stmt.where(Todo.completed == completed)
    if due_before is not None:
        stmt = stmt.where((Todo.due_date.is_not(None)) & (Todo.due_date <= due_before))
    if due_after is not None:
        stmt = stmt.where((Todo.due_date.is_not(None)) & (Todo.due_date >= due_after))
    return stmt


def apply_sort(stmt: Select, sort_by: str, order: str) -> Select:
    column = getattr(Todo, sort_by)
    sort_fn = asc if order == "asc" else desc
    return stmt.order_by(sort_fn(column))


def list_todos(
    db: Session,
    *,
    search: Optional[str] = None,
    completed: Optional[bool] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Todo], int]:
    stmt = build_todo_query(
        search=search,
        completed=completed,
        due_before=due_before,
        due_after=due_after,
    )
    stmt = apply_sort(stmt, sort_by, order)

    total = db.execute(stmt).unique().scalars().all()
    count = len(total)
    if offset:
        total = total[offset:]
    if limit:
        total = total[:limit]
    return total, count
