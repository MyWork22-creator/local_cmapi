from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from app.database import get_db
from app.models.banks import Bank
from app.models.user import User
from app.models.customers import Customer 
from app.schemas.bank import BankCreate, BankUpdate, BankResponse,BankDeletionResponse
from app.schemas.common import ErrorResponse, ListResponse,SuccessResponse
from app.api.deps import get_db, check_permissions, get_current_user

common_responses = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
}

router = APIRouter(tags=["banks"],responses=common_responses)

@router.post("/banks", response_model=SuccessResponse[BankResponse], responses={
    409: {"model": ErrorResponse}
})
def create_bank(
    payload: BankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:create"]))
):
    # Proactive check for a conflicting bank name
    existing_bank = db.query(Bank).filter(Bank.bank_name == payload.bank_name).first()
    if existing_bank:
        raise HTTPException(status_code=409, detail="Bank with this name already exists.")
        
    new_bank = Bank(
        **payload.model_dump(),
        created_by_user_id=current_user.id
    )
    
    db.add(new_bank)
    db.commit()
    db.refresh(new_bank)
    return SuccessResponse(
        message="Bank created successfully",
        data = BankResponse.model_validate(new_bank)
    )

@router.get("/banks", response_model=ListResponse[BankResponse])
def list_banks(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:read"]))
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

@router.put("/banks/{bank_id}", response_model=SuccessResponse[BankResponse])
def update_bank(
    bank_id: int,
    payload: BankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:update"]))
):
    # Step 1: Check if the bank to be updated exists
    bank = db.query(Bank).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Step 2: Check for a conflicting bank name
    if 'bank_name' in update_data:
        existing_bank = db.query(Bank).filter(
            and_(
                Bank.bank_name == update_data['bank_name'],
                Bank.bank_id != bank_id  # Ensures you're not checking the current bank
            )
        ).first()
        if existing_bank:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A bank with this name already exists."
            )

    # Step 3: Apply the updates
    for key, value in update_data.items():
        setattr(bank, key, value)
    
    db.commit()
    db.refresh(bank)
    return SuccessResponse(
        message=f"Bank with ID {bank_id} updated successfully",
        data = BankResponse.model_validate(bank)
    )

@router.delete("/banks/{bank_id}", response_model=BankDeletionResponse, responses={
    404: {"model": ErrorResponse, "description": "Bank not found"},
    409: {"model": ErrorResponse, "description": "Conflict: Bank cannot be deleted as it has associated customers."}
})
def delete_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:delete"]))
):
    # Check if the bank exists
    bank = db.query(Bank).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    # Check for any associated customers
    has_customers = db.query(Customer).filter(Customer.bank_id == bank.bank_id).first()
    if has_customers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bank cannot be deleted because it has associated customers."
        )

    # Store details before deletion
    response_data = {
        "bank_id": bank.bank_id,
        "bank_name": bank.bank_name,
        "created_by_user_id": bank.created_by_user_id
    }

    # If no customers exist, proceed with deletion
    db.delete(bank)
    db.commit()

    return BankDeletionResponse(**response_data)