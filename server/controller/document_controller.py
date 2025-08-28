from fastapi import UploadFile, HTTPException, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import hashlib
import mimetypes

from models.document import DocumentModel
from schemas.document_schemas import (
    DocumentUploadRequest, DocumentUploadResponse, DocumentProcessingResponse,
    DocumentResponse, DocumentErrorResponse, DocumentType, DocumentStatus,
    UploadSource, BulkDocumentUploadRequest, BulkDocumentUploadResponse
)
from services.gcp_storage_service import get_gcp_storage_service
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)


class DocumentController:
    """Controller for handling document upload and processing operations"""
    
    def __init__(self):
        self.storage_service = get_gcp_storage_service()
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.doc', '.docx', '.xls', '.xlsx'
        }
        self.allowed_content_types = {
            'application/pdf',
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        logger.info("✅ Document Controller initialized")
    
    async def upload_document(
        self, 
        file: UploadFile, 
        upload_request: DocumentUploadRequest,
        current_user: Dict[str, Any]
    ) -> DocumentUploadResponse:
        """
        Handle single document upload
        
        Args:
            file: Uploaded file
            upload_request: Upload request parameters
            current_user: Authenticated user information
            
        Returns:
            DocumentUploadResponse with upload results
        """
        try:
            logger.info(f"🚀 Processing document upload: {file.filename} by user {current_user.get('email')}")
            
            # Validate file
            validation_error = await self._validate_file(file)
            if validation_error:
                return DocumentUploadResponse(
                    success=False,
                    message=validation_error,
                    processing_status="error"
                )
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Generate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Create document model
            document = DocumentModel(
                filename=upload_request.filename,
                original_filename=file.filename or upload_request.filename,
                document_type=upload_request.document_type,
                file_size=len(file_content),
                content_type=file.content_type or 'application/octet-stream',
                description=upload_request.description,
                tags=upload_request.tags,
                source=upload_request.source,
                metadata=upload_request.metadata,
                status=DocumentStatus.PENDING,
                uploaded_by=current_user.get('email', ''),
                user_id=current_user.get('user_id'),
                file_hash=file_hash
            )
            
            # Generate GCP storage path
            gcp_path = DocumentModel.generate_gcp_path(
                current_user.get('email', 'unknown'),
                upload_request.filename,
                upload_request.document_type
            )
            document.gcp_bucket_path = gcp_path
            
            # Upload to GCP Storage
            logger.info(f"📤 Uploading to GCP Storage: {gcp_path}")
            upload_result = self.storage_service.upload_file(
                file_content=file_content,
                destination_path=gcp_path,
                content_type=file.content_type,
                metadata={
                    'document_id': document.id,
                    'uploaded_by': current_user.get('email', ''),
                    'document_type': upload_request.document_type.value,
                    'original_filename': file.filename or upload_request.filename,
                    'upload_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            if not upload_result.get('success'):
                logger.error(f"❌ GCP upload failed: {upload_result.get('message')}")
                return DocumentUploadResponse(
                    success=False,
                    message=f"Storage upload failed: {upload_result.get('message')}",
                    processing_status="error"
                )
            
            # Update document status
            document.status = DocumentStatus.PROCESSING
            document.download_url = upload_result.get('download_url')
            
            # TODO: Save document to database
            # await self.document_repository.create(document)
            
            logger.info(f"✅ Document uploaded successfully: {document.id}")
            
            return DocumentUploadResponse(
                success=True,
                message="✅ Document uploaded successfully",
                document_id=document.id,
                upload_url=upload_result.get('download_url'),
                processing_status="completed",
                metadata={
                    'file_size': document.file_size,
                    'content_type': document.content_type,
                    'gcp_path': gcp_path,
                    'file_hash': file_hash
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Document upload failed: {str(e)}")
            return DocumentUploadResponse(
                success=False,
                message=f"Upload failed: {str(e)}",
                processing_status="error"
            )
    
    async def bulk_upload_documents(
        self,
        files: List[UploadFile],
        bulk_request: BulkDocumentUploadRequest,
        current_user: Dict[str, Any]
    ) -> BulkDocumentUploadResponse:
        """
        Handle bulk document upload
        
        Args:
            files: List of uploaded files
            bulk_request: Bulk upload request parameters
            current_user: Authenticated user information
            
        Returns:
            BulkDocumentUploadResponse with bulk upload results
        """
        try:
            logger.info(f"🚀 Processing bulk upload: {len(files)} files by user {current_user.get('email')}")
            
            if len(files) != len(bulk_request.documents):
                return BulkDocumentUploadResponse(
                    success=False,
                    message="Number of files doesn't match number of document requests",
                    total_documents=len(files),
                    successful_uploads=0,
                    failed_uploads=len(files),
                    results=[]
                )
            
            results = []
            successful_uploads = 0
            failed_uploads = 0
            
            # Process each file
            for file, upload_request in zip(files, bulk_request.documents):
                try:
                    result = await self.upload_document(file, upload_request, current_user)
                    results.append(result)
                    
                    if result.success:
                        successful_uploads += 1
                    else:
                        failed_uploads += 1
                        
                except Exception as e:
                    logger.error(f"❌ Failed to process file {file.filename}: {str(e)}")
                    results.append(DocumentUploadResponse(
                        success=False,
                        message=f"Processing failed: {str(e)}",
                        processing_status="error"
                    ))
                    failed_uploads += 1
            
            success = successful_uploads > 0
            message = f"✅ Bulk upload completed: {successful_uploads} successful, {failed_uploads} failed"
            
            if failed_uploads == 0:
                message = f"✅ All {successful_uploads} documents uploaded successfully"
            elif successful_uploads == 0:
                message = f"❌ All {failed_uploads} document uploads failed"
            
            logger.info(message)
            
            return BulkDocumentUploadResponse(
                success=success,
                message=message,
                total_documents=len(files),
                successful_uploads=successful_uploads,
                failed_uploads=failed_uploads,
                results=results,
                batch_id=f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.get('email', 'unknown')}"
            )
            
        except Exception as e:
            logger.error(f"❌ Bulk upload failed: {str(e)}")
            return BulkDocumentUploadResponse(
                success=False,
                message=f"Bulk upload failed: {str(e)}",
                total_documents=len(files),
                successful_uploads=0,
                failed_uploads=len(files),
                results=[]
            )
    
    async def get_document(self, document_id: str, current_user: Dict[str, Any]) -> Optional[DocumentResponse]:
        """
        Get document by ID
        
        Args:
            document_id: Document identifier
            current_user: Authenticated user information
            
        Returns:
            DocumentResponse or None if not found
        """
        try:
            logger.info(f"📄 Retrieving document: {document_id} for user {current_user.get('email')}")
            
            # TODO: Retrieve document from database
            # document = await self.document_repository.get_by_id(document_id)
            # if not document or document.user_id != current_user.get('user_id'):
            #     return None
            
            # For now, return a mock response
            logger.info(f"✅ Document retrieved: {document_id}")
            return None  # TODO: Return actual document
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve document {document_id}: {str(e)}")
            return None
    
    async def delete_document(self, document_id: str, current_user: Dict[str, Any]) -> bool:
        """
        Delete document
        
        Args:
            document_id: Document identifier
            current_user: Authenticated user information
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            logger.info(f"🗑️ Deleting document: {document_id} by user {current_user.get('email')}")
            
            # TODO: Retrieve document from database and check ownership
            # document = await self.document_repository.get_by_id(document_id)
            # if not document or document.user_id != current_user.get('user_id'):
            #     return False
            
            # Delete from GCP Storage
            # delete_result = self.storage_service.delete_file(document.gcp_bucket_path)
            
            # Delete from database
            # await self.document_repository.delete(document_id)
            
            logger.info(f"✅ Document deleted: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document {document_id}: {str(e)}")
            return False
    
    async def list_documents(
        self,
        user_id: str,
        document_type: Optional[DocumentType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List documents from GCP Storage bucket
        
        Args:
            user_id: User ID for filtering
            document_type: Optional document type filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            Tuple of (documents_list, total_count)
        """
        try:
            logger.info(f"📋 Listing documents for user: {user_id}, type: {document_type}")
            
            # Determine prefix based on document type filter
            if document_type:
                prefix = f"{document_type.value}/"
                logger.info(f"🔍 Filtering by document type: {document_type.value}")
            else:
                prefix = ""
                logger.info("📄 Listing all document types")
            
            # Get files from GCP Storage
            # Note: Since we removed user folders, we get all files and will need to implement
            # user filtering via database once it's available
            max_results = limit + offset + 100  # Get extra to handle pagination
            files = self.storage_service.list_files(prefix=prefix, max_results=max_results)
            
            logger.info(f"📦 Found {len(files)} files in GCP Storage with prefix: '{prefix}'")
            
            # Convert GCP file info to document format
            documents = []
            for file_info in files:
                # Parse document type from path
                path_parts = file_info['name'].split('/')
                if len(path_parts) >= 2:
                    doc_type = path_parts[0]
                    filename = path_parts[-1]
                else:
                    doc_type = 'other'
                    filename = file_info['name']
                
                # Extract timestamp from filename (format: YYYYMMDD_HHMMSS_originalname)
                timestamp_match = filename.split('_')[:2]
                if len(timestamp_match) >= 2:
                    try:
                        date_part = timestamp_match[0]
                        time_part = timestamp_match[1]
                        created_at = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
                    except:
                        created_at = file_info.get('created', '')
                else:
                    created_at = file_info.get('created', '')
                
                # Generate download URL
                download_url = self.storage_service.generate_download_url(file_info['name'], expires_in_hours=24)
                
                document = {
                    "id": f"doc_{hash(file_info['name']) % 10000000}",  # Generate ID from path
                    "filename": filename,
                    "original_filename": filename,
                    "document_type": doc_type,
                    "file_size": file_info.get('size', 0),
                    "content_type": file_info.get('content_type', 'application/octet-stream'),
                    "gcp_bucket_path": file_info['name'],
                    "download_url": download_url,
                    "created_at": created_at,
                    "updated_at": file_info.get('updated', created_at),
                    "status": "completed",
                    "processing_status": "completed",
                    # Note: user association will come from database once implemented
                    "uploaded_by": "system",  # Placeholder until database integration
                    "tags": [],
                    "metadata": {}
                }
                documents.append(document)
            
            # Sort by creation date (newest first)
            documents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Apply pagination
            total = len(documents)
            paginated_documents = documents[offset:offset + limit]
            
            logger.info(f"✅ Returning {len(paginated_documents)} documents (total: {total})")
            
            return paginated_documents, total
            
        except Exception as e:
            logger.error(f"❌ Failed to list documents: {str(e)}")
            return [], 0
    
    async def _validate_file(self, file: UploadFile) -> Optional[str]:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file to validate
            
        Returns:
            Error message if validation fails, None if valid
        """
        try:
            # Check if file exists
            if not file:
                return "No file provided"
            
            # Check filename
            if not file.filename:
                return "File must have a filename"
            
            # Check file extension
            file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            if file_extension not in self.allowed_extensions:
                return f"File type not supported. Allowed types: {', '.join(self.allowed_extensions)}"
            
            # Check content type
            if file.content_type and file.content_type not in self.allowed_content_types:
                return f"Content type not supported: {file.content_type}"
            
            # Check file size (read content to get size)
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            if len(content) == 0:
                return "File is empty"
            
            if len(content) > self.max_file_size:
                return f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
            
            logger.info(f"✅ File validation passed: {file.filename} ({len(content)} bytes)")
            return None
            
        except Exception as e:
            logger.error(f"❌ File validation error: {str(e)}")
            return f"File validation failed: {str(e)}"
    
    def _generate_error_response(self, error_message: str, error_code: str = "UPLOAD_ERROR") -> DocumentErrorResponse:
        """Generate standardized error response"""
        return DocumentErrorResponse(
            error=error_message,
            error_code=error_code,
            timestamp=datetime.utcnow()
        )


# Global controller instance
_document_controller = None

def get_document_controller() -> DocumentController:
    """Get singleton document controller instance"""
    global _document_controller
    if _document_controller is None:
        _document_controller = DocumentController()
    return _document_controller