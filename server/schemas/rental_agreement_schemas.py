from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class RentalAgreementType(str, Enum):
    MONTH_TO_MONTH = "month_to_month"
    FIXED_TERM = "fixed_term"
    RENT_TO_OWN = "rent_to_own"
    STANDARD_RESIDENTIAL = "standard_residential"
    SHORT_TERM_VACATION = "short_term_vacation"
    SUBLEASE = "sublease"
    ROOM_RENTAL = "room_rental"
    COMMERCIAL_LEASE = "commercial_lease"
    LAND_LEASE = "land_lease"
    LEAVE_AND_LICENSE = "leave_and_license"
    PAYING_GUEST = "paying_guest"


class PropertyType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    LAND = "land"
    ROOM = "room"
    APARTMENT = "apartment"
    HOUSE = "house"
    OFFICE = "office"
    SHOP = "shop"
    WAREHOUSE = "warehouse"


class PaymentFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ONE_TIME = "one_time"
    DAILY = "daily"


class ContactInfo(BaseModel):
    """Contact information for parties"""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    alternative_contact: Optional[str] = None
    business_registration: Optional[str] = None  # For commercial entities
    

class PropertyInfo(BaseModel):
    """Property details"""
    description: Optional[str] = None
    address: Optional[str] = None
    property_type: Optional[PropertyType] = None
    size: Optional[str] = None  # "1200 sq ft", "3 BHK", etc.
    unique_features: Optional[str] = None
    furnishing_status: Optional[str] = None  # "Furnished", "Semi-furnished", "Unfurnished"
    floor: Optional[str] = None
    parking: Optional[str] = None
    utilities_included: Optional[List[str]] = []


class AmountInfo(BaseModel):
    """Amount with text parsing capabilities"""
    numeric_value: Optional[Decimal] = None
    text_value: Optional[str] = None  # "Four Thousand Rupees"
    currency: str = "INR"
    
    @validator('numeric_value', pre=True)
    def parse_amount(cls, v):
        """Parse amount from various text formats"""
        if isinstance(v, str):
            # Remove common currency symbols and formatting
            clean_amount = v.replace('Rs.', '').replace('₹', '').replace('$', '').replace(',', '').strip()
            try:
                return Decimal(clean_amount)
            except:
                return None
        return v


class PaymentTerms(BaseModel):
    """Payment terms with advanced parsing"""
    rent_amount: Optional[AmountInfo] = None
    security_deposit: Optional[AmountInfo] = None
    advance_payment: Optional[AmountInfo] = None
    maintenance_charges: Optional[AmountInfo] = None
    frequency: Optional[PaymentFrequency] = PaymentFrequency.MONTHLY
    due_date: Optional[int] = None  # Day of month (1-31)
    late_fee: Optional[AmountInfo] = None
    increment_percentage: Optional[Decimal] = None  # Annual increment
    payment_method: Optional[str] = None
    bank_details: Optional[str] = None


class BaseRentalAgreement(BaseModel):
    """Base rental agreement with common fields"""
    agreement_type: RentalAgreementType
    landlord: ContactInfo
    tenant: ContactInfo
    property_info: PropertyInfo
    payment_terms: PaymentTerms
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    agreement_date: Optional[date] = None
    duration_text: Optional[str] = None  # "eleven months", "2 years"
    witness_details: Optional[List[ContactInfo]] = []
    additional_clauses: Optional[List[str]] = []
    termination_clause: Optional[str] = None
    renewal_terms: Optional[str] = None
    additional_notes: Optional[str] = None
    
    # Metadata
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    extracted_at: Optional[datetime] = None


class MonthToMonthRentalAgreement(BaseRentalAgreement):
    """Month-to-month rental agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.MONTH_TO_MONTH
    notice_period_days: Optional[int] = 30
    automatic_renewal: bool = True
    rent_review_period: Optional[int] = None  # months


class FixedTermRentalAgreement(BaseRentalAgreement):
    """Fixed-term rental agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.FIXED_TERM
    term_length_months: Optional[int] = None
    early_termination_penalty: Optional[AmountInfo] = None
    renewal_option: bool = False
    lock_in_period: Optional[int] = None  # months


