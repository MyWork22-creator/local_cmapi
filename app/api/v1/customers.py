"""
API endpoints for managing customer data.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy import and_

from app.database import get_db
from app.models.customers import Customer
from app.models.user import User
from app.models.banks import Bank
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse,CustomerDeletionResponse
from app.schemas.common import ErrorResponse, ListResponse,SuccessResponse
from app.api.deps import get_db, check_permissions, get_current_user

# Define a shared responses dictionary for common HTTP errors
common_responses = {
    401: {"model": ErrorResponse, "description": "Unauthorized: Not authenticated"},
    403: {"model": ErrorResponse, "description": "Forbidden: Insufficient permissions"},
    404: {"model": ErrorResponse, "description": "Resource not found"}
}

# Create the APIRouter and apply the common responses
router = APIRouter( tags=["customers"], responses=common_responses)

@router.post("/customers", response_model=SuccessResponse[CustomerResponse], status_code=status.HTTP_201_CREATED, responses={
    409: {"model": ErrorResponse, "description": "Conflict: Customer ID already exists"}
})
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["customers:create"]))
):
    # Check if the bank exists
    bank = db.query(Bank).filter(Bank.bank_id == payload.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail=f"Bank with id {payload.bank_id} not found")
    
    # Check if the customer_id already exists
    existing_customer = db.query(Customer).filter(Customer.customer_id == payload.customer_id).first()
    if existing_customer:
        raise HTTPException(status_code=409, detail=f"Customer with id {payload.customer_id} already exists")

    # Create the new customer instance with the provided ID
    new_customer = Customer(
        **payload.model_dump(),
        create_by_user=current_user.id,
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return {
        "message": "Customer created successfully",
        "data": new_customer
    }


@router.get("/customers", response_model=ListResponse[CustomerResponse])
def list_customers(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["customers:read"]))
):
    """
    Retrieve a paginated list of all customers.

    Includes pagination details and eager-loads the associated user.
    """
    total_count = db.query(Customer).count()
    
    items = (
        db.query(Customer)
        .options(joinedload(Customer.created_by_user),
                 joinedload(Customer.bank,innerjoin=False)
        )
        .order_by(Customer.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return ListResponse[CustomerResponse](items=items, total=total_count, limit=limit, offset=offset)


@router.get("/customers/{id}", response_model=SuccessResponse[CustomerResponse], responses={
    404: {"model": ErrorResponse, "description": "Not Found: Customer not found"}
})
def get_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["customers:read"]))
):
    """
    Get a single customer by their unique integer ID.
    """
    customer = (
        db.query(Customer)
        .options(joinedload(Customer.created_by_user))
        .filter(Customer.id == id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    return SuccessResponse(
        message="Customer retrieved successfully",
        data=customer
    )


@router.put("/customers/{id}", response_model=SuccessResponse[CustomerResponse], responses={
    404: {"model": ErrorResponse, "description": "Not Found: Customer not found"},
    409: {"model": ErrorResponse, "description": "Conflict: New customer ID already exists"}
})
def update_customer(
    id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["customers:update"]))
):
    """
    Update an existing customer's information.
    """
    # 1. Primary check: Find the customer to update using the ID from the URL.
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    update_data = payload.model_dump(exclude_unset=True)

    # 2. Secondary check: Validate the new customer_id in the payload.
    if 'customer_id' in update_data:
        existing_customer = db.query(Customer).filter(
            and_(
                Customer.customer_id == update_data['customer_id'],
                Customer.id != id
            )
        ).first()
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer ID {update_data['customer_id']} already exists."
            )

    # 3. Apply the updates.
    for key, value in update_data.items():
        setattr(customer, key, value)

    try:
        db.commit()
        db.refresh(customer)
        
        return SuccessResponse(
            message=f"Customer with ID {id} updated successfully",
            data=CustomerResponse.model_validate(customer)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A conflict occurred, likely due to a non-existent bank ID."
        )


@router.delete("/customers/{id}", response_model=CustomerDeletionResponse, responses={
    404: {"model": ErrorResponse, "description": "Not Found: Customer not found"}
})
def delete_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions(["customers:delete"]))
):
    """
    Delete a customer entry by ID and return a detailed deletion response.
    """
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # Store the details before deleting the object
    response_data = {
        "customer_id": customer.customer_id,
        "bank_id": customer.bank_id,
        "created_by_user_id": customer.created_by_user.id
    }
    
    db.delete(customer)
    db.commit()
    
    return CustomerDeletionResponse(
        message="Customer deleted successfully",
        **response_data
    )
