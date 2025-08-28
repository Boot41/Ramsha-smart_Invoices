from typing import Optional, List, Dict, Any
from datetime import datetime
from schemas.document_schemas import DocumentType, DocumentStatus, UploadSource
import hashlib
import os


class DocumentModel:
    """Document model for database operations"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        filename: str = "",
        original_filename: str = "",
        document_type: DocumentType = DocumentType.OTHER,
        file_size: int = 0,
        content_type: str = "",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: UploadSource = UploadSource.WEB_UPLOAD,
        metadata: Optional[Dict[str, Any]] = None,
        status: DocumentStatus = DocumentStatus.PENDING,
        uploaded_by: str = "",
        gcp_bucket_path: str = "",
        file_hash: str = "",
        download_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        processing_status: Optional[str] = None,
        processing_results: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        processed_at: Optional[datetime] = None
    ):
        self.id = id or self._generate_id()
        self.user_id = user_id
        self.filename = filename
        self.original_filename = original_filename
        self.document_type = document_type
        self.file_size = file_size
        self.content_type = content_type
        self.description = description
        self.tags = tags or []
        self.source = source
        self.metadata = metadata or {}
        self.status = status
        self.uploaded_by = uploaded_by
        self.gcp_bucket_path = gcp_bucket_path
        self.file_hash = file_hash
        self.download_url = download_url
        self.thumbnail_url = thumbnail_url
        self.processing_status = processing_status
        self.processing_results = processing_results or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.processed_at = processed_at
    
    def _generate_id(self) -> str:
        """Generate unique document ID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_file_hash(file_content: bytes) -> str:
        """Generate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def generate_gcp_path(user_email: str, filename: str, document_type: DocumentType) -> str:
        """Generate GCP bucket path for document (no user folders - users stored in PostgreSQL)"""
        # Create folder structure: {document_type}/{timestamp}_{filename}
        # User association will be tracked in PostgreSQL database
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
        return f"{document_type.value}/{timestamp}_{safe_filename}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "document_type": self.document_type.value if isinstance(self.document_type, DocumentType) else self.document_type,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "description": self.description,
            "tags": self.tags,
            "source": self.source.value if isinstance(self.source, UploadSource) else self.source,
            "metadata": self.metadata,
            "status": self.status.value if isinstance(self.status, DocumentStatus) else self.status,
            "uploaded_by": self.uploaded_by,
            "gcp_bucket_path": self.gcp_bucket_path,
            "file_hash": self.file_hash,
            "download_url": self.download_url,
            "thumbnail_url": self.thumbnail_url,
            "processing_status": self.processing_status,
            "processing_results": self.processing_results,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentModel":
        """Create model from dictionary"""
        # Convert string values back to enums
        if isinstance(data.get("document_type"), str):
            data["document_type"] = DocumentType(data["document_type"])
        if isinstance(data.get("source"), str):
            data["source"] = UploadSource(data["source"])
        if isinstance(data.get("status"), str):
            data["status"] = DocumentStatus(data["status"])
        
        # Convert ISO strings back to datetime
        for field in ["created_at", "updated_at", "processed_at"]:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def update_status(self, status: DocumentStatus):
        """Update document status"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if status == DocumentStatus.COMPLETED:
            self.processed_at = datetime.utcnow()
    
    def add_processing_result(self, key: str, value: Any):
        """Add processing result"""
        if not self.processing_results:
            self.processing_results = {}
        self.processing_results[key] = value
        self.updated_at = datetime.utcnow()
    
    def is_valid_file_type(self) -> bool:
        """Check if file type is supported"""
        supported_types = {
            "application/pdf",
            "image/jpeg",
            "image/jpg", 
            "image/png",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        return self.content_type.lower() in supported_types
    
    def get_file_extension(self) -> str:
        """Get file extension from filename"""
        return os.path.splitext(self.filename)[1].lower()
    
    def __repr__(self) -> str:
        return f"DocumentModel(id={self.id}, filename={self.filename}, type={self.document_type}, status={self.status})"
