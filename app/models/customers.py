"""
Customer model with enhanced validation and business logic.
"""

from typing import List, Optional
from sqlalchemy import Column,Integer,String,DateTime,ForeignKey,Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer,primary_key=True,index=True)
    customer_id = Column(String(20),unique=True,nullable=False,index=True)
    type = Column(String(20),nullable=False,index=True)
    currency = Column(String(3),nullable=False,index=True)
    credit = Column(Numeric(15,2),nullable=False,index=True)
    amount = Column(Numeric(15, 2),nullable=False,index=True)
    bank_id = Column(Integer,ForeignKey("banks.bank_id",ondelete="CASCADE"),nullable=False)
    #bank_name = Column(String(255),nullable=False,index=True)
    note = Column(String(255),nullable=True)
    create_at = Column(DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    update_at = Column(DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()    
    )
    create_by_user = Column(Integer,ForeignKey("users.id", ondelete="CASCADE"),nullable=False)
    
    bank = relationship("Bank", back_populates="customers")
    created_by_user = relationship("User", back_populates="customers_created")
        
    
    