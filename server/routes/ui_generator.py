from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from services.template_service import TemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ui-generator", tags=["🎨 UI Generator"])

# Request/Response Models
class UIGenerationRequest(BaseModel):
    data: Dict[str, Any]
    template_type: str = "invoice"  # invoice, contract, report, etc.
    style_preferences: Optional[Dict[str, Any]] = None
    layout_preferences: Optional[str] = "modern"  # modern, classic, minimal

class UITemplateWithDataRequest(BaseModel):
    template_id: Optional[str] = None
    data: Dict[str, Any]
    preview_mode: bool = True
    include_styling: bool = True

class CodeGenerationRequest(BaseModel):
    invoice_data: Dict[str, Any]
    output_format: str = "react"  # react, vue, html, angular, svelte
    component_name: Optional[str] = "InvoiceComponent"
    styling_framework: str = "tailwind"  # tailwind, bootstrap, css, styled-components
    include_types: bool = True

class UITemplateResponse(BaseModel):
    html_content: str
    css_content: str
    template_id: str
    data_used: Dict[str, Any]
    preview_url: Optional[str] = None

# Initialize services
template_service = TemplateService()

@router.post("/generate-ui", response_model=UITemplateResponse)
async def generate_ui_with_data(request: UIGenerationRequest):
    """
    Generate a UI template populated with your data
    
    This endpoint takes your data and creates a beautiful UI template with that data populated.
    Perfect for previewing how your data will look in different UI layouts.
    """
    try:
        # Generate or select appropriate template based on data structure
        if request.template_type == "invoice":
            template_id = await _select_best_invoice_template(request.data)
        else:
            # For other types, use a default template
            template_id = "default-modern"
        
        # Generate UI with data
        html_content = await _generate_ui_with_data(
            template_id=template_id,
            data=request.data,
            style_preferences=request.style_preferences,
            layout_preferences=request.layout_preferences
        )
        
        # Generate accompanying CSS
        css_content = await _generate_css_for_template(template_id, request.style_preferences)
        
        return UITemplateResponse(
            html_content=html_content,
            css_content=css_content,
            template_id=template_id,
            data_used=request.data,
            preview_url=f"/api/ui-generator/preview/{template_id}"
        )
        
    except Exception as e:
        logger.error(f"Error generating UI with data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate UI: {str(e)}")

