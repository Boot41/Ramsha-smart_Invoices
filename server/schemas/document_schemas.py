from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    LEASE_AGREEMENT = "lease_agreement"
    PAYMENT_RECEIPT = "payment_receipt"
    IDENTIFICATION = "identification"
    BANK_STATEMENT = "bank_statement"
    OTHER = "other"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    REJECTED = "rejected"


class UploadSource(str, Enum):
    WEB_UPLOAD = "web_upload"
    EMAIL = "email"
    DRIVE = "drive"


class DocumentUploadRequest(BaseModel):
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType = Field(..., description="Type of document")
    description: Optional[str] = Field(None, description="Optional description")
    tags: Optional[List[str]] = Field(default=[], description="Document tags")
    source: UploadSource = Field(default=UploadSource.WEB_UPLOAD)
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")


class DocumentProcessingRequest(BaseModel):
    document_id: str
    processing_options: Optional[Dict[str, Any]] = Field(default={})


class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    document_type: DocumentType
    file_size: int
    content_type: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    source: UploadSource = UploadSource.WEB_UPLOAD
    metadata: Optional[Dict[str, Any]] = {}
    status: DocumentStatus = DocumentStatus.PENDING
    uploaded_by: EmailStr
    user_id: Optional[str] = None


class DocumentCreate(DocumentBase):
    gcp_bucket_path: str
    file_hash: str


class DocumentResponse(DocumentBase):
    id: str
    gcp_bucket_path: str
    file_hash: str
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    processing_status: Optional[str] = None
    processing_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    document_type: Optional[DocumentType] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[DocumentStatus] = None
    processing_results: Optional[Dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    upload_url: Optional[str] = None
    processing_status: str = "pending"
    metadata: Optional[Dict[str, Any]] = None


class DocumentProcessingResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    processing_status: str
    results: Optional[Dict[str, Any]] = None
    timestamp: datetime


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class DocumentErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BulkDocumentUploadRequest(BaseModel):
    documents: List[DocumentUploadRequest]
    batch_metadata: Optional[Dict[str, Any]] = {}


class BulkDocumentUploadResponse(BaseModel):
    success: bool
    message: str
    total_documents: int
    successful_uploads: int
    failed_uploads: int
    results: List[DocumentUploadResponse]
    batch_id: Optional[str] = None