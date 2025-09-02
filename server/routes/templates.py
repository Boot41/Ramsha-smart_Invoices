from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from services.template_service import TemplateService
from services.pdf_service import PDFService
from utils.html_sanitizer import HTMLSanitizer, TemplateValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Request/Response Models
class PreviewRequest(BaseModel):
    templateId: str
    invoiceData: Dict[str, Any]
    invoiceNumber: Optional[str] = None
    invoiceDate: Optional[str] = None
    dueDate: Optional[str] = None
    status: str = "Draft"

class PDFGenerationRequest(BaseModel):
    templateId: str
    invoiceData: Dict[str, Any]
    invoiceNumber: str
    invoiceDate: str
    dueDate: str
    status: str = "Pending"

class BulkPDFRequest(BaseModel):
    invoices: List[Dict[str, Any]]

class TemplateValidationResponse(BaseModel):
    valid: bool
    safe: bool
    structure_errors: List[str]
    missing_placeholders: List[str]
    found_placeholders: List[str]
    warnings: List[str]

class TemplateListResponse(BaseModel):
    templates: List[Dict[str, Any]]
    total: int

# Initialize services
template_service = TemplateService()

# Initialize PDF service with error handling
try:
    pdf_service = PDFService()
    PDF_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PDF service not available: {str(e)}")
    pdf_service = None
    PDF_AVAILABLE = False

@router.post("/preview")
async def generate_preview(request: PreviewRequest):
    """Generate HTML preview of invoice template with data"""
    try:
        # Parse dates
        invoice_date = None
        due_date = None
        
        if request.invoiceDate:
            invoice_date = datetime.fromisoformat(request.invoiceDate.replace('Z', '+00:00'))
        
        if request.dueDate:
            due_date = datetime.fromisoformat(request.dueDate.replace('Z', '+00:00'))
        
        # Generate preview
        rendered_html = await template_service.render_invoice_preview(
            template_id=request.templateId,
            invoice_data=request.invoiceData,
            invoice_number=request.invoiceNumber,
            invoice_date=invoice_date,
            due_date=due_date,
            status=request.status
        )
        
        return {
            "html": rendered_html,
            "templateId": request.templateId,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")

@router.post("/generate-pdf")
async def generate_pdf(request: PDFGenerationRequest):
    """Generate PDF from invoice template and data"""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generation service is not available")
    
    try:
        # Parse dates
        invoice_date = datetime.fromisoformat(request.invoiceDate.replace('Z', '+00:00'))
        due_date = datetime.fromisoformat(request.dueDate.replace('Z', '+00:00'))
        
        # Generate PDF
        pdf_content = await pdf_service.generate_invoice_pdf(
            template_id=request.templateId,
            invoice_data=request.invoiceData,
            invoice_number=request.invoiceNumber,
            invoice_date=invoice_date,
            due_date=due_date,
            status=request.status
        )
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice-{request.invoiceNumber}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@router.post("/generate-bulk-pdf")
async def generate_bulk_pdf(request: BulkPDFRequest):
    """Generate bulk PDF containing multiple invoices"""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generation service is not available")
    
    try:
        # Process invoice data
        processed_invoices = []
        for invoice in request.invoices:
            processed_invoices.append({
                'template_id': invoice['templateId'],
                'data': invoice['invoiceData'],
                'invoice_number': invoice['invoiceNumber'],
                'invoice_date': datetime.fromisoformat(invoice['invoiceDate'].replace('Z', '+00:00')),
                'due_date': datetime.fromisoformat(invoice['dueDate'].replace('Z', '+00:00')),
                'status': invoice.get('status', 'Pending')
            })
        
        # Generate bulk PDF
        pdf_content = await pdf_service.generate_bulk_invoices_pdf(processed_invoices)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoices-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating bulk PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate bulk PDF: {str(e)}")

@router.get("/", response_model=TemplateListResponse)
async def list_templates():
    """List all available invoice templates"""
    try:
        templates = await template_service.list_available_templates()
        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list templates")

@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get template details and content"""
    try:
        template_content = await template_service.get_template_by_id(template_id)
        
        if not template_content:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "templateId": template_id,
            "content": template_content,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@router.post("/{template_id}/validate", response_model=TemplateValidationResponse)
async def validate_template(template_id: str):
    """Validate template for security and structure"""
    try:
        template_content = await template_service.get_template_by_id(template_id)
        
        if not template_content:
            raise HTTPException(status_code=404, detail="Template not found")
        
        validation_result = await template_service.validate_template(template_content)
        
        return TemplateValidationResponse(**validation_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate template: {str(e)}")

@router.post("/{template_id}/preview-pdf")
async def generate_preview_pdf(template_id: str):
    """Generate a preview PDF with sample data"""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generation service is not available")
    
    try:
        pdf_content = await pdf_service.generate_preview_pdf(template_id)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=preview-{template_id}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating preview PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview PDF: {str(e)}")

@router.post("/validate-html")
async def validate_html_content(request: Dict[str, str]):
    """Validate HTML content for template safety"""
    try:
        html_content = request.get('html', '')
        
        if not html_content:
            raise HTTPException(status_code=400, detail="HTML content is required")
        
        # Validate structure
        structure_validation = TemplateValidator.validate_template_structure(html_content)
        
        # Validate safety
        is_safe = TemplateValidator.is_template_safe(html_content)
        
        # Validate PDF compatibility
        if PDF_AVAILABLE:
            pdf_validation = pdf_service.validate_pdf_generation(html_content)
        else:
            pdf_validation = {
                'valid': True,
                'issues': ['PDF service not available'],
                'warnings': ['PDF generation is disabled'],
                'pdf_ready': False
            }
        
        return {
            "valid": is_safe and len(structure_validation) == 0 and pdf_validation['valid'],
            "safe": is_safe,
            "structure_errors": structure_validation,
            "pdf_ready": pdf_validation['pdf_ready'],
            "pdf_issues": pdf_validation['issues'],
            "pdf_warnings": pdf_validation['warnings'],
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error validating HTML content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate HTML: {str(e)}")

@router.get("/{template_id}/sample-data")
async def get_sample_data(template_id: str):
    """Get sample invoice data for template preview"""
    try:
        sample_data = await template_service.create_sample_invoice_data(template_id)
        
        return {
            "templateId": template_id,
            "sampleData": sample_data,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sample data: {str(e)}")