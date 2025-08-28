from .address_schemas import (
    AddressBase,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    Address  # For backward compatibility
)

from .user_schemas import (
    UserRole,
    UserBase,
    UserRegistrationRequest,
    UserResponse,
    TenantRegistrationRequest,
    RentPayerRegistrationRequest,
    UserLoginRequest,
    UserLoginResponse,
    UpdateUserRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest
)

from .property_schemas import (
    PropertyType,
    PropertyBase,
    PropertyCreate,
    PropertyResponse,
    PropertyUpdate,
    PropertyReference
)

from .permission_schemas import (
    TenantPermissions,
    RentPayerPermissions,
    RolePermissions,
    UserPermissionResponse
)

from .invoice_schemas import (
    PaymentStatus,
    RentalAgreementStatus,
    RentalAgreementBase,
    RentalAgreementCreate,
    RentalAgreementResponse,
    RentalAgreementUpdate,
    RentPaymentBase,
    RentPaymentCreate,
    RentPaymentResponse,
    RentPaymentUpdateRequest,
    BulkRentPaymentCreate,
    DownloadAgreementRequest,
    PaymentReceiptRequest
)

from .schedule_schemas import (
    RentScheduleFrequency,
    ReminderType,
    ScheduleStatus,
    RentScheduleBase,
    RentScheduleCreate,
    RentScheduleResponse,
    RentScheduleUpdate,
    PaymentReminderBase,
    PaymentReminderCreate,
    PaymentReminderResponse,
    PaymentReminderUpdate,
    ScheduledReminderRecord,
    BulkReminderRequest,
    RescheduleRentRequest
)

from .document_schemas import (
    DocumentType,
    DocumentStatus,
    UploadSource,
    DocumentUploadRequest,
    DocumentProcessingRequest,
    DocumentBase,
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    DocumentProcessingResponse,
    DocumentListResponse,
    DocumentErrorResponse,
    BulkDocumentUploadRequest,
    BulkDocumentUploadResponse
)

__all__ = [
    # Address schemas
    "AddressBase",
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
    "Address",
    
    # User schemas
    "UserRole",
    "UserBase",
    "UserRegistrationRequest", 
    "UserResponse",
    "TenantRegistrationRequest",
    "RentPayerRegistrationRequest",
    "UserLoginRequest",
    "UserLoginResponse",
    "UpdateUserRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "ChangePasswordRequest",
    
    # Property schemas
    "PropertyType",
    "PropertyBase",
    "PropertyCreate",
    "PropertyResponse",
    "PropertyUpdate",
    "PropertyReference",
    
    # Permission schemas
    "TenantPermissions",
    "RentPayerPermissions",
    "RolePermissions",
    "UserPermissionResponse",
    
    # Rental Agreement & Payment schemas
    "PaymentStatus",
    "RentalAgreementStatus",
    "RentalAgreementBase",
    "RentalAgreementCreate",
    "RentalAgreementResponse",
    "RentalAgreementUpdate",
    "RentPaymentBase",
    "RentPaymentCreate",
    "RentPaymentResponse",
    "RentPaymentUpdateRequest",
    "BulkRentPaymentCreate",
    "DownloadAgreementRequest",
    "PaymentReceiptRequest",
    
    # Schedule schemas
    "RentScheduleFrequency",
    "ReminderType",
    "ScheduleStatus",
    "RentScheduleBase",
    "RentScheduleCreate",
    "RentScheduleResponse",
    "RentScheduleUpdate",
    "PaymentReminderBase",
    "PaymentReminderCreate",
    "PaymentReminderResponse",
    "PaymentReminderUpdate",
    "ScheduledReminderRecord",
    "BulkReminderRequest",
    "RescheduleRentRequest",
    
    # Document schemas
    "DocumentType",
    "DocumentStatus",
    "UploadSource",
    "DocumentUploadRequest",
    "DocumentProcessingRequest",
    "DocumentBase",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentUpdate",
    "DocumentUploadResponse",
    "DocumentProcessingResponse",
    "DocumentListResponse",
    "DocumentErrorResponse",
    "BulkDocumentUploadRequest",
    "BulkDocumentUploadResponse"
]