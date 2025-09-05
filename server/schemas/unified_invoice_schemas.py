from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import uuid


class ContractType(str, Enum):
    SERVICE_AGREEMENT = "service_agreement"
    RENTAL_LEASE = "rental_lease"
    MAINTENANCE_CONTRACT = "maintenance_contract"
    SUPPLY_CONTRACT = "supply_contract"
    CONSULTING_AGREEMENT = "consulting_agreement"
    SUBSCRIPTION = "subscription"
    OTHER = "other"


class InvoiceFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BIANNUALLY = "biannually"
    ANNUALLY = "annually"
    WEEKLY = "weekly"
    DAILY = "daily"
    ONE_TIME = "one_time"
    CUSTOM = "custom"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    VALIDATED = "validated"
    CORRECTED = "corrected"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PartyRole(str, Enum):
    CLIENT = "client"
    SERVICE_PROVIDER = "service_provider"
    TENANT = "tenant"
    LANDLORD = "landlord"
    VENDOR = "vendor"
    CONTRACTOR = "contractor"


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    INR = "INR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"


class UnifiedParty(BaseModel):
    """Unified party information structure"""
    name: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    role: Optional[PartyRole] = None
    
    @validator('role', pre=True, always=True)
    def set_default_role(cls, v, values):
        """Set default role if not provided"""
        if v is None:
            # Default fallback - this should be overridden by context-specific methods
            return PartyRole.CLIENT
        return v
    
    class Config:
        use_enum_values = True


