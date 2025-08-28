from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .address_schemas import AddressResponse, AddressCreate


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"
    STUDIO = "studio"
    OTHER = "other"


class PropertyBase(BaseModel):
    name: Optional[str] = None  # Property name/identifier
    property_type: PropertyType
    address_id: str  # Reference to Address
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    amenities: Optional[List[str]] = []
    description: Optional[str] = None
    owner_email: EmailStr  # Reference to tenant who owns the property


class PropertyCreate(PropertyBase):
    address: AddressCreate  # Embedded address for creation


class PropertyResponse(PropertyBase):
    id: str
    address: Optional[AddressResponse] = None  # Populated address details
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    property_type: Optional[PropertyType] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    amenities: Optional[List[str]] = None
    description: Optional[str] = None
    address: Optional[AddressCreate] = None  # Can update address


class PropertyReference(BaseModel):
    property_id: str
    property_name: Optional[str] = None  # For display purposes