@router.post("/preview-with-data")
async def preview_template_with_data(request: UITemplateWithDataRequest):
    """
    Preview an existing template with your custom data
    
    Use this endpoint to see how your data looks in existing UI templates.
    """
    try:
        # If no template_id provided, select the best one based on data
        template_id = request.template_id
        if not template_id:
            template_id = await _select_best_template_for_data(request.data)
        
        # Get the base template
        template_content = await template_service.get_template_by_id(template_id)
        if not template_content:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Populate template with data
        populated_html = await _populate_template_with_data(
            template_content=template_content,
            data=request.data,
            include_styling=request.include_styling
        )
        
        return {
            "html": populated_html,
            "template_id": template_id,
            "data_preview": request.data,
            "status": "success",
            "message": f"Template populated with {len(request.data)} data fields"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing template with data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preview template: {str(e)}")

@router.get("/templates/by-data-type")
async def get_templates_by_data_type(data_type: str = "invoice"):
    """
    Get available UI templates filtered by data type
    """
    try:
        all_templates = await template_service.list_available_templates()
        
        # Filter templates based on data type
        filtered_templates = [
            template for template in all_templates 
            if template.get('category', '').lower() == data_type.lower() or 
               template.get('type', '').lower() == data_type.lower()
        ]
        
        return {
            "templates": filtered_templates,
            "data_type": data_type,
            "total": len(filtered_templates),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting templates by data type: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.post("/live-preview")
async def live_preview_with_data(request: Dict[str, Any]):
    """
    Real-time preview endpoint for UI generation
    
    Perfect for live editing - send your data and get instant HTML preview
    """
    try:
        data = request.get('data', {})
        template_style = request.get('style', 'modern')
        
        if not data:
            return {
                "html": "<div class='preview-placeholder'>Add some data to see the preview</div>",
                "message": "No data provided",
                "status": "empty"
            }
        
        # Generate a quick preview HTML
        preview_html = await _generate_quick_preview(data, template_style)
        
        return {
            "html": preview_html,
            "data_fields": list(data.keys()),
            "field_count": len(data),
            "style": template_style,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error generating live preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate live preview: {str(e)}")

@router.get("/sample-data/{template_type}")
async def get_sample_data_for_ui(template_type: str):
    """
    Get sample data structure for different UI template types
    """
    sample_data_templates = {
        "invoice": {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-12-05",
            "due_date": "2024-12-20",
            "company": {
                "name": "Acme Solutions Inc.",
                "address": "123 Business St, City, State 12345",
                "email": "billing@acmesolutions.com",
                "phone": "+1 (555) 123-4567"
            },
            "client": {
                "name": "Tech Startup LLC",
                "address": "456 Innovation Ave, Tech City, TC 67890",
                "email": "accounts@techstartup.com"
            },
            "items": [
                {"description": "Web Development Services", "quantity": 40, "rate": 150, "amount": 6000},
                {"description": "UI/UX Design", "quantity": 20, "rate": 120, "amount": 2400},
                {"description": "Project Management", "quantity": 10, "rate": 100, "amount": 1000}
            ],
            "subtotal": 9400,
            "tax_rate": 0.08,
            "tax_amount": 752,
            "total": 10152,
            "payment_terms": "Net 15 days",
            "notes": "Thank you for your business!"
        },
        "contract": {
            "contract_title": "Service Agreement",
            "contract_number": "SA-2024-001",
            "effective_date": "2024-12-05",
            "expiration_date": "2025-12-05",
            "client_name": "Tech Innovations Corp",
            "service_provider": "Professional Services LLC",
            "scope_of_work": "Custom software development and maintenance",
            "payment_terms": "Monthly billing cycle",
            "total_value": 120000
        },
        "report": {
            "report_title": "Monthly Performance Report",
            "report_date": "2024-12-05",
            "period": "November 2024",
            "metrics": {
                "revenue": 45000,
                "expenses": 28000,
                "profit": 17000,
                "growth_rate": "12%"
            },
            "highlights": [
                "Exceeded revenue target by 8%",
                "Reduced operational costs by 5%",
                "Launched 2 new product features"
            ]
        }
    }
    
    return {
        "template_type": template_type,
        "sample_data": sample_data_templates.get(template_type, {}),
        "available_types": list(sample_data_templates.keys()),
        "status": "success"
    }

@router.post("/generate-code")
async def generate_code_from_invoice_data(request: CodeGenerationRequest):
    """
    Generate component code from JSON invoice data
    
    Takes invoice JSON data and generates a complete component in the specified framework
    with proper styling and TypeScript/JavaScript support.
    """
    try:
        invoice_data = request.invoice_data
        output_format = request.output_format.lower()
        component_name = request.component_name or "InvoiceComponent"
        styling_framework = request.styling_framework.lower()
        
        # Generate component code based on format
        if output_format == "react":
            code = await _generate_react_component(invoice_data, component_name, styling_framework, request.include_types)
        elif output_format == "vue":
            code = await _generate_vue_component(invoice_data, component_name, styling_framework)
        elif output_format == "angular":
            code = await _generate_angular_component(invoice_data, component_name, styling_framework)
        elif output_format == "svelte":
            code = await _generate_svelte_component(invoice_data, component_name, styling_framework)
        elif output_format == "html":
            code = await _generate_html_template(invoice_data, styling_framework)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported output format: {output_format}")
        
        return {
            "component_code": code,
            "output_format": output_format,
            "component_name": component_name,
            "styling_framework": styling_framework,
            "data_structure": invoice_data,
            "file_extension": _get_file_extension(output_format, request.include_types),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate code: {str(e)}")

@router.post("/generate-multiple-formats")
async def generate_code_multiple_formats(request: Dict[str, Any]):
    """
    Generate component code in multiple formats at once
    
    Perfect for getting the same invoice component in React, Vue, Angular, etc.
    """
    try:
        invoice_data = request.get('invoice_data', {})
        formats = request.get('formats', ['react', 'vue', 'html'])
        component_name = request.get('component_name', 'InvoiceComponent')
        styling_framework = request.get('styling_framework', 'tailwind')
        include_types = request.get('include_types', True)
        
        if not invoice_data:
            raise HTTPException(status_code=400, detail="Invoice data is required")
        
        generated_code = {}
        
        for format_type in formats:
            try:
                format_request = CodeGenerationRequest(
                    invoice_data=invoice_data,
                    output_format=format_type,
                    component_name=component_name,
                    styling_framework=styling_framework,
                    include_types=include_types
                )
                
                result = await generate_code_from_invoice_data(format_request)
                generated_code[format_type] = result
                
            except Exception as e:
                generated_code[format_type] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        return {
            "generated_code": generated_code,
            "total_formats": len(formats),
            "successful_formats": len([k for k, v in generated_code.items() if v.get("status") == "success"]),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error generating multiple formats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate multiple formats: {str(e)}")

@router.get("/supported-formats")
async def get_supported_code_formats():
    """
    Get list of supported code generation formats and styling frameworks
    """
    return {
        "output_formats": [
            {"value": "react", "label": "React (JSX/TSX)", "extensions": [".jsx", ".tsx"]},
            {"value": "vue", "label": "Vue.js", "extensions": [".vue"]},
            {"value": "angular", "label": "Angular", "extensions": [".component.ts", ".component.html", ".component.css"]},
            {"value": "svelte", "label": "Svelte", "extensions": [".svelte"]},
            {"value": "html", "label": "Pure HTML", "extensions": [".html"]}
        ],
        "styling_frameworks": [
            {"value": "tailwind", "label": "Tailwind CSS"},
            {"value": "bootstrap", "label": "Bootstrap"},
            {"value": "css", "label": "Pure CSS"},
            {"value": "styled-components", "label": "Styled Components (React only)"}
        ],
        "features": [
            "TypeScript support",
            "Responsive design",
            "Component props/data binding",
            "Modern styling frameworks",
            "Accessibility features"
        ]
    }

# Helper functions
async def _select_best_invoice_template(data: Dict[str, Any]) -> str:
    """Select the best template based on invoice data structure"""
    # Analyze data to determine best template
    if 'items' in data and len(data.get('items', [])) > 5:
        return "detailed-invoice-template"
    elif 'company' in data and 'client' in data:
        return "professional-invoice-template"
    else:
        return "simple-invoice-template"

async def _select_best_template_for_data(data: Dict[str, Any]) -> str:
    """Select the best template based on general data structure"""
    if any(key in data for key in ['invoice_number', 'invoice_date', 'items']):
        return await _select_best_invoice_template(data)
    elif any(key in data for key in ['contract_number', 'contract_title', 'client_name']):
        return "contract-template"
    else:
        return "general-data-template"

async def _generate_ui_with_data(template_id: str, data: Dict[str, Any], 
                                style_preferences: Optional[Dict[str, Any]], 
                                layout_preferences: str) -> str:
    """Generate UI HTML with data populated"""
    
    # This is a simplified version - you can expand this with actual template rendering
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated UI - {template_id}</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            .ui-container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 2rem;
                background: white;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }}
            .data-field {{
                margin-bottom: 1rem;
                padding: 0.75rem;
                background: #f8f9fa;
                border-left: 4px solid #3b82f6;
                border-radius: 4px;
            }}
            .field-label {{
                font-weight: 600;
                color: #374151;
                text-transform: capitalize;
            }}
            .field-value {{
                color: #6b7280;
                margin-top: 0.25rem;
            }}
        </style>
    </head>
    <body class="bg-gray-100 py-8">
        <div class="ui-container">
            <h1 class="text-3xl font-bold text-gray-900 mb-6">UI Template: {template_id}</h1>
            <div class="data-preview">
    """
    
    # Add data fields to HTML
    for key, value in data.items():
        if isinstance(value, dict):
            html_template += f"""
                <div class="data-field">
                    <div class="field-label">{key.replace('_', ' ')}</div>
                    <div class="field-value">
            """
            for sub_key, sub_value in value.items():
                html_template += f"<div><strong>{sub_key.replace('_', ' ')}:</strong> {sub_value}</div>"
            html_template += "</div></div>"
        elif isinstance(value, list):
            html_template += f"""
                <div class="data-field">
                    <div class="field-label">{key.replace('_', ' ')}</div>
                    <div class="field-value">
            """
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    html_template += f"<div class='mb-2'><strong>Item {i+1}:</strong>"
                    for item_key, item_value in item.items():
                        html_template += f"<div class='ml-4'>{item_key}: {item_value}</div>"
                    html_template += "</div>"
                else:
                    html_template += f"<div>• {item}</div>"
            html_template += "</div></div>"
        else:
            html_template += f"""
                <div class="data-field">
                    <div class="field-label">{key.replace('_', ' ')}</div>
                    <div class="field-value">{value}</div>
                </div>
            """
    
    html_template += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template

async def _generate_css_for_template(template_id: str, style_preferences: Optional[Dict[str, Any]]) -> str:
    """Generate CSS for the template"""
    return """
    .ui-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .data-field:hover {
        background: #e5e7eb;
        transition: background-color 0.2s ease;
    }
    """

async def _populate_template_with_data(template_content: str, data: Dict[str, Any], include_styling: bool) -> str:
    """Populate existing template with data"""
    # Simple template population - you can make this more sophisticated
    populated_content = template_content
    
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        if isinstance(value, (dict, list)):
            populated_content = populated_content.replace(placeholder, str(value))
        else:
            populated_content = populated_content.replace(placeholder, str(value))
    
    return populated_content

async def _generate_quick_preview(data: Dict[str, Any], style: str) -> str:
    """Generate a quick HTML preview"""
    preview_html = f"""
    <div class="preview-container" style="padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: #1f2937; margin-bottom: 1rem;">Live Data Preview ({style} style)</h2>
        <div class="data-grid" style="display: grid; gap: 0.5rem;">
    """
    
    for key, value in data.items():
        preview_html += f"""
            <div style="padding: 0.5rem; background: #f3f4f6; border-radius: 4px; border-left: 3px solid #3b82f6;">
                <strong style="color: #374151;">{key.replace('_', ' ').title()}:</strong>
                <span style="color: #6b7280; margin-left: 0.5rem;">{value}</span>
            </div>
        """
    
    preview_html += """
        </div>
    </div>
    """
    
    return preview_html