class UnifiedPaymentTerms(BaseModel):
    """Unified payment terms structure"""
    amount: Optional[Union[Decimal, float, str]] = None
    currency: CurrencyCode = CurrencyCode.USD
    frequency: Optional[InvoiceFrequency] = None
    due_days: Optional[int] = 30
    late_fee: Optional[Union[Decimal, float, str]] = None
    discount_terms: Optional[str] = None
    payment_method: Optional[str] = "bank_transfer"
    
    @validator('amount', 'late_fee', pre=True)
    def convert_to_decimal(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return Decimal(v)
            except:
                return None
        return Decimal(str(v))
    
    class Config:
        use_enum_values = True


class UnifiedServiceItem(BaseModel):
    """Unified service/item structure"""
    description: str
    quantity: Optional[float] = 1.0
    unit_price: Optional[Union[Decimal, float, str]] = None
    total_amount: Optional[Union[Decimal, float, str]] = None
    unit: Optional[str] = "service"
    
    @validator('unit_price', 'total_amount', pre=True)
    def convert_to_decimal(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return Decimal(v)
            except:
                return None
        return Decimal(str(v))


class UnifiedInvoiceTotals(BaseModel):
    """Unified invoice totals structure"""
    subtotal: Union[Decimal, float] = 0.0
    tax_amount: Union[Decimal, float] = 0.0
    discount_amount: Union[Decimal, float] = 0.0
    late_fee_amount: Union[Decimal, float] = 0.0
    total_amount: Union[Decimal, float] = 0.0
    
    @validator('*', pre=True)
    def convert_to_decimal(cls, v):
        if isinstance(v, str):
            try:
                return Decimal(v)
            except:
                return 0.0
        return v if v is not None else 0.0


class UnifiedInvoiceMetadata(BaseModel):
    """Unified metadata structure"""
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    validation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    human_input_applied: bool = False
    human_reviewed: bool = False
    generated_by: Optional[str] = "smart_invoice_scheduler"
    agent_version: str = "1.0.0"
    processing_time_seconds: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    extracted_at: Optional[datetime] = None


class UnifiedInvoiceData(BaseModel):
    """
    Unified Invoice Data Structure
    
    This is the single source of truth for invoice data across the entire system.
    All agents (validation, correction, database) will use this format.
    """
    
    # === HEADER INFORMATION ===
    invoice_id: Optional[str] = Field(default_factory=lambda: f"INV-{str(uuid.uuid4())[:8]}")
    invoice_number: Optional[str] = None
    invoice_date: Optional[Union[date, str]] = None
    due_date: Optional[Union[date, str]] = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    
    # === CONTRACT INFORMATION ===
    contract_title: Optional[str] = None
    contract_type: Optional[ContractType] = None
    contract_number: Optional[str] = None
    contract_reference: Optional[str] = None
    
    # === PARTIES ===
    client: Optional[UnifiedParty] = None
    service_provider: Optional[UnifiedParty] = None
    
    # === CONTRACT DATES ===
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None
    effective_date: Optional[Union[date, str]] = None
    
    # === PAYMENT INFORMATION ===
    payment_terms: Optional[UnifiedPaymentTerms] = None
    
    # === SERVICES AND ITEMS ===
    services: List[UnifiedServiceItem] = []
    
    # === INVOICE SCHEDULE ===
    invoice_frequency: Optional[InvoiceFrequency] = None
    first_invoice_date: Optional[Union[date, str]] = None
    next_invoice_date: Optional[Union[date, str]] = None
    
    # === ADDITIONAL TERMS ===
    special_terms: Optional[str] = None
    notes: Optional[str] = None
    late_fee_policy: Optional[str] = None
    
    # === FINANCIAL TOTALS ===
    totals: Optional[UnifiedInvoiceTotals] = None
    
    # === METADATA ===
    metadata: UnifiedInvoiceMetadata = Field(default_factory=UnifiedInvoiceMetadata)
    
    @validator('invoice_number', always=True)
    def set_invoice_number(cls, v, values):
        if v:
            return v
        invoice_id = values.get('invoice_id')
        if invoice_id:
            return f"INV-{invoice_id}"
        return f"INV-{str(uuid.uuid4())[:8]}"
    
    @validator('totals', always=True)
    def ensure_totals(cls, v, values):
        if v is None:
            # Calculate totals from payment_terms if available
            payment_terms = values.get('payment_terms')
            if payment_terms and payment_terms.amount:
                amount = float(payment_terms.amount)
                return UnifiedInvoiceTotals(
                    subtotal=amount,
                    total_amount=amount
                )
            return UnifiedInvoiceTotals()
        return v
    
    def to_legacy_contract_invoice_data(self) -> Dict[str, Any]:
        """Convert to legacy ContractInvoiceData format for backward compatibility"""
        return {
            "contract_title": self.contract_title,
            "contract_type": self.contract_type.value if self.contract_type else None,
            "contract_number": self.contract_number,
            "client": self.client.model_dump() if self.client else None,
            "service_provider": self.service_provider.model_dump() if self.service_provider else None,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "effective_date": self.effective_date,
            "payment_terms": self.payment_terms.model_dump() if self.payment_terms else None,
            "services": [service.model_dump() for service in self.services],
            "invoice_frequency": self.invoice_frequency.value if self.invoice_frequency else None,
            "first_invoice_date": self.first_invoice_date,
            "next_invoice_date": self.next_invoice_date,
            "special_terms": self.special_terms,
            "notes": self.notes,
            "confidence_score": self.metadata.confidence_score,
            "extracted_at": self.metadata.extracted_at or self.metadata.created_at
        }
    
    def to_correction_agent_format(self) -> Dict[str, Any]:
        """Convert to correction agent's expected format"""
        return {
            "invoice_header": {
                "invoice_id": self.invoice_id,
                "invoice_number": self.invoice_number,
                "invoice_date": str(self.invoice_date) if self.invoice_date else datetime.now().strftime('%Y-%m-%d'),
                "due_date": str(self.due_date) if self.due_date else None,
                "contract_reference": self.contract_reference or self.contract_title,
                "workflow_id": self.metadata.workflow_id,
                "generated_at": self.metadata.created_at.isoformat() if self.metadata.created_at else datetime.now().isoformat()
            },
            "parties": {
                "client": self.client.model_dump() if self.client else {},
                "service_provider": self.service_provider.model_dump() if self.service_provider else {}
            },
            "contract_details": {
                "contract_type": self.contract_type.value if self.contract_type else None,
                "start_date": str(self.start_date) if self.start_date else None,
                "end_date": str(self.end_date) if self.end_date else None,
                "effective_date": str(self.effective_date) if self.effective_date else None
            },
            "payment_information": self.payment_terms.model_dump() if self.payment_terms else {},
            "services_and_items": [service.model_dump() for service in self.services],
            "invoice_schedule": {
                "frequency": self.invoice_frequency.value if self.invoice_frequency else None,
                "first_invoice_date": str(self.first_invoice_date) if self.first_invoice_date else None,
                "next_invoice_date": str(self.next_invoice_date) if self.next_invoice_date else None
            },
            "additional_terms": {
                "special_terms": self.special_terms,
                "notes": self.notes,
                "late_fee_policy": self.late_fee_policy
            },
            "totals": self.totals.model_dump() if self.totals else {},
            "metadata": self.metadata.model_dump()
        }
    
    def to_database_format(self) -> Dict[str, Any]:
        """Convert to format expected by database service"""
        return {
            "invoice_header": {
                "invoice_number": self.invoice_number,
                "invoice_id": self.invoice_id,
                "invoice_date": str(self.invoice_date) if self.invoice_date else datetime.now().strftime('%Y-%m-%d'),
                "due_date": str(self.due_date) if self.due_date else None,
                "contract_reference": self.contract_reference or self.contract_title,
                "workflow_id": self.metadata.workflow_id
            },
            "parties": {
                "client": self.client.model_dump() if self.client else {},
                "service_provider": self.service_provider.model_dump() if self.service_provider else {}
            },
            "payment_information": self.payment_terms.model_dump() if self.payment_terms else {},
            "totals": self.totals.model_dump() if self.totals else {},
            "contract_details": {
                "contract_type": self.contract_type.value if self.contract_type else None,
                "contract_title": self.contract_title
            },
            "metadata": self.metadata.model_dump(),
            "processing_metadata": {
                "user_id": self.metadata.user_id,
                "confidence_score": self.metadata.confidence_score,
                "quality_score": self.metadata.quality_score,
                "human_input_applied": self.metadata.human_input_applied
            }
        }
    
    @classmethod
    def from_legacy_format(cls, data: Dict[str, Any]) -> "UnifiedInvoiceData":
        """Create UnifiedInvoiceData from legacy formats"""
        # Handle various input formats
        if "invoice_data" in data and isinstance(data["invoice_data"], dict):
            invoice_data = data["invoice_data"]
        elif "invoice_response" in data and "invoice_data" in data["invoice_response"]:
            invoice_data = data["invoice_response"]["invoice_data"]
        else:
            invoice_data = data
        
        # Extract client and service provider
        client = None
        if "client" in invoice_data and invoice_data["client"]:
            client_data = invoice_data["client"]
            client = UnifiedParty(
                name=client_data.get("name", ""),
                email=client_data.get("email"),
                address=client_data.get("address"),
                phone=client_data.get("phone"),
                tax_id=client_data.get("tax_id"),
                role=PartyRole.CLIENT
            )
        
        service_provider = None
        if "service_provider" in invoice_data and invoice_data["service_provider"]:
            provider_data = invoice_data["service_provider"]
            service_provider = UnifiedParty(
                name=provider_data.get("name", ""),
                email=provider_data.get("email"),
                address=provider_data.get("address"),
                phone=provider_data.get("phone"),
                tax_id=provider_data.get("tax_id"),
                role=PartyRole.SERVICE_PROVIDER
            )
        
        # Extract payment terms
        payment_terms = None
        if "payment_terms" in invoice_data and invoice_data["payment_terms"]:
            pt_data = invoice_data["payment_terms"]
            payment_terms = UnifiedPaymentTerms(
                amount=pt_data.get("amount"),
                currency=pt_data.get("currency", "USD"),
                frequency=pt_data.get("frequency"),
                due_days=pt_data.get("due_days", 30),
                late_fee=pt_data.get("late_fee"),
                discount_terms=pt_data.get("discount_terms"),
                payment_method=pt_data.get("payment_method", "bank_transfer")
            )
        
        # Extract services
        services = []
        if "services" in invoice_data and isinstance(invoice_data["services"], list):
            for service_data in invoice_data["services"]:
                services.append(UnifiedServiceItem(
                    description=service_data.get("description", "Service"),
                    quantity=service_data.get("quantity", 1.0),
                    unit_price=service_data.get("unit_price"),
                    total_amount=service_data.get("total_amount"),
                    unit=service_data.get("unit", "service")
                ))
        
        # Extract metadata
        metadata = UnifiedInvoiceMetadata(
            workflow_id=invoice_data.get("workflow_id"),
            confidence_score=invoice_data.get("confidence_score"),
            extracted_at=invoice_data.get("extracted_at")
        )
        
        return cls(
            contract_title=invoice_data.get("contract_title"),
            contract_type=invoice_data.get("contract_type"),
            contract_number=invoice_data.get("contract_number"),
            client=client,
            service_provider=service_provider,
            start_date=invoice_data.get("start_date"),
            end_date=invoice_data.get("end_date"),
            effective_date=invoice_data.get("effective_date"),
            payment_terms=payment_terms,
            services=services,
            invoice_frequency=invoice_data.get("invoice_frequency"),
            first_invoice_date=invoice_data.get("first_invoice_date"),
            next_invoice_date=invoice_data.get("next_invoice_date"),
            special_terms=invoice_data.get("special_terms"),
            notes=invoice_data.get("notes"),
            metadata=metadata
        )
    
    def apply_manual_corrections(self, corrections: Dict[str, Any]) -> "UnifiedInvoiceData":
        """Apply manual field corrections to the invoice data"""
        updated_data = self.dict()
        
        for field_path, new_value in corrections.items():
            if new_value is not None and str(new_value).strip():
                self._set_nested_field(updated_data, field_path, new_value)
        
        # Ensure required role fields are set based on party context
        if updated_data.get("client"):
            if not updated_data["client"].get("role"):
                updated_data["client"]["role"] = PartyRole.CLIENT.value
        
        if updated_data.get("service_provider"):
            if not updated_data["service_provider"].get("role"):
                updated_data["service_provider"]["role"] = PartyRole.SERVICE_PROVIDER.value
                
        # Handle cases where corrections might have created party data without roles
        for field_path, new_value in corrections.items():
            if field_path.startswith("client.") and updated_data.get("client"):
                if not updated_data["client"].get("role"):
                    updated_data["client"]["role"] = PartyRole.CLIENT.value
            elif field_path.startswith("service_provider.") and updated_data.get("service_provider"):
                if not updated_data["service_provider"].get("role"):
                    updated_data["service_provider"]["role"] = PartyRole.SERVICE_PROVIDER.value
        
        # Mark as having human input applied
        updated_data["metadata"]["human_input_applied"] = True
        updated_data["metadata"]["human_reviewed"] = True
        updated_data["metadata"]["updated_at"] = datetime.now()
        
        return UnifiedInvoiceData(**updated_data)
    
    def _set_nested_field(self, data_dict: Dict[str, Any], field_path: str, value: Any):
        """Set nested field value using dot notation"""
        keys = field_path.split('.')
        current = data_dict
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif current[key] is None:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    @validator('client', pre=True)
    def ensure_client_role(cls, v):
        """Ensure client has correct role"""
        if v and isinstance(v, dict) and not v.get('role'):
            v['role'] = PartyRole.CLIENT.value
        return v
    
    @validator('service_provider', pre=True)
    def ensure_service_provider_role(cls, v):
        """Ensure service provider has correct role"""
        if v and isinstance(v, dict) and not v.get('role'):
            v['role'] = PartyRole.SERVICE_PROVIDER.value
        return v
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            date: lambda d: d.isoformat(),
            Decimal: lambda d: str(d)
        }


class UnifiedInvoiceRequest(BaseModel):
    """Request to process invoice with unified format"""
    user_id: str
    contract_name: str
    invoice_data: Optional[UnifiedInvoiceData] = None
    corrections: Optional[Dict[str, Any]] = None


class UnifiedInvoiceResponse(BaseModel):
    """Response with unified invoice data"""
    status: str
    message: str
    invoice_data: Optional[UnifiedInvoiceData] = None
    validation_results: Optional[Dict[str, Any]] = None
    processing_metadata: Optional[Dict[str, Any]] = None