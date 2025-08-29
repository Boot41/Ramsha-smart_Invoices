from sqlalchemy import Column, String, DateTime, Boolean, Integer, Enum as SQLEnum, ForeignKey, Text
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