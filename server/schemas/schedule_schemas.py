from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class RentScheduleFrequency(str, Enum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"


class ReminderType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"


class ScheduleStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RentScheduleBase(BaseModel):
    rental_agreement_id: str
    due_day: int  # Day of month (1-31)
    frequency: RentScheduleFrequency = RentScheduleFrequency.MONTHLY
    amount: Optional[float] = None  # If None, uses agreement amount
    start_date: date
    end_date: Optional[date] = None  # If None, follows lease end date
    auto_generate: bool = True  # Auto-generate payment records
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_by: EmailStr


class RentScheduleCreate(RentScheduleBase):
    pass


class RentScheduleResponse(RentScheduleBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    next_due_date: Optional[date] = None


class RentScheduleUpdate(BaseModel):
    due_day: Optional[int] = None
    frequency: Optional[RentScheduleFrequency] = None
    amount: Optional[float] = None
    end_date: Optional[date] = None
    auto_generate: Optional[bool] = None
    status: Optional[ScheduleStatus] = None


class PaymentReminderBase(BaseModel):
    rental_agreement_id: str
    reminder_types: List[ReminderType]
    days_before_due: List[int] = [7, 3, 1]  # Send reminders X days before due
    days_after_due: List[int] = [1, 3, 7]  # Send overdue reminders
    custom_message: Optional[str] = None
    enabled: bool = True


class PaymentReminderCreate(PaymentReminderBase):
    pass


class PaymentReminderResponse(PaymentReminderBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentReminderUpdate(BaseModel):
    reminder_types: Optional[List[ReminderType]] = None
    days_before_due: Optional[List[int]] = None
    days_after_due: Optional[List[int]] = None
    custom_message: Optional[str] = None
    enabled: Optional[bool] = None


class ScheduledReminderRecord(BaseModel):
    reminder_id: str
    payment_id: str
    rent_payer_email: EmailStr
    reminder_type: ReminderType
    scheduled_datetime: datetime
    status: str = "pending"  # pending, sent, failed
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None


class BulkReminderRequest(BaseModel):
    payment_ids: List[str]
    reminder_type: ReminderType
    custom_message: Optional[str] = None
    send_immediately: bool = False


class RescheduleRentRequest(BaseModel):
    schedule_id: str
    new_due_day: Optional[int] = None
    new_frequency: Optional[RentScheduleFrequency] = None
    reason: Optional[str] = None