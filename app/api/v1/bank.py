from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
import os
from pathlib import Path
import shutil
import uuid

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

@router.post("/banks", response_model=SuccessResponse[BankResponse])
def create_bank(
    
    bank_name: str = Form(...),
    description: str = Form(None),
    # Use File for the uploaded file
    logo: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:create"]))
):
    """Creates a new bank with an optional logo upload."""
    
    existing_bank = db.query(Bank).filter(Bank.bank_name == bank_name).first()
    if existing_bank:
        raise HTTPException(status_code=409, detail="Bank with this name already exists.")

    logo_url = None
    if logo:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/svg+xml","image/webp"]
        if logo.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        # Generate a unique, safe filename using UUID
        file_extension = logo.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        upload_path = f"app/static/logos/{unique_filename}"

        # Save the file to the local filesystem
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
            
        logo_url = f"/static/logos/{unique_filename}"

    new_bank = Bank(
        bank_name=bank_name,
        description=description,
        logo=logo_url,
        created_by_user_id=current_user.id
    )
    
    db.add(new_bank)
    db.commit()
    db.refresh(new_bank)
    
    return SuccessResponse(
        message="Bank created successfully",
        data=BankResponse.model_validate(new_bank)
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
    message = f"Found {len(items)} banks out of {total_count} total."
    return ListResponse[BankResponse](message=message,items=items, total=total_count, limit=limit, offset=offset)

@router.put("/banks/{bank_id}", response_model=SuccessResponse[BankResponse])
def update_bank(
    bank_id: int,
    payload: BankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:update"]))
):
    
    bank = db.query(Bank).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    update_data = payload.model_dump(exclude_unset=True)

    
    if 'bank_name' in update_data:
        existing_bank = db.query(Bank).filter(
            and_(
                Bank.bank_name == update_data['bank_name'],
                Bank.bank_id != bank_id  
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

@router.put("/banks/{bank_id}/logo", response_model=SuccessResponse[BankResponse])
def upload_bank_logo(
    bank_id: int,
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:update"]))
):
    """Uploads and updates the logo for an existing bank."""
    
    bank = db.query(Bank).filter(Bank.bank_id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found.")

    # Step 1: Delete the old logo if it exists
    if bank.logo:
        old_logo_path = Path("app") / bank.logo.lstrip('/')
        if old_logo_path.exists() and old_logo_path.is_file():
            try:
                os.remove(old_logo_path)
                print(f"Successfully deleted old logo file: {old_logo_path}")
            except OSError as e:
                print(f"Error deleting old logo file {old_logo_path}: {e}")

    # Step 2: Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/svg+xml","image/webp"]
    if logo.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    # Step 3: Generate and save the new filename
    file_extension = logo.filename.split(".")[-1]
    filename = f"bank_{bank.bank_id}.{file_extension}"
    upload_path = f"app/static/logos/{filename}"
    
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(logo.file, buffer)
        
    # Step 4: Update the database with the new logo URL
    logo_url = f"/static/logos/{filename}"
    bank.logo = logo_url
    
    db.commit()
    db.refresh(bank)
    
    return SuccessResponse(
        message=f"Bank logo for ID {bank_id} updated successfully",
        data=BankResponse.model_validate(bank)
    )
STATIC_DIR = Path(__file__).parent.parent / "static"

@router.delete("/banks/{bank_id}", response_model=BankDeletionResponse, responses={
    404: {"model": ErrorResponse, "description": "Bank not found"},
    409: {"model": ErrorResponse, "description": "Conflict: Bank cannot be deleted as it has associated customers."}
})
def delete_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["banks:delete"]))
):
   
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

    
    if bank.logo:
       
        logo_path = Path("app") / bank.logo.lstrip('/')
        
        
        if logo_path.exists() and logo_path.is_file():
            try:
                os.remove(logo_path)
                print(f"Successfully deleted logo file: {logo_path}")
            except OSError as e:
                print(f"Error deleting logo file {logo_path}: {e}")

    
    response_data = {
        "bank_id": bank.bank_id,
        "bank_name": bank.bank_name,
        "created_by_user_id": bank.created_by_user_id
    }

    # Proceed with database deletion
    db.delete(bank)
    db.commit()

    return BankDeletionResponse(**response_data)