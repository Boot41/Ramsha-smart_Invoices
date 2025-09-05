from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ContractType(str, Enum):
    SERVICE_AGREEMENT = "service_agreement"
    RENTAL_LEASE = "rental_lease"
    MAINTENANCE_CONTRACT = "maintenance_contract"
    SUPPLY_CONTRACT = "supply_contract"
    CONSULTING_AGREEMENT = "consulting_agreement"
    OTHER = "other"


class InvoiceFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BIANNUALLY = "biannually"
    ANNUALLY = "annually"
    ONE_TIME = "one_time"
    CUSTOM = "custom"


class LineItemCategory(str, Enum):
    RENT = "rent"
    DEPOSIT = "deposit"
    UTILITY = "utility"
    MAINTENANCE_FEE = "maintenance_fee"
    LATE_FEE = "late_fee"
    OTHER = "other"


class ContractParty(BaseModel):
    """Information about a party in the contract"""
    name: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    role: str  # client, service_provider, tenant, landlord, etc.


class LineItem(BaseModel):
    """Represents a single, specific financial charge or item from the contract."""
    item_description: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = "USD"
    category: LineItemCategory
    billing_cycle: Optional[InvoiceFrequency] = None
    due_days: Optional[int] = None # e.g., due on the 10th of the month


class ContractInvoiceData(BaseModel):
    """Structured invoice data extracted from contract"""
    
    # Contract Information
    contract_title: Optional[str] = None
    contract_type: Optional[ContractType] = None
    contract_number: Optional[str] = None
    
    # Parties
    client: Optional[ContractParty] = None
    service_provider: Optional[ContractParty] = None
    
    # Contract Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    effective_date: Optional[date] = None
    
    # Financial Line Items
    line_items: List[LineItem] = []
    
    # Invoice Schedule
    invoice_frequency: Optional[InvoiceFrequency] = None
    first_invoice_date: Optional[date] = None
    next_invoice_date: Optional[date] = None
    
    # Additional Terms
    special_terms: Optional[str] = None
    notes: Optional[str] = None
    
    # Metadata
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    extracted_at: Optional[datetime] = None


class ContractProcessRequest(BaseModel):
    """Request to process a contract file"""
    user_id: str
    contract_name: str


class ContractProcessResponse(BaseModel):
    """Response after processing a contract"""
    status: str
    message: str
    contract_name: str
    user_id: str
    total_chunks: int
    total_embeddings: int
    vector_ids: List[str]
    text_preview: str
    processing_timestamp: str


class InvoiceGenerationRequest(BaseModel):
    """Request to generate invoice data from processed contract"""
    user_id: str
    contract_name: str
    query: Optional[str] = "Extract invoice data and payment terms from this contract"
    specific_requirements: Optional[List[str]] = []


class InvoiceGenerationResponse(BaseModel):
    """Response containing generated invoice data"""
    status: str
    message: str
    contract_name: str
    user_id: str
    invoice_data: ContractInvoiceData
    raw_response: Optional[str] = None
    confidence_score: Optional[float] = None
    generated_at: str


class ContractQueryRequest(BaseModel):
    """General query request for contract information"""
    user_id: str
    contract_name: str
    query: str


class ContractQueryResponse(BaseModel):
    """Response to contract query"""
    status: str
    response: str
    contract_name: str
    user_id: str
    query: str
    generated_at: str
