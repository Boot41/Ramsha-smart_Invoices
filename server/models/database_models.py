from sqlalchemy import Column, String, DateTime, Boolean, Integer, Enum as SQLEnum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import bcrypt
import secrets
import uuid
import enum
from db.postgresdb import Base


class UserRole(str, enum.Enum):
    TENANT = "tenant"
    RENT_PAYER = "rent_payer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Address(Base):
    __tablename__ = "addresses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    street = Column(String(255), nullable=False)
    building_number = Column(String(20), nullable=True)
    room_number = Column(String(10), nullable=True)
    floor = Column(String(10), nullable=True)
    apartment_unit = Column(String(20), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False, default="USA")
    landmark = Column(String(255), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def get_full_address(self) -> str:
        """Returns formatted full address string"""
        parts = []
        
        # Building info
        building_parts = []
        if self.building_number:
            building_parts.append(self.building_number)
        building_parts.append(self.street)
        parts.append(" ".join(building_parts))
        
        # Unit info
        unit_parts = []
        if self.apartment_unit:
            unit_parts.append(f"Unit {self.apartment_unit}")
        if self.room_number:
            unit_parts.append(f"Room {self.room_number}")
        if self.floor:
            unit_parts.append(f"Floor {self.floor}")
        if unit_parts:
            parts.append(", ".join(unit_parts))
        
        # Location info
        location_parts = [self.city, self.state, self.postal_code]
        if self.country and self.country.upper() != "USA":
            location_parts.append(self.country)
        parts.append(", ".join(filter(None, location_parts)))
        
        return ", ".join(parts)


class User(Base):
    """User model for authentication and profile management"""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    tenant_email = Column(String(255), nullable=True)  # For rent_payers
    address_id = Column(String, ForeignKey("addresses.id"), nullable=True)
    
    # Authentication fields
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Security tracking
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)
    lockout_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_metadata = Column(JSON, nullable=True)
    
    # Relationships
    address = relationship("Address", backref="users")
    
    @property
    def name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def set_password(self, password: str):
        """Set new password (hashed)"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def generate_email_verification_token(self) -> str:
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = datetime.now(timezone.utc) + timedelta(days=1)
        return self.email_verification_token
    
    def verify_email_token(self, token: str) -> bool:
        """Verify email verification token"""
        if not self.email_verification_token or not self.email_verification_expires:
            return False
        
        if datetime.now(timezone.utc) > self.email_verification_expires:
            return False
        
        if self.email_verification_token != token:
            return False
        
        # Mark email as verified
        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_expires = None
        return True
    
    def generate_password_reset_token(self) -> str:
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        return self.password_reset_token
    
    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if datetime.now(timezone.utc) > self.password_reset_expires:
            return False
        
        return self.password_reset_token == token
    
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using valid token"""
        if not self.verify_password_reset_token(token):
            return False
        
        self.set_password(new_password)
        self.password_reset_token = None
        self.password_reset_expires = None
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.lockout_until = None
        return True
    
    def record_login_attempt(self, success: bool, ip_address: Optional[str] = None):
        """Record login attempt"""
        if success:
            self.last_login = datetime.now(timezone.utc)
            self.failed_login_attempts = 0
            self.last_failed_login = None
            if self.lockout_until:
                self.lockout_until = None
        else:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.now(timezone.utc)
            
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.lockout_until = datetime.now(timezone.utc) + timedelta(hours=1)
    
    def is_account_locked(self) -> bool:
        """Check if account is locked"""
        if not self.lockout_until:
            return False
        
        if datetime.now(timezone.utc) > self.lockout_until:
            # Unlock expired lock
            self.lockout_until = None
            self.failed_login_attempts = 0
            return False
        
        return True
    
    def update_profile(self, name: Optional[str] = None, phone: Optional[str] = None):
        """Update user profile information"""
        if name is not None:
            self.name = name.strip()
        if phone is not None:
            self.phone = phone
    
    def can_login(self) -> tuple[bool, Optional[str]]:
        """Check if user can login"""
        if self.status != UserStatus.ACTIVE:
            return False, f"Account is {self.status.value}"
        
        if self.is_account_locked():
            return False, "Account is temporarily locked due to failed login attempts"
        
        return True, None
    
    def get_permissions(self) -> Dict[str, bool]:
        """Get user permissions based on role"""
        if self.role == UserRole.TENANT:
            return {
                "dashboard_access": True,
                "view_all_properties": True,
                "create_rental_agreements": True,
                "edit_rental_agreements": True,
                "delete_rental_agreements": True,
                "manage_rent_payers": True,
                "view_reports": True,
                "export_data": True,
                "send_payment_reminders": True
            }
        elif self.role == UserRole.RENT_PAYER:
            return {
                "dashboard_access": True,
                "view_own_payments": True,
                "view_payment_due": True,
                "make_payments": True,
                "view_payment_receipts": True,
                "view_rental_agreement": True,
                "update_profile": True
            }
        else:
            return {}