class RentToOwnAgreement(FixedTermRentalAgreement):
    """Rent-to-own agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.RENT_TO_OWN
    option_to_purchase: bool = True
    purchase_price: Optional[AmountInfo] = None
    portion_rent_to_purchase: Optional[Decimal] = None  # Percentage
    option_expiry_date: Optional[date] = None
    purchase_terms: Optional[str] = None


class StandardResidentialRentalAgreement(FixedTermRentalAgreement):
    """Standard residential rental agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.STANDARD_RESIDENTIAL
    pet_policy: Optional[str] = None
    maintenance_responsibility: Optional[str] = None
    subletting_allowed: bool = False
    visitor_policy: Optional[str] = None


class ShortTermRentalAgreement(BaseRentalAgreement):
    """Short-term/vacation rental agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.SHORT_TERM_VACATION
    rental_duration_days: Optional[int] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    cleaning_fee: Optional[AmountInfo] = None
    cancellation_policy: Optional[str] = None
    house_rules: Optional[List[str]] = []


class SubleaseAgreement(BaseRentalAgreement):
    """Sublease agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.SUBLEASE
    original_tenant: ContactInfo
    subtenant: ContactInfo
    original_lease_expiry: Optional[date] = None
    landlord_consent: bool = False
    sublease_portion: Optional[str] = None  # "entire property", "one room"


class RoomRentalAgreement(BaseRentalAgreement):
    """Room rental agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.ROOM_RENTAL
    room_number: Optional[str] = None
    shared_facilities: Optional[List[str]] = []
    house_rules: Optional[List[str]] = []
    common_area_access: Optional[str] = None


class CommercialLeaseAgreement(BaseRentalAgreement):
    """Commercial lease agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.COMMERCIAL_LEASE
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    permitted_use: Optional[str] = None
    operating_hours: Optional[str] = None
    signage_rights: Optional[str] = None
    common_area_maintenance: Optional[AmountInfo] = None
    property_tax_responsibility: Optional[str] = None
    insurance_requirements: Optional[str] = None
    renewal_terms: Optional[str] = None
    base_rent: Optional[AmountInfo] = None
    percentage_rent: Optional[Decimal] = None  # Percentage of sales


class LandLeaseAgreement(BaseRentalAgreement):
    """Land lease agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.LAND_LEASE
    land_area: Optional[str] = None  # "2 acres", "5000 sq ft"
    land_survey_number: Optional[str] = None
    permitted_activities: Optional[List[str]] = []
    development_rights: Optional[str] = None
    agricultural_use: bool = False
    construction_allowed: bool = False
    water_rights: Optional[str] = None


class LeaveAndLicenseAgreement(BaseRentalAgreement):
    """Leave and License agreement (Indian)"""
    agreement_type: RentalAgreementType = RentalAgreementType.LEAVE_AND_LICENSE
    license_period_months: Optional[int] = None
    license_fee: Optional[AmountInfo] = None
    occupancy_rights: Optional[str] = None
    licensee_obligations: Optional[List[str]] = []
    licensor_obligations: Optional[List[str]] = []
    registration_required: bool = False


class PayingGuestAgreement(BaseRentalAgreement):
    """Paying Guest (PG) agreement"""
    agreement_type: RentalAgreementType = RentalAgreementType.PAYING_GUEST
    meals_included: bool = False
    meal_times: Optional[List[str]] = []
    utilities_included: Optional[List[str]] = []
    bed_type: Optional[str] = None  # "single", "double", "bunk"
    sharing_type: Optional[str] = None  # "single occupancy", "double sharing"
    common_facilities: Optional[List[str]] = []
    pg_rules: Optional[List[str]] = []
    food_preferences: Optional[str] = None  # "veg", "non-veg", "both"


# Union type for all rental agreements
RentalAgreementUnion = Union[
    MonthToMonthRentalAgreement,
    FixedTermRentalAgreement,
    RentToOwnAgreement,
    StandardResidentialRentalAgreement,
    ShortTermRentalAgreement,
    SubleaseAgreement,
    RoomRentalAgreement,
    CommercialLeaseAgreement,
    LandLeaseAgreement,
    LeaveAndLicenseAgreement,
    PayingGuestAgreement
]


class RentalAgreementExtractionResult(BaseModel):
    """Result of rental agreement extraction"""
    identified_type: RentalAgreementType
    confidence_score: float = Field(ge=0.0, le=1.0)
    agreement_data: RentalAgreementUnion
    raw_text_analysis: Optional[Dict[str, Any]] = None
    extraction_notes: Optional[List[str]] = []
    requires_human_review: bool = False
    extracted_at: datetime = Field(default_factory=datetime.now)