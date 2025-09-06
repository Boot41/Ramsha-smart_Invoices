from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Dict, Any
import logging
from services.contract_processor import get_contract_processor
from services.contract_rag_service import get_contract_rag_service
from services.contract_db_service import get_contract_db_service
from schemas.contract_schemas import (
    ContractProcessRequest,
    ContractProcessResponse,
    InvoiceGenerationRequest,
    InvoiceGenerationResponse,
    ContractQueryRequest,
    ContractQueryResponse
)
from middleware.auth import get_current_user
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/contracts",
    tags=["contracts"]
)


@router.post("/upload-and-process", response_model=ContractProcessResponse)
async def upload_and_process_contract(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    current_user = Depends(get_current_user)
):
    """
    Upload and process a contract PDF file
    - Extracts text from PDF
    - Chunks the text
    - Generates embeddings
    - Stores in vector database
    """
    try:
        logger.info(f"🚀 Processing contract upload for user: {user_id}")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="File is empty or corrupted"
            )
        
        # Process contract
        contract_processor = get_contract_processor()
        result = await contract_processor.process_contract(
            pdf_file=file_content,
            user_id=user_id,
            contract_name=file.filename
        )
        
        # Convert to response model
        response = ContractProcessResponse(**result)
        
        logger.info(f"✅ Contract processing completed successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Contract processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Contract processing failed: {str(e)}"
        )


@router.post("/generate-invoice-data", response_model=InvoiceGenerationResponse)
async def generate_invoice_data(
    request: InvoiceGenerationRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate structured invoice data from a processed contract using RAG
    """
    try:
        logger.info(f"🚀 Generating invoice data for contract: {request.contract_name}")
        
        # Generate invoice data using RAG
        contract_rag_service = get_contract_rag_service()
        result = contract_rag_service.generate_invoice_data(
            user_id=request.user_id,
            contract_name=request.contract_name,
            query=request.query
        )
        
        logger.info(f"✅ Invoice data generation completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Invoice data generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Invoice data generation failed: {str(e)}"
        )


@router.post("/query", response_model=ContractQueryResponse)
async def query_contract(
    request: ContractQueryRequest,
    current_user = Depends(get_current_user)
):
    """
    Query a processed contract for specific information using RAG
    """
    try:
        logger.info(f"🚀 Processing contract query: {request.query}")
        
        # Query contract using RAG
        contract_rag_service = get_contract_rag_service()
        response = contract_rag_service.query_contract(
            user_id=request.user_id,
            contract_name=request.contract_name,
            query=request.query
        )
        
        result = ContractQueryResponse(
            status="success",
            response=response,
            contract_name=request.contract_name,
            user_id=request.user_id,
            query=request.query,
            generated_at=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Contract query completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Contract query failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Contract query failed: {str(e)}"
        )


@router.post("/process-and-generate-invoice")
async def process_and_generate_invoice(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    current_user = Depends(get_current_user)
):
    """
    Complete workflow: Upload contract, process it, and generate invoice data
    """
    try:
        logger.info(f"🚀 Starting complete contract-to-invoice workflow")
        
        # Step 1: Process contract
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="File is empty or corrupted"
            )
        
        # Process contract
        contract_processor = get_contract_processor()
        processing_result = await contract_processor.process_contract(
            pdf_file=file_content,
            user_id=user_id,
            contract_name=file.filename
        )
        
        # Step 2: Generate invoice data
        contract_rag_service = get_contract_rag_service()
        invoice_result = contract_rag_service.generate_invoice_data(
            user_id=user_id,
            contract_name=file.filename,
            query="Extract comprehensive invoice data including all parties, payment terms, services, and billing schedules"
        )
        
        # Combine results
        combined_result = {
            "status": "success",
            "message": "✅ Contract processed and invoice data generated successfully",
            "contract_processing": processing_result,
            "invoice_generation": invoice_result.dict(),
            "workflow_completed_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Complete workflow completed successfully")
        return combined_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Complete workflow failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Complete workflow failed: {str(e)}"
        )


@router.get("/user/{user_id}")
async def get_user_contracts(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get all contracts for a specific user
    """
    try:
        logger.info(f"🔍 Fetching contracts for user: {user_id}")
        
        # Get contracts from database
        contract_db_service = get_contract_db_service()
        contracts = await contract_db_service.get_contracts_by_user(user_id)
        
        # Format contract data for frontend
        formatted_contracts = []
        for contract in contracts:
            formatted_contract = {
                "id": contract.id,
                "contract_id": contract.contract_id,
                "original_filename": contract.original_filename,
                "storage_path": contract.storage_path,
                "file_size": contract.file_size,
                "content_type": contract.content_type,
                "file_hash": contract.file_hash,
                "is_processed": contract.is_processed,
                "processing_completed_at": contract.processing_completed_at.isoformat() if contract.processing_completed_at else None,
                "total_chunks": contract.total_chunks,
                "total_embeddings": contract.total_embeddings,
                "text_preview": contract.text_preview,
                "created_at": contract.created_at.isoformat(),
                "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
                # Add extracted invoice data if available
                "extracted_invoice_data": None
            }
            
            # Include extracted invoice data if available
            if hasattr(contract, 'extracted_invoice_data') and contract.extracted_invoice_data:
                for extracted_data in contract.extracted_invoice_data:
                    formatted_contract["extracted_invoice_data"] = {
                        "id": extracted_data.id,
                        "invoice_frequency": (extracted_data.invoice_frequency.value if hasattr(extracted_data.invoice_frequency, 'value') else extracted_data.invoice_frequency) if extracted_data.invoice_frequency else None,
                        "first_invoice_date": extracted_data.first_invoice_date.isoformat() if extracted_data.first_invoice_date else None,
                        "next_invoice_date": extracted_data.next_invoice_date.isoformat() if extracted_data.next_invoice_date else None,
                        "payment_amount": extracted_data.payment_amount,
                        "currency": extracted_data.currency,
                        "payment_due_days": extracted_data.payment_due_days,
                        "services": extracted_data.services,
                        "confidence_score": extracted_data.confidence_score
                    }
                    break  # Take the first (most recent) extracted data
            
            formatted_contracts.append(formatted_contract)
        
        result = {
            "status": "success",
            "message": f"✅ Found {len(contracts)} contracts for user {user_id}",
            "user_id": user_id,
            "contracts": formatted_contracts,
            "total_count": len(contracts),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Returned {len(contracts)} contracts for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to get contracts for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contracts: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for contract processing service"""
    try:
        # Test contract processor
        contract_processor = get_contract_processor()
        
        # Test RAG service
        contract_rag_service = get_contract_rag_service()
        
        return {
            "status": "healthy",
            "message": "✅ Contract processing service is running",
            "services": {
                "contract_processor": "available",
                "contract_rag_service": "available",
                "embedding_service": "available"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"❌ Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }