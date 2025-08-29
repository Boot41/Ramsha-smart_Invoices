from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum
from .address_schemas import AddressResponse, AddressCreate


class UserRole(str, Enum):
    TENANT = "tenant"
    RENT_PAYER = "rent_payer"


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole
    address_id: Optional[str] = None  # Reference to Address table
    
    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserRegistrationRequest(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    address: Optional[AddressResponse] = None  # Populated address details
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    last_login: Optional[datetime] = None


class TenantRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[AddressCreate] = None  # Embedded for creation
    
    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class RentPayerRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    tenant_email: EmailStr  # Which tenant they are associated with
    
    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[AddressCreate] = None  # Can update address


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str