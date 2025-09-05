"""
Natural Language Validation Routes

API endpoints for testing and using natural language query processing
for invoice field correction instead of structured forms.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from services.natural_language_correction_service import get_natural_language_correction_service
from schemas.unified_invoice_schemas import UnifiedInvoiceData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/natural-language", tags=["natural language validation"])


class NaturalLanguageQueryRequest(BaseModel):
    """Request model for natural language query processing"""
    query: str
    missing_fields: Optional[List[str]] = ["client.name", "service_provider.name", "payment_terms.amount"]
    current_invoice_data: Optional[Dict[str, Any]] = None


class NaturalLanguageQueryResponse(BaseModel):
    """Response model for natural language query processing"""
    success: bool
    query: str
    extracted_fields: Dict[str, Any]
    confidence: float
    message: str


@router.post("/extract-fields", response_model=NaturalLanguageQueryResponse)
async def extract_fields_from_query(request: NaturalLanguageQueryRequest):
    """
    Extract invoice fields from natural language query
    
    Example queries:
    - "The client is John Smith and the service provider is TechCorp. The monthly fee is $1500 for web development."
    - "Client: Ramsha, Provider: Iqbal, Amount: $2000, Service: Software development services"
    - "Invoice for Sarah Johnson from ABC Consulting for $800 monthly consulting services"
    """
    try:
        nl_service = get_natural_language_correction_service()
        
        # Create minimal invoice data if not provided
        if request.current_invoice_data:
            current_data = UnifiedInvoiceData(**request.current_invoice_data)
        else:
            current_data = UnifiedInvoiceData(
                client=None,
                service_provider=None,
                payment_terms=None,
                service_details=None,
                contract_details=None,
                metadata={"version": "1.0"}
            )
        
        # Process the natural language query
        result = await nl_service.process_natural_language_query(
            query=request.query,
            current_invoice_data=current_data,
            missing_fields=request.missing_fields,
            validation_issues=[]
        )
        
        return NaturalLanguageQueryResponse(
            success=result.get("success", False),
            query=request.query,
            extracted_fields=result.get("corrections", {}),
            confidence=result.get("extraction_confidence", 0.0),
            message=f"Extracted {len(result.get('corrections', {}))} fields" if result.get("success") else result.get("error", "Extraction failed")
        )
        
    except Exception as e:
        logger.error(f"❌ Natural language extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Natural language processing failed: {str(e)}")


@router.post("/preview", response_model=NaturalLanguageQueryResponse)
async def preview_extraction(request: NaturalLanguageQueryRequest):
    """
    Preview what would be extracted from a natural language query without applying changes
    """
    try:
        nl_service = get_natural_language_correction_service()
        
        # Create minimal invoice data
        current_data = UnifiedInvoiceData(
            client=None,
            service_provider=None, 
            payment_terms=None,
            service_details=None,
            contract_details=None,
            metadata={"version": "1.0"}
        )
        
        # Preview extraction
        result = await nl_service.preview_corrections(request.query, current_data)
        
        return NaturalLanguageQueryResponse(
            success=result.get("success", False),
            query=request.query,
            extracted_fields=result.get("extracted_fields", {}),
            confidence=result.get("confidence", 0.0),
            message=f"Preview: Would extract {len(result.get('extracted_fields', {}))} fields"
        )
        
    except Exception as e:
        logger.error(f"❌ Natural language preview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/examples")
async def get_query_examples():
    """Get examples of natural language queries that work well"""
    
    examples = [
        {
            "category": "Complete Information",
            "query": "The client is John Smith from john@email.com and the service provider is TechCorp LLC. The monthly fee is $1500 for web development services starting January 2025.",
            "extracts": ["client.name", "client.email", "service_provider.name", "payment_terms.amount", "payment_terms.frequency", "service_details.description"]
        },
        {
            "category": "Basic Information",
            "query": "Client: Sarah Johnson, Provider: ABC Consulting, Amount: $800, Service: Monthly consulting",
            "extracts": ["client.name", "service_provider.name", "payment_terms.amount", "service_details.description"]
        },
        {
            "category": "Conversational Style",
            "query": "The invoice is for Mary Wilson and it's from Digital Solutions Inc. She pays $2000 quarterly for software maintenance.",
            "extracts": ["client.name", "service_provider.name", "payment_terms.amount", "payment_terms.frequency", "service_details.description"]
        },
        {
            "category": "Minimal Information",
            "query": "Client is Ramsha, provider is Iqbal, amount is $1200",
            "extracts": ["client.name", "service_provider.name", "payment_terms.amount"]
        },
        {
            "category": "With Contact Details",
            "query": "Invoice for David Brown (david@company.com, 555-1234) from WebDev Pro LLC (contact@webdevpro.com) for $950 monthly website maintenance services",
            "extracts": ["client.name", "client.email", "client.phone", "service_provider.name", "service_provider.email", "payment_terms.amount", "payment_terms.frequency", "service_details.description"]
        }
    ]
    
    return {
        "examples": examples,
        "tips": [
            "Be specific about names and amounts",
            "Use clear indicators like 'client is', 'provider is', 'amount is'",
            "Include frequency words like 'monthly', 'quarterly', 'annually'",
            "Describe the service being provided",
            "Include contact information when available"
        ],
        "supported_fields": [
            "client.name",
            "client.email", 
            "client.address",
            "client.phone",
            "service_provider.name",
            "service_provider.email",
            "service_provider.address",
            "payment_terms.amount",
            "payment_terms.currency",
            "payment_terms.frequency",
            "service_details.description",
            "service_details.start_date",
            "service_details.end_date"
        ]
    }