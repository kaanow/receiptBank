from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccountCreate(BaseModel):
    name: str
    friendly_name: str
    type: str  # rental, employment, personal
    metadata: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    friendly_name: Optional[str] = None
    type: Optional[str] = None
    metadata: Optional[str] = None


class AccountResponse(BaseModel):
    id: int
    owner_user_id: int
    name: str
    friendly_name: str
    type: str
    metadata: Optional[str] = Field(None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ShareRequest(BaseModel):
    email: EmailStr


class ExpenseCreate(BaseModel):
    account_id: int
    amount: float
    amount_subtotal: Optional[float] = None
    tax_gst: Optional[float] = None
    tax_pst: Optional[float] = None
    currency: str = "CAD"
    date: datetime
    vendor: str
    category: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    amount_subtotal: Optional[float] = None
    tax_gst: Optional[float] = None
    tax_pst: Optional[float] = None
    date: Optional[datetime] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    account_id: int
    amount: float
    amount_subtotal: Optional[float] = None
    tax_gst: Optional[float] = None
    tax_pst: Optional[float] = None
    currency: str
    date: datetime
    vendor: str
    category: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    created_by_user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class ReceiptResponse(BaseModel):
    id: int
    expense_id: int
    original_filename: str
    stored_path: str
    mime_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExtractResponse(BaseModel):
    date: Optional[datetime] = None
    amount: Optional[float] = None
    amount_subtotal: Optional[float] = None
    tax_gst: Optional[float] = None
    tax_pst: Optional[float] = None
    vendor: str = "Unknown"
