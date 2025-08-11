from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import create_todo, delete_todo, get_todo, list_todos, update_todo
from ..db import get_db
from ..schemas.schemas import Order, SortBy, TodoCreate, TodoRead, TodoUpdate
from ..schemas.pagination import PaginatedResponse
from ..models.models import User
from ..core.security import get_current_user

router = APIRouter(prefix="/todos", tags=["todos"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo_endpoint(
    payload: TodoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        todo = create_todo(
            db,
            user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            completed=payload.completed,
            priority=payload.priority,
            due_date=payload.due_date,
        )
        return todo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create todo item"
        ) from e


@router.get("", response_model=PaginatedResponse[TodoRead])
def list_todos_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search in title (ILIKE)"),
    completed: Optional[bool] = Query(None, description="Filter by completion"),
    due_before: Optional[date] = Query(None),
    due_after: Optional[date] = Query(None),
    sort_by: SortBy = Query("created_at"),
    order: Order = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = list_todos(
        db,
        user_id=current_user.id,
        search=search,
        completed=completed,
        due_before=due_before,
        due_after=due_after,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{todo_id}", response_model=TodoRead)
def get_todo_endpoint(
    todo_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    todo = get_todo(db, todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.patch("/{todo_id}", response_model=TodoRead)
def update_todo_endpoint(
    todo_id: int, 
    payload: TodoUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    todo = update_todo(
        db,
        todo_id,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        completed=payload.completed,
        priority=payload.priority,
        due_date=payload.due_date,
    )
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo_endpoint(
    todo_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ok = delete_todo(db, todo_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return None
