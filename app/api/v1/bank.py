from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.banks import Bank
from app.models.user import User
from app.schemas.bank import BankCreate, BankUpdate, BankResponse,BankDeletionResponse
from app.schemas.common import ErrorResponse, ListResponse
from app.core.dependencies import require_permissions, get_current_user

common_responses = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
}

router = APIRouter(prefix="/banks", tags=["banks"],responses=common_responses)

@router.post("/", response_model=BankResponse, responses={
    409: {"model": ErrorResponse}
})
def create_bank(
    payload: BankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:write"]))
):
    
    bank = Bank(
        **payload.model_dump(),
        created_by_user_id=current_user.id
    )
    
    try:
        db.add(bank)
        db.commit()
        db.refresh(bank)
        return bank
    except IntegrityError:
        db.rollback()  # Rollback in case of a failed commit
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bank with this name already exists."
        )

@router.get("/", response_model=ListResponse[BankResponse])
def list_banks(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:read"]))
):
    
    total_count = db.query(Bank).count()
    
    items = (
        db.query(Bank)
        .options(joinedload(Bank.created_by_user))
        .order_by(Bank.bank_id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return ListResponse[BankResponse](items=items, total=total_count, limit=limit, offset=offset)

@router.get("/{bank_id}", response_model=BankResponse)
def get_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:read"]))
):
    bank = db.query(Bank).options(joinedload(Bank.created_by_user).joinedload(User.role)).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")
    return bank


@router.put("/{bank_id}", response_model=BankResponse)
def update_bank(
    bank_id: int,
    payload: BankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:update"]))
):
    bank = db.query(Bank).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    
    update_data = payload.model_dump(exclude_unset=True)

    
    for key, value in update_data.items():
        setattr(bank, key, value)
    
    db.commit()
    db.refresh(bank)
    return bank


@router.delete("/{bank_id}", response_model=BankDeletionResponse)
def delete_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["banks:delete"]))
):
    bank = db.query(Bank).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    # Store the details before deleting the object
    response_data = {
        "bank_id": bank.bank_id,
        "bank_name": bank.bank_name,
        "created_by_user_id": bank.created_by_user_id
    }

    db.delete(bank)
    db.commit()

    return BankDeletionResponse(**response_data)