class SecurityEvent(Base):
    """Security event logging model"""
    
    __tablename__ = "security_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship
    user = relationship("User", backref="security_events")


class UserSession(Base):
    """User session management model"""
    
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", backref="sessions")


class Invoice(Base):
    """Invoice model for storing generated invoice data"""
    
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Invoice details
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.GENERATED)
    
    # Parties information
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255), nullable=True)
    client_address = Column(Text, nullable=True)
    client_phone = Column(String(50), nullable=True)
    
    service_provider_name = Column(String(255), nullable=False)
    service_provider_email = Column(String(255), nullable=True)
    service_provider_address = Column(Text, nullable=True)
    service_provider_phone = Column(String(50), nullable=True)
    
    # Financial information
    subtotal = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USD")
    
    # Contract details
    contract_title = Column(String(255), nullable=True)
    contract_type = Column(String(100), nullable=True)
    contract_reference = Column(String(255), nullable=True)
    
    # Complete invoice data (JSON)
    invoice_data = Column(JSON, nullable=False)
    
    # AI generation metadata
    generated_by_agent = Column(String(100), nullable=False, default="correction_agent")
    confidence_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    human_reviewed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="invoices")
    invoice_templates = relationship("InvoiceTemplate", backref="invoice", cascade="all, delete-orphan")


class InvoiceTemplate(Base):
    """Invoice template model for storing generated React components"""
    
    __tablename__ = "invoice_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    
    # Template details
    template_name = Column(String(255), nullable=False)
    component_name = Column(String(255), nullable=False)
    template_type = Column(String(100), nullable=False, default="Professional Invoice Template")
    
    # File system details
    file_path = Column(String(500), nullable=False)
    component_code = Column(Text, nullable=False)
    
    # Generation metadata
    generated_by = Column(String(100), nullable=False, default="ui_invoice_generator")
    model_used = Column(String(100), nullable=True)
    
    # Status and availability
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class InvoiceFrequency(str, enum.Enum):
    """Invoice frequency enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ContractType(str, enum.Enum):
    """Contract type enumeration"""
    SERVICE = "service"
    RENTAL = "rental"
    CONSULTING = "consulting"
    SUBSCRIPTION = "subscription"
    OTHER = "other"


class Contract(Base):
    """Contract model for storing uploaded contract information"""
    
    __tablename__ = "contracts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, nullable=True, unique=True, index=True)  # Custom contract ID for GCP path
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False, unique=True, index=True)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False, default="application/pdf")
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    
    # Processing information
    is_processed = Column(Boolean, default=False)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    total_chunks = Column(Integer, nullable=True)
    total_embeddings = Column(Integer, nullable=True)
    pinecone_vector_ids = Column(JSON, nullable=True)  # List of vector IDs in Pinecone
    text_preview = Column(Text, nullable=True)
    processing_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="contracts")
    extracted_invoice_data = relationship("ExtractedInvoiceData", backref="contract", cascade="all, delete-orphan")


class ContractParty(Base):
    """Contract party model for storing party information"""
    
    __tablename__ = "contract_parties"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    
    # Party information
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(100), nullable=True)
    role = Column(String(100), nullable=False)  # client, service_provider, tenant, landlord
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("Contract", backref="parties")


class ExtractedInvoiceData(Base):
    """Model for storing extracted invoice data from contracts"""
    
    __tablename__ = "extracted_invoice_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Invoice scheduling
    invoice_frequency = Column(SQLEnum(InvoiceFrequency), nullable=True)
    first_invoice_date = Column(DateTime(timezone=True), nullable=True)
    next_invoice_date = Column(DateTime(timezone=True), nullable=True)
    
    # Payment terms
    payment_amount = Column(Float, nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    payment_due_days = Column(Integer, nullable=False, default=30)
    late_fee = Column(Float, nullable=True)
    discount_terms = Column(String(500), nullable=True)
    
    # Services and terms
    services = Column(JSON, nullable=True)  # List of service items
    special_terms = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # AI extraction metadata
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    extraction_query = Column(Text, nullable=True)
    raw_ai_response = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")


class GeneratedInvoice(Base):
    """Model for storing generated invoices from extracted data"""
    
    __tablename__ = "generated_invoices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    extracted_data_id = Column(String, ForeignKey("extracted_invoice_data.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Invoice details
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.GENERATED)
    
    # Financial information
    subtotal = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USD")
    
    # Complete invoice data (JSON)
    invoice_data = Column(JSON, nullable=False)
    
    # Generation metadata
    generated_by = Column(String(100), nullable=False, default="ai_agent")
    generation_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("Contract")
    extracted_data = relationship("ExtractedInvoiceData")
    user = relationship("User")