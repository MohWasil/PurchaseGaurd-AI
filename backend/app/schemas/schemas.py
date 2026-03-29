"""
Pydantic Schemas - Request/Response Validation
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be 8+ characters")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str

# Purchase Schemas
class PurchaseCreate(BaseModel):
    merchant_name: str
    purchase_date: datetime
    total_amount: float
    currency: str = "USD"
    return_deadline: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

class PurchaseResponse(BaseModel):
    id: int
    user_id: int
    merchant_name: str
    purchase_date: datetime
    total_amount: float
    currency: str
    return_deadline: Optional[datetime]
    warranty_expiry: Optional[datetime]
    is_returned: bool
    is_claimed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Alert Schema
class AlertResponse(BaseModel):
    id: int
    alert_type: str
    message: str
    is_sent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True