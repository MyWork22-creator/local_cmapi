from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.banks import Bank
from app.models.user import User
from app.schemas.bank import BankCreate, BankUpdate, BankResponse
from app.schemas.common import ErrorResponse, ListResponse, MessageResponse
from app.core.dependencies import get_current_user, require_permissions

router = APIRouter(prefix="/banks", tags=["banks"])


@router.post("/", response_model=BankResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
})
def create_bank(
    payload: BankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:create"]))
):
    # Simple uniqueness on bank_name (application-level)
    existing = db.query(Bank).filter(Bank.bank_name == payload.bank_name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bank name already exists")

    bank = Bank(
        bank_name=payload.bank_name,
        logo=payload.logo,
        description=payload.description,
        created_by_user_id=current_user.id
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


@router.get("/", response_model=ListResponse[BankResponse], responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
})
def list_banks(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:list"]))
):
    q = db.query(Bank).options(joinedload(Bank.created_by_user).joinedload(User.role))
    total = q.count()
    items = q.order_by(Bank.bank_id.desc()).limit(limit).offset(offset).all()
    return ListResponse[BankResponse](items=items, total=total, limit=limit, offset=offset)


@router.get("/{bank_id}", response_model=BankResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
def get_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:read"]))
):
    bank = db.query(Bank).options(joinedload(Bank.created_by_user).joinedload(User.role)).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")
    return bank


@router.put("/{bank_id}", response_model=BankResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
def update_bank(
    bank_id: int,
    payload: BankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:update"]))
):
    bank = db.query(Bank).options(joinedload(Bank.created_by_user).joinedload(User.role)).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    if payload.bank_name is not None:
        bank.bank_name = payload.bank_name
    if payload.logo is not None:
        bank.logo = payload.logo
    if payload.description is not None:
        bank.description = payload.description

    db.commit()
    db.refresh(bank)
    return bank


@router.delete("/{bank_id}", response_model=MessageResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
def delete_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:delete"]))
):
    bank = db.query(Bank).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    db.delete(bank)
    db.commit()
    return MessageResponse(message="Bank deleted successfully")

