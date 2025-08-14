"""
API endpoints for managing customer data.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, DBAPIError

from app.database import get_db
from app.models.customers import Customer
from app.models.user import User
from app.models.banks import Bank
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse,CustomerDeletionResponse
from app.schemas.common import ErrorResponse, ListResponse,SuccessResponse
from app.core.dependencies import get_current_user, require_permissions

# Define a shared responses dictionary for common HTTP errors
common_responses = {
    401: {"model": ErrorResponse, "description": "Unauthorized: Not authenticated"},
    403: {"model": ErrorResponse, "description": "Forbidden: Insufficient permissions"},
    404: {"model": ErrorResponse, "description": "Resource not found"}
}

# Create the APIRouter and apply the common responses
router = APIRouter(prefix="/customers", tags=["customers"], responses=common_responses)

@router.post("/", response_model=SuccessResponse[CustomerResponse], status_code=status.HTTP_201_CREATED, responses={
    409: {"model": ErrorResponse, "description": "Conflict: Customer ID already exists"}
})
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["customers:write"]))
):
    # 1. Check for a duplicate customer_id before starting the insert
    existing = db.query(Customer).filter(Customer.customer_id == payload.customer_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with ID '{payload.customer_id}' already exists."
        )

    # 2. Check if the bank exists. Use `payload.bank_id` directly here.
    bank = db.query(Bank).filter(Bank.bank_id == payload.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail=f"Bank with id {payload.bank_id} not found")
    
    # 3. If no duplicate is found and bank exists, proceed with the insert
    # Now you can create the dictionary if you need it later.
    customer_data = payload.model_dump()
    new_customer = Customer(
        **customer_data,
        create_by_user=current_user.id,
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return {
        "message": "Customer created successfully",
        "data": new_customer
    }


@router.get("/", response_model=ListResponse[CustomerResponse])
def list_customers(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["customers:read"]))
):
    """
    Retrieve a paginated list of all customers.

    Includes pagination details and eager-loads the associated user.
    """
    total_count = db.query(Customer).count()
    
    items = (
        db.query(Customer)
        .options(joinedload(Customer.created_by_user))
        .order_by(Customer.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return ListResponse[CustomerResponse](items=items, total=total_count, limit=limit, offset=offset)


@router.get("/{id}", response_model=SuccessResponse[CustomerResponse], responses={
    404: {"model": ErrorResponse, "description": "Not Found: Customer not found"}
})
def get_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["customers:read"]))
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

@router.put("/{id}", response_model=SuccessResponse[CustomerResponse], responses={
    404: {"model": ErrorResponse, "description": "Not Found: Customer not found"}
})
def update_customer(
    id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["customers:update"]))
):
    """
    Update an existing customer's information.
    """
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(customer, key, value)

    try:
        db.commit()
        db.refresh(customer)
        
        # Convert the SQLAlchemy object to the Pydantic model before returning
        return SuccessResponse(
            message=f"Customer with ID {id} updated successfully",
            data=CustomerResponse.model_validate(customer)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bank with id {payload.bank_id} not found"
        )
@router.delete("/{id}", response_model=CustomerDeletionResponse, responses={
    404: {"model": ErrorResponse, "description": "Not Found: Customer not found"}
})
def delete_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["customers:delete"]))
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