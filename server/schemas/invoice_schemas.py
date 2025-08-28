from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from .property_schemas import PropertyReference


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIAL = "partial"


class RentalAgreementStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class PropertyReference(BaseModel):
    property_id: str
    property_name: Optional[str] = None  # For display purposes


class RentalAgreementBase(BaseModel):
    property_id: str  # Reference to Property
    tenant_email: EmailStr
    rent_payer_emails: List[EmailStr]
    monthly_rent: Decimal
    security_deposit: Decimal
    lease_start_date: date
    lease_end_date: date
    rent_due_date: int  # Day of month (1-31)
    late_fee: Optional[Decimal] = None
    grace_period_days: Optional[int] = 0
    utilities_included: Optional[List[str]] = []
    terms_and_conditions: Optional[str] = None
    additional_fees: Optional[Dict[str, Decimal]] = {}
    status: RentalAgreementStatus = RentalAgreementStatus.DRAFT
    created_by: EmailStr  # Tenant who creates the agreement


class RentalAgreementCreate(RentalAgreementBase):
    pass


class RentalAgreementResponse(RentalAgreementBase):
    id: str
    property: Optional[PropertyReference] = None  # Populated property details
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None


class RentalAgreementUpdate(BaseModel):
    monthly_rent: Optional[Decimal] = None
    security_deposit: Optional[Decimal] = None
    lease_end_date: Optional[date] = None
    rent_due_date: Optional[int] = None
    late_fee: Optional[Decimal] = None
    grace_period_days: Optional[int] = None
    utilities_included: Optional[List[str]] = None
    terms_and_conditions: Optional[str] = None
    additional_fees: Optional[Dict[str, Decimal]] = None
    status: Optional[RentalAgreementStatus] = None


class RentPaymentBase(BaseModel):
    rental_agreement_id: str
    rent_payer_email: EmailStr
    amount: Decimal
    due_date: date
    payment_type: str = "monthly_rent"  # monthly_rent, late_fee, security_deposit, etc.
    description: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING


class RentPaymentCreate(RentPaymentBase):
    pass


class RentPaymentResponse(RentPaymentBase):
    id: str
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    receipt_url: Optional[str] = None


class RentPaymentUpdateRequest(BaseModel):
    status: Optional[PaymentStatus] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None


class BulkRentPaymentCreate(BaseModel):
    rental_agreement_id: str
    rent_payer_emails: List[EmailStr]
    amount_per_payer: Decimal
    due_date: date
    description: Optional[str] = None


class DownloadAgreementRequest(BaseModel):
    agreement_id: str
    format: str = "pdf"  # pdf, docx


class PaymentReceiptRequest(BaseModel):
    payment_id: str
    format: str = "pdf"  # pdf, email