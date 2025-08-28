from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

from schemas.document_schemas import (
    DocumentUploadRequest, DocumentUploadResponse, DocumentProcessingResponse,
    DocumentResponse, DocumentErrorResponse, DocumentType, UploadSource,
    BulkDocumentUploadRequest, BulkDocumentUploadResponse
)
from controller.document_controller import get_document_controller
from middleware.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Document Management"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    filename: str = Form(...),
    document_type: DocumentType = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form("[]"),  # JSON string of tags
    source: UploadSource = Form(UploadSource.WEB_UPLOAD),
    metadata: Optional[str] = Form("{}"),  # JSON string of metadata
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Upload a single document
    
    - **file**: Document file to upload
    - **filename**: Name for the document
    - **document_type**: Type of document (contract, invoice, etc.)
    - **description**: Optional description
    - **tags**: JSON array of tags (e.g., ["tag1", "tag2"])
    - **source**: Upload source (web_upload, email, drive)
    - **metadata**: JSON object with additional metadata
    """
    try:
        logger.info(f"📄 Document upload request from user: {current_user.get('email')}")
        
        # Parse JSON fields
        try:
            tags_list = json.loads(tags) if tags else []
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format in tags or metadata: {str(e)}"
            )
        
        # Create upload request
        upload_request = DocumentUploadRequest(
            filename=filename,
            document_type=document_type,
            description=description,
            tags=tags_list,
            source=source,
            metadata=metadata_dict
        )
        
        # Get controller and process upload
        controller = get_document_controller()
        result = await controller.upload_document(file, upload_request, current_user)
        
        if result.success:
            logger.info(f"✅ Document upload successful: {result.document_id}")
        else:
            logger.error(f"❌ Document upload failed: {result.message}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.post("/upload/bulk", response_model=BulkDocumentUploadResponse)
async def bulk_upload_documents(
    files: List[UploadFile] = File(...),
    documents_json: str = Form(...),  # JSON string of document requests
    batch_metadata: Optional[str] = Form("{}"),
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Upload multiple documents in bulk
    
    - **files**: List of document files to upload
    - **documents_json**: JSON array of DocumentUploadRequest objects
    - **batch_metadata**: Optional batch metadata as JSON object
    """
    try:
        logger.info(f"📄 Bulk document upload request: {len(files)} files from user: {current_user.get('email')}")
        
        # Parse JSON fields
        try:
            documents_data = json.loads(documents_json)
            batch_metadata_dict = json.loads(batch_metadata) if batch_metadata else {}
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )
        
        # Create document upload requests
        document_requests = []
        for doc_data in documents_data:
            document_requests.append(DocumentUploadRequest(**doc_data))
        
        # Create bulk request
        bulk_request = BulkDocumentUploadRequest(
            documents=document_requests,
            batch_metadata=batch_metadata_dict
        )
        
        # Get controller and process bulk upload
        controller = get_document_controller()
        result = await controller.bulk_upload_documents(files, bulk_request, current_user)
        
        logger.info(f"✅ Bulk upload completed: {result.successful_uploads}/{result.total_documents} successful")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bulk document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk document upload failed: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get document by ID
    
    - **document_id**: Unique document identifier
    """
    try:
        logger.info(f"📄 Get document request: {document_id} from user: {current_user.get('email')}")
        
        controller = get_document_controller()
        document = await controller.get_document(document_id, current_user)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        logger.info(f"✅ Document retrieved: {document_id}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get document error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Delete document by ID
    
    - **document_id**: Unique document identifier
    """
    try:
        logger.info(f"🗑️ Delete document request: {document_id} from user: {current_user.get('email')}")
        
        controller = get_document_controller()
        success = await controller.delete_document(document_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found or access denied: {document_id}"
            )
        
        logger.info(f"✅ Document deleted: {document_id}")
        return {
            "success": True,
            "message": f"Document deleted successfully: {document_id}",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete document error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/")
async def list_documents(
    document_type: Optional[DocumentType] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    List user documents with optional filtering
    
    - **document_type**: Filter by document type (optional)
    - **limit**: Maximum number of documents to return (default 50)
    - **offset**: Number of documents to skip (default 0)
    """
    try:
        logger.info(f"📋 List documents request from user: {current_user.get('email')}")
        
        # Get controller and list documents
        controller = get_document_controller()
        documents, total = await controller.list_documents(
            user_id=current_user.get('user_id'),
            document_type=document_type,
            limit=limit,
            offset=offset
        )
        
        # Calculate pagination info
        has_more = (offset + limit) < total
        
        return {
            "success": True,
            "message": "Documents retrieved successfully",
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": has_more
        }
        
    except Exception as e:
        logger.error(f"❌ List documents error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.post("/{document_id}/process", response_model=DocumentProcessingResponse)
async def process_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Trigger document processing (OCR, parsing, etc.)
    
    - **document_id**: Unique document identifier
    - **processing_options**: Optional processing configuration
    """
    try:
        logger.info(f"⚙️ Process document request: {document_id} from user: {current_user.get('email')}")
        
        # TODO: Implement document processing
        # For now, return mock response
        return DocumentProcessingResponse(
            success=True,
            message="Document processing initiated successfully",
            document_id=document_id,
            processing_status="processing",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ Process document error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


# Legacy endpoints for backward compatibility
@router.post("/upload-contract")
async def upload_pdf_legacy(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """Legacy endpoint for contract upload (deprecated)"""
    logger.warning("⚠️ Legacy endpoint /upload-contract called, please use /upload instead")
    
    upload_request = DocumentUploadRequest(
        filename=file.filename or "contract.pdf",
        document_type=DocumentType.CONTRACT,
        description="Uploaded via legacy endpoint",
        source=UploadSource.WEB_UPLOAD
    )
    
    controller = get_document_controller()
    result = await controller.upload_document(file, upload_request, current_user)
    
    # Return legacy format
    return {
        "message": "PDF uploaded successfully" if result.success else "Upload failed",
        "file_id": result.document_id,
        "filename": file.filename,
        "success": result.success
    }