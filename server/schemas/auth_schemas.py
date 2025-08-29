from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from .user_schemas import UserRole
from .address_schemas import AddressCreate, AddressResponse


class AuthStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


# Registration Schemas
class UserRegistrationRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    first_name: str = Field(..., min_length=2, max_length=50, description="First name")
    last_name: str = Field(..., min_length=2, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    role: UserRole = Field(UserRole.TENANT, description="User role (default: tenant)")
    address: Optional[AddressCreate] = Field(None, description="User address")
    tenant_email: Optional[EmailStr] = Field(None, description="Associated tenant email (for rent_payers)")
    
    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    
    @validator('tenant_email')
    def validate_tenant_email(cls, v, values):
        if values.get('role') == UserRole.RENT_PAYER and not v:
            raise ValueError('Tenant email is required for rent payers')
        if values.get('role') == UserRole.TENANT and v:
            raise ValueError('Tenant email should not be provided for tenant role')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('+', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v


class UserRegistrationResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    email: EmailStr
    role: UserRole
    verification_required: bool = False
    verification_method: Optional[str] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # seconds
    user: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None


# Login Schemas
class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Extended session duration")


class UserLoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # seconds
    user: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None


# Password Management Schemas
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetResponse(BaseModel):
    success: bool
    message: str
    reset_token: Optional[str] = None  # For forgot password
    expires_at: Optional[datetime] = None


# Profile Management Schemas
class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None)
    address: Optional[AddressCreate] = Field(None)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('+', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v


class UserProfileResponse(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: UserRole
    status: AuthStatus
    address: Optional[AddressResponse] = None
    tenant_email: Optional[EmailStr] = None  # For rent_payers
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    email_verified: bool = False
    phone_verified: bool = False


# Email Verification Schemas
class EmailVerificationRequest(BaseModel):
    token: str = Field(..., description="Email verification token")


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class VerificationResponse(BaseModel):
    success: bool
    message: str
    verification_token: Optional[str] = None
    expires_at: Optional[datetime] = None


# Session Management Schemas
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    logout_all_devices: bool = Field(default=False, description="Logout from all devices")


class SessionInfo(BaseModel):
    session_id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False


class UserSessionsResponse(BaseModel):
    success: bool
    active_sessions: list[SessionInfo]
    total_sessions: int


# Admin/Management Schemas
class UserSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    role: Optional[UserRole] = Field(None, description="Filter by role")
    status: Optional[AuthStatus] = Field(None, description="Filter by status")
    limit: int = Field(50, ge=1, le=100, description="Maximum results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class UserListResponse(BaseModel):
    users: list[UserProfileResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class UpdateUserStatusRequest(BaseModel):
    user_id: str
    status: AuthStatus
    reason: Optional[str] = Field(None, description="Reason for status change")


# Security Schemas
class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    PROFILE_UPDATE = "profile_update"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class SecurityEvent(BaseModel):
    event_type: SecurityEventType
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SecurityLogResponse(BaseModel):
    events: list[SecurityEvent]
    total: int
    filtered_total: int


# Error Response Schema
class AuthErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Bulk Operations Schemas
class BulkUserInviteRequest(BaseModel):
    invitations: list[Dict[str, Any]]  # List of user invitation data
    tenant_email: EmailStr  # Tenant who is sending invites
    default_role: UserRole = UserRole.RENT_PAYER
    send_email: bool = True


class BulkUserInviteResponse(BaseModel):
    success: bool
    message: str
    total_invitations: int
    successful_invitations: int
    failed_invitations: int
    results: list[Dict[str, Any]]
    batch_id: Optional[str] = None