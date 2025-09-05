from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from typing import List, Optional
from datetime import datetime, timedelta
from services.database_service import get_database_service
from models.database_models import InvoiceStatus, HTMLInvoice

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

# HTML Invoice Viewing Endpoints

@router.get("/{invoice_uuid}/view", response_class=HTMLResponse)
async def view_html_invoice(invoice_uuid: str):
    """View the generated HTML invoice"""
    try:
        db_service = get_database_service()
        
        # Get the HTML invoice from database
        # For now, we'll mock this since database service needs to be implemented
        # In a real implementation, you would:
        # html_invoice = await db_service.get_html_invoice_by_uuid(invoice_uuid)
        
        # Mock HTML invoice for now
        html_invoice = {
            "invoice_uuid": invoice_uuid,
            "invoice_number": f"INV-{invoice_uuid[:8].upper()}",
            "html_content": f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Invoice {invoice_uuid[:8].upper()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; color: #333; }}
        .invoice-container {{ max-width: 800px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.05); }}
        .header {{ text-align: left; margin-bottom: 20px; }}
        .header h1 {{ color: #0056b3; margin-bottom: 5px; }}
        .invoice-meta {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
        .addresses {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
        .address-section {{ width: 48%; }}
        .address-section h3 {{ margin-bottom: 5px; color: #0056b3; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; color: #0056b3; }}
        .totals {{ text-align: right; margin-bottom: 20px; }}
        .footer {{ text-align: center; font-size: 0.8em; color: #777; border-top: 1px solid #ddd; padding-top: 10px; }}
        .status {{ font-weight: bold; color: #007bff; }}
    </style>
</head>
<body>
    <div class="invoice-container">
        <div class="header">
            <h1>Smart Invoice Scheduler</h1>
            <p>Generated HTML Invoice</p>
        </div>
        
        <div class="invoice-meta">
            <div>
                <p>Invoice Number: INV-{invoice_uuid[:8].upper()}</p>
                <p>Invoice Date: {datetime.now().strftime("%Y-%m-%d")}</p>
                <p>Due Date: {(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")}</p>
            </div>
            <div>
                <p>Status: <span class="status">Generated</span></p>
            </div>
        </div>
        
        <div class="addresses">
            <div class="address-section">
                <h3>Bill To:</h3>
                <p>Client Name</p>
                <p>Client Address</p>
            </div>
            <div class="address-section">
                <h3>Bill From:</h3>
                <p>Service Provider</p>
                <p>Provider Address</p>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Service Rendered</td>
                    <td>$1,000.00</td>
                </tr>
            </tbody>
        </table>
        
        <div class="totals">
            <p>Total: $1,000.00</p>
        </div>
        
        <div class="footer">
            <p>Thank you for your business!</p>
            <p>Generated by Smart Invoice Scheduler - UI Generation Agent</p>
        </div>
    </div>
</body>
</html>
            """,
            "viewing_enabled": True,
            "is_active": True
        }
        
        # Check if invoice exists and is viewable
        if not html_invoice:
            raise HTTPException(status_code=404, detail="HTML invoice not found")
        
        if not html_invoice.get("viewing_enabled") or not html_invoice.get("is_active"):
            raise HTTPException(status_code=403, detail="Invoice viewing is disabled")
        
        # Increment view count (in real implementation)
        # await db_service.increment_html_invoice_view_count(invoice_uuid)
        
        # Return the HTML content directly
        return HTMLResponse(content=html_invoice["html_content"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error viewing HTML invoice: {str(e)}")

@router.get("/{invoice_uuid}/html-details")
async def get_html_invoice_details(invoice_uuid: str):
    """Get HTML invoice metadata and details (JSON response)"""
    try:
        db_service = get_database_service()
        
        # Get the HTML invoice details from database
        # For now, mock the response
        html_invoice_details = {
            "id": f"html_{invoice_uuid[:8]}",
            "invoice_uuid": invoice_uuid,
            "invoice_number": f"INV-{invoice_uuid[:8].upper()}",
            "user_id": "mock_user_id",
            "workflow_id": f"workflow_{invoice_uuid[:8]}",
            "template_used": "modern-professional-invoice-bb14c848.html",
            "template_version": "1.0",
            "contract_name": "Mock Contract",
            "generation_method": "template_based",
            "generated_by_agent": "ui_generation_agent",
            "content_type": "text/html",
            "character_count": 5000,
            "viewing_enabled": True,
            "viewing_url": f"/api/invoices/{invoice_uuid}/view",
            "access_count": 0,
            "last_viewed_at": None,
            "status": "generated",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if not html_invoice_details:
            raise HTTPException(status_code=404, detail="HTML invoice not found")
        
        return html_invoice_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching HTML invoice details: {str(e)}")

@router.get("/html/list")
async def list_html_invoices(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    limit: int = Query(50, description="Number of HTML invoices to return"),
    offset: int = Query(0, description="Number of HTML invoices to skip")
):
    """List all HTML invoices with filtering options"""
    try:
        db_service = get_database_service()
        
        # In real implementation, you would:
        # html_invoices, total = await db_service.list_html_invoices(
        #     user_id=user_id, workflow_id=workflow_id, limit=limit, offset=offset
        # )
        
        # Mock response for now
        mock_invoices = [
            {
                "id": f"html_mock_{i}",
                "invoice_uuid": f"inv_uuid_{i:03d}",
                "invoice_number": f"INV-MOCK{i:03d}",
                "user_id": user_id or "mock_user",
                "workflow_id": workflow_id or f"workflow_{i}",
                "template_used": "modern-professional-invoice.html",
                "contract_name": f"Mock Contract {i}",
                "viewing_url": f"/api/invoices/inv_uuid_{i:03d}/view",
                "status": "generated",
                "created_at": datetime.now().isoformat()
            }
            for i in range(1, min(limit + 1, 6))  # Mock up to 5 invoices
        ]
        
        return {
            "html_invoices": mock_invoices,
            "total": len(mock_invoices),
            "limit": limit,
            "offset": offset,
            "filters": {
                "user_id": user_id,
                "workflow_id": workflow_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching HTML invoices: {str(e)}")

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