from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import List, Optional
from services.database_service import get_database_service
from models.database_models import InvoiceStatus

router = APIRouter(prefix="/invoices", tags=["invoice management"])

# Real Database Endpoints for Viewing Invoice Data

@router.get("/database/list")
async def list_database_invoices(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of invoices to return"),
    offset: int = Query(0, description="Number of invoices to skip")
):
    """Get all invoices from database with optional filtering"""
    try:
        db_service = get_database_service()
        
        # Convert string status to enum if provided
        status_filter = None
        if status:
            try:
                status_filter = InvoiceStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        invoices, total = await db_service.list_invoices(
            status=status_filter,
            limit=limit,
            offset=offset
        )
        
        # Convert to dict for JSON serialization
        invoice_list = []
        for invoice in invoices:
            invoice_dict = {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "workflow_id": invoice.workflow_id,
                "client_name": invoice.client_name,
                "client_email": invoice.client_email,
                "service_provider_name": invoice.service_provider_name,
                "total_amount": invoice.total_amount,
                "currency": invoice.currency,
                "status": invoice.status.value,
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "contract_title": invoice.contract_title,
                "generated_by_agent": invoice.generated_by_agent,
                "confidence_score": invoice.confidence_score,
                "quality_score": invoice.quality_score,
                "human_reviewed": invoice.human_reviewed,
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None
            }
            invoice_list.append(invoice_dict)
        
        return {
            "invoices": invoice_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching invoices: {str(e)}")

@router.get("/database/{invoice_id}")
async def get_database_invoice(invoice_id: str):
    """Get a specific invoice by ID with full data"""
    try:
        db_service = get_database_service()
        invoice = await db_service.get_invoice_by_id(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "workflow_id": invoice.workflow_id,
            "user_id": invoice.user_id,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "status": invoice.status.value,
            
            # Client information
            "client_name": invoice.client_name,
            "client_email": invoice.client_email,
            "client_address": invoice.client_address,
            "client_phone": invoice.client_phone,
            
            # Service provider information
            "service_provider_name": invoice.service_provider_name,
            "service_provider_email": invoice.service_provider_email,
            "service_provider_address": invoice.service_provider_address,
            "service_provider_phone": invoice.service_provider_phone,
            
            # Financial information
            "subtotal": invoice.subtotal,
            "tax_amount": invoice.tax_amount,
            "total_amount": invoice.total_amount,
            "currency": invoice.currency,
            
            # Contract details
            "contract_title": invoice.contract_title,
            "contract_type": invoice.contract_type,
            "contract_reference": invoice.contract_reference,
            
            # Complete invoice data (JSON)
            "invoice_data": invoice.invoice_data,
            
            # AI generation metadata
            "generated_by_agent": invoice.generated_by_agent,
            "confidence_score": invoice.confidence_score,
            "quality_score": invoice.quality_score,
            "human_reviewed": invoice.human_reviewed,
            
            # Timestamps
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
            "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching invoice: {str(e)}")

@router.get("/database/workflow/{workflow_id}")
async def get_invoice_by_workflow(workflow_id: str):
    """Get invoice by workflow ID"""
    try:
        db_service = get_database_service()
        invoice = await db_service.get_invoice_by_workflow_id(workflow_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found for this workflow")
        
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "workflow_id": invoice.workflow_id,
            "client_name": invoice.client_name,
            "service_provider_name": invoice.service_provider_name,
            "total_amount": invoice.total_amount,
            "status": invoice.status.value,
            "contract_title": invoice.contract_title,
            "invoice_data": invoice.invoice_data,  # Full JSON data
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching invoice: {str(e)}")

@router.get("/database/templates")
async def list_invoice_templates(
    invoice_id: Optional[str] = Query(None, description="Filter by invoice ID"),
    limit: int = Query(50, description="Number of templates to return"),
    offset: int = Query(0, description="Number of templates to skip")
):
    """Get all invoice templates from database"""
    try:
        db_service = get_database_service()
        templates, total = await db_service.list_invoice_templates(
            invoice_id=invoice_id,
            is_active=True,
            limit=limit,
            offset=offset
        )
        
        template_list = []
        for template in templates:
            template_dict = {
                "id": template.id,
                "invoice_id": template.invoice_id,
                "template_name": template.template_name,
                "component_name": template.component_name,
                "template_type": template.template_type,
                "file_path": template.file_path,
                "generated_by": template.generated_by,
                "model_used": template.model_used,
                "is_active": template.is_active,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None
            }
            template_list.append(template_dict)
        
        return {
            "templates": template_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@router.get("/{invoice_id}/adaptive-ui-designs")
async def get_adaptive_ui_designs(invoice_id: str):
    """Get adaptive UI designs for a specific invoice"""
    try:
        db_service = get_database_service()
        invoice = await db_service.get_invoice_by_id(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Extract adaptive UI designs from invoice_data
        invoice_data = invoice.invoice_data or {}
        adaptive_designs = invoice_data.get('adaptive_ui_designs', {})
        
        if not adaptive_designs:
            # Return empty designs structure if none found
            return {
                "invoice_id": invoice_id,
                "designs": [],
                "message": "No adaptive UI designs found for this invoice"
            }
        
        # Return the designs with invoice metadata
        return {
            "invoice_id": invoice_id,
            "invoice_number": invoice.invoice_number,
            "workflow_id": invoice.workflow_id,
            "client_name": invoice.client_name,
            "service_provider_name": invoice.service_provider_name,
            "designs": adaptive_designs.get("designs", []),
            "generated_at": adaptive_designs.get("generated_at"),
            "total_designs": len(adaptive_designs.get("designs", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching adaptive UI designs: {str(e)}")

@router.get("/{invoice_id}/html-invoices")
async def get_html_invoices(invoice_id: str):
    """Get generated HTML invoices for a specific invoice"""
    try:
        db_service = get_database_service()
        invoice = await db_service.get_invoice_by_id(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Extract HTML invoices from invoice_data
        invoice_data = invoice.invoice_data or {}
        html_invoices = invoice_data.get('html_invoices', [])
        
        if not html_invoices:
            # Return empty structure if none found
            return {
                "invoice_id": invoice_id,
                "html_invoices": [],
                "message": "No HTML invoices found for this invoice. The invoice may not have been processed by the design agent yet."
            }
        
        # Return the HTML invoices with invoice metadata
        return {
            "invoice_id": invoice_id,
            "invoice_number": invoice.invoice_number,
            "workflow_id": invoice.workflow_id,
            "client_name": invoice.client_name,
            "service_provider_name": invoice.service_provider_name,
            "html_invoices": html_invoices,
            "total_designs": len(html_invoices)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching HTML invoices: {str(e)}")

@router.get("/{invoice_id}/html-invoices/{design_id}")
async def get_html_invoice_by_design(invoice_id: str, design_id: str):
    """Get a specific HTML invoice design for rendering"""
    try:
        db_service = get_database_service()
        invoice = await db_service.get_invoice_by_id(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Extract HTML invoices from invoice_data
        invoice_data = invoice.invoice_data or {}
        html_invoices = invoice_data.get('html_invoices', [])
        
        # Find the specific design
        target_invoice = None
        for html_invoice in html_invoices:
            if html_invoice.get("design_id") == design_id:
                target_invoice = html_invoice
                break
        
        if not target_invoice:
            raise HTTPException(
                status_code=404, 
                detail=f"HTML invoice with design_id '{design_id}' not found"
            )
        
        return {
            "invoice_id": invoice_id,
            "design_id": design_id,
            "design_name": target_invoice.get("design_name"),
            "html_content": target_invoice.get("html_content"),
            "generated_at": target_invoice.get("generated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching HTML invoice: {str(e)}")

@router.get("/{invoice_id}/preview/{design_id}", response_class=HTMLResponse)
async def preview_html_invoice(invoice_id: str, design_id: str):
    """Preview a specific HTML invoice design directly in the browser"""
    try:
        db_service = get_database_service()
        invoice = await db_service.get_invoice_by_id(invoice_id)
        
        if not invoice:
            return HTMLResponse(
                content="<html><body><h1>Invoice Not Found</h1><p>The requested invoice could not be found.</p></body></html>",
                status_code=404
            )
        
        # Extract HTML invoices from invoice_data
        invoice_data = invoice.invoice_data or {}
        html_invoices = invoice_data.get('html_invoices', [])
        
        # Find the specific design
        target_invoice = None
        for html_invoice in html_invoices:
            if html_invoice.get("design_id") == design_id:
                target_invoice = html_invoice
                break
        
        if not target_invoice:
            return HTMLResponse(
                content=f"<html><body><h1>Design Not Found</h1><p>HTML invoice with design_id '{design_id}' not found.</p></body></html>",
                status_code=404
            )
        
        # Return the HTML content directly for browser rendering
        return HTMLResponse(content=target_invoice.get("html_content", ""))
        
    except Exception as e:
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>Error fetching HTML invoice: {str(e)}</p></body></html>",
            status_code=500
        )

# Mock Endpoints (existing)

@router.post("/create_invoice")
async def create_invoice():
    # Mock invoice creation
    return {
        "message": "Invoice created successfully", 
        "invoice_id": "inv_123", 
        "status": "draft"
    }

@router.post("/approve_invoice")
async def approve_invoice():
    # Mock invoice approval
    return {
        "message": "Invoice approved successfully", 
        "invoice_id": "inv_123", 
        "status": "approved"
    }

@router.post("/multi-invoice")
async def multi_invoice():
    # Mock multiple invoice processing
    return {"message": "Multiple invoices processed", "processed_count": 5}

@router.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    # Mock invoice upload
    return {
        "message": "Invoice uploaded successfully", 
        "invoice_id": "inv_456", 
        "filename": file.filename
    }

@router.get("/get-all-invoices")
async def get_all_invoices():
    # Mock get all invoices
    return {"invoices": [
        {
            "id": "inv_1", 
            "number": "INV-001", 
            "amount": 1000, 
            "status": "pending", 
            "due_date": "2024-02-01"
        },
        {
            "id": "inv_2", 
            "number": "INV-002", 
            "amount": 1500, 
            "status": "approved", 
            "due_date": "2024-02-15"
        }
    ]}

@router.get("/initial-invoice/{file_name}")
async def get_initial_invoice(file_name: str):
    # Mock get initial invoice
    return {
        "file_name": file_name, 
        "data": {"amount": 1000, "client": "Sample Client"}
    }

@router.post("/invoice-preview")
async def invoice_preview():
    # Mock invoice preview
    return {
        "preview": {
            "html": "<div>Invoice Preview</div>", 
            "pdf_url": "/static/preview.pdf"
        }
    }

@router.post("/invoice-approval")
async def invoice_approval():
    # Mock invoice approval workflow
    return {"message": "Invoice sent for approval", "approval_id": "app_123"}

@router.post("/validate-invoice")
async def validate_invoice():
    # Mock invoice validation
    return {"valid": True, "errors": [], "warnings": []}

@router.post("/schedule-invoice")
async def schedule_invoice():
    # Mock invoice scheduling
    return {
        "message": "Invoice scheduled successfully", 
        "schedule_id": "sch_123", 
        "send_date": "2024-02-01"
    }

@router.get("/schedules")
async def get_schedules():
    # Mock get all schedules
    return {"schedules": [
        {
            "id": "sch_1", 
            "invoice_id": "inv_1", 
            "send_date": "2024-02-01", 
            "status": "scheduled"
        },
        {
            "id": "sch_2", 
            "invoice_id": "inv_2", 
            "send_date": "2024-02-15", 
            "status": "sent"
        }
    ]}

@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    # Mock get specific schedule
    return {
        "schedule_id": schedule_id, 
        "invoice_id": "inv_1", 
        "send_date": "2024-02-01", 
        "status": "scheduled"
    }