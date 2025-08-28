from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AddressBase(BaseModel):
    street: str
    building_number: Optional[str] = None
    room_number: Optional[str] = None
    floor: Optional[str] = None
    apartment_unit: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    landmark: Optional[str] = None
    neighborhood: Optional[str] = None


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    street: Optional[str] = None
    building_number: Optional[str] = None
    room_number: Optional[str] = None
    floor: Optional[str] = None
    apartment_unit: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    landmark: Optional[str] = None
    neighborhood: Optional[str] = None


class AddressResponse(AddressBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
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


# For backward compatibility with existing user_schemas.py
Address = AddressResponse