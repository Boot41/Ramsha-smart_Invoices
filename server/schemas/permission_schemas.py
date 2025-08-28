from pydantic import BaseModel, EmailStr
from typing import Optional
from .user_schemas import UserRole


class TenantPermissions(BaseModel):
    # Dashboard and Overview
    dashboard_access: bool = True
    view_all_properties: bool = True
    view_all_tenants: bool = True
    
    # Rental Agreement Management
    create_rental_agreements: bool = True
    edit_rental_agreements: bool = True
    delete_rental_agreements: bool = True
    view_rental_agreements: bool = True
    
    # Rent Payment Management
    create_rent_schedules: bool = True
    edit_rent_schedules: bool = True
    view_payment_history: bool = True
    send_payment_reminders: bool = True
    
    # User Management
    manage_rent_payers: bool = True
    add_rent_payers: bool = True
    remove_rent_payers: bool = True
    
    # Reports and Analytics
    view_reports: bool = True
    export_data: bool = True
    view_analytics: bool = True


class RentPayerPermissions(BaseModel):
    # Limited dashboard access
    dashboard_access: bool = True
    view_own_payments: bool = True
    
    # Payment related access only
    view_payment_due: bool = True
    view_payment_history: bool = True
    make_payments: bool = True
    view_payment_receipts: bool = True
    
    # Rental agreement (read-only)
    view_rental_agreement: bool = True
    
    # Profile management
    update_profile: bool = True
    
    # No access to these
    create_rental_agreements: bool = False
    edit_rental_agreements: bool = False
    manage_users: bool = False
    view_reports: bool = False


class RolePermissions(BaseModel):
    role: UserRole
    tenant_permissions: Optional[TenantPermissions] = None
    rent_payer_permissions: Optional[RentPayerPermissions] = None
    
    def get_permissions(self):
        if self.role == UserRole.TENANT:
            return self.tenant_permissions or TenantPermissions()
        elif self.role == UserRole.RENT_PAYER:
            return self.rent_payer_permissions or RentPayerPermissions()
        return None


class UserPermissionResponse(BaseModel):
    user_email: EmailStr
    role: UserRole
    permissions: dict