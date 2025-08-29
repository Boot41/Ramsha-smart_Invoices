from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
import uuid
from db.postgresdb import Base


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