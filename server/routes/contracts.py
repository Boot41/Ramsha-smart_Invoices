from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Dict, Any
import logging
from services.contract_processor import get_contract_processor
from services.contract_rag_service import get_contract_rag_service
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
        result = contract_processor.process_contract(
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
        processing_result = contract_processor.process_contract(
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