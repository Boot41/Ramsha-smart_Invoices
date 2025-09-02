from typing import Dict, Any, Optional, List
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from utils.html_sanitizer import HTMLSanitizer, TemplateValidator
from services.database_service import get_database_service

logger = logging.getLogger(__name__)

class TemplateService:
    """Service for managing HTML invoice templates and rendering them with data"""
    
    def __init__(self):
        self.db_service = get_database_service()
        self.templates_dir = Path(__file__).parent.parent / "templates" / "invoices"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_template_by_id(self, template_id: str) -> Optional[str]:
        """Retrieve HTML template content by template ID"""
        try:
            # Try file system first (for now, until database integration is complete)
            template_files = list(self.templates_dir.glob(f"*{template_id}*.html"))
            if template_files:
                with open(template_files[0], 'r', encoding='utf-8') as f:
                    return f.read()
            
            # Try exact filename match
            exact_file = self.templates_dir / f"{template_id}.html"
            if exact_file.exists():
                with open(exact_file, 'r', encoding='utf-8') as f:
                    return f.read()
            
            logger.warning(f"Template not found: {template_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving template {template_id}: {str(e)}")
            return None
    
    async def render_invoice_preview(
        self,
        template_id: str,
        invoice_data: Dict[str, Any],
        invoice_number: Optional[str] = None,
        invoice_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        status: str = "Draft"
    ) -> str:
        """
        Render an invoice preview with secure data injection
        
        Args:
            template_id: ID of the HTML template
            invoice_data: Invoice data dictionary
            invoice_number: Override invoice number
            invoice_date: Override invoice date  
            due_date: Override due date
            status: Invoice status
            
        Returns:
            Rendered HTML ready for safe display
        """
        try:
            # Get template content
            template_content = await self.get_template_by_id(template_id)
            if not template_content:
                raise ValueError(f"Template not found: {template_id}")
            
            # Validate template safety
            if not TemplateValidator.is_template_safe(template_content):
                raise ValueError("Template contains unsafe content")
            
            # Sanitize the template
            safe_template = HTMLSanitizer.sanitize_html_template(template_content)
            
            # Prepare enhanced invoice data with preview overrides
            enhanced_data = self._prepare_preview_data(
                invoice_data, invoice_number, invoice_date, due_date, status
            )
            
            # Inject data safely
            rendered_html = HTMLSanitizer.inject_data_safely(safe_template, enhanced_data)
            
            # Add preview watermark CSS if in preview mode
            if status == "Draft" or "PREVIEW" in (invoice_number or ""):
                rendered_html = self._add_preview_watermark(rendered_html)
            
            logger.info(f"Successfully rendered invoice preview for template {template_id}")
            return rendered_html
            
        except Exception as e:
            logger.error(f"Error rendering invoice preview: {str(e)}")
            raise ValueError(f"Failed to render invoice preview: {str(e)}")
    
    async def render_final_invoice(
        self,
        template_id: str,
        invoice_data: Dict[str, Any],
        invoice_number: str,
        invoice_date: datetime,
        due_date: datetime,
        status: str = "Pending"
    ) -> str:
        """
        Render final invoice for PDF generation (no preview watermarks)
        
        Returns:
            Clean HTML ready for PDF conversion
        """
        return await self.render_invoice_preview(
            template_id=template_id,
            invoice_data=invoice_data,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            status=status
        )
    
    def _prepare_preview_data(
        self,
        invoice_data: Dict[str, Any],
        invoice_number: Optional[str],
        invoice_date: Optional[datetime],
        due_date: Optional[datetime],
        status: str
    ) -> Dict[str, Any]:
        """Prepare invoice data with preview-specific overrides"""
        
        # Create a copy to avoid modifying original data
        enhanced_data = dict(invoice_data)
        
        # Add preview-specific metadata
        enhanced_data.update({
            'preview_mode': True,
            'generated_at': datetime.now().isoformat(),
            'template_rendered_by': 'template_service'
        })
        
        # Override dates if provided
        if invoice_date:
            enhanced_data['invoice_date'] = invoice_date.strftime('%Y-%m-%d')
            enhanced_data['invoice_date_formatted'] = invoice_date.strftime('%B %d, %Y')
        
        if due_date:
            enhanced_data['due_date'] = due_date.strftime('%Y-%m-%d')
            enhanced_data['due_date_formatted'] = due_date.strftime('%B %d, %Y')
        
        # Override invoice number if provided
        if invoice_number:
            enhanced_data['invoice_number'] = invoice_number
        
        # Add status
        enhanced_data['status'] = status
        enhanced_data['status_class'] = self._get_status_css_class(status)
        
        # Ensure required fields exist with defaults
        enhanced_data.setdefault('payment_terms', {})
        enhanced_data['payment_terms'].setdefault('amount', 0)
        enhanced_data['payment_terms'].setdefault('currency', 'USD')
        
        return enhanced_data
    
    def _get_status_css_class(self, status: str) -> str:
        """Get CSS class for invoice status styling"""
        status_classes = {
            'Draft': 'status-draft',
            'Pending': 'status-pending', 
            'Paid': 'status-paid',
            'Overdue': 'status-overdue',
            'Cancelled': 'status-cancelled'
        }
        return status_classes.get(status, 'status-default')
    
    def _add_preview_watermark(self, rendered_html: str) -> str:
        """Add preview watermark styling to rendered HTML"""
        
        watermark_css = """
        <style>
            .preview-watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 6rem;
                color: rgba(59, 130, 246, 0.1);
                font-weight: bold;
                pointer-events: none;
                z-index: 9999;
                user-select: none;
            }
            @media print {
                .preview-watermark { display: none; }
            }
        </style>
        """
        
        watermark_html = """
        <div class="preview-watermark">PREVIEW</div>
        """
        
        # Insert watermark CSS in head
        if '<head>' in rendered_html:
            rendered_html = rendered_html.replace('</head>', f'{watermark_css}</head>')
        
        # Insert watermark HTML in body
        if '<body>' in rendered_html:
            rendered_html = rendered_html.replace('<body>', f'<body>{watermark_html}')
        
        return rendered_html
    
    async def validate_template(self, template_content: str) -> Dict[str, Any]:
        """
        Validate HTML template for security and structure
        
        Returns:
            Validation result with errors and warnings
        """
        try:
            # Structure validation
            structure_errors = TemplateValidator.validate_template_structure(template_content)
            
            # Security validation
            is_safe = TemplateValidator.is_template_safe(template_content)
            
            # Placeholder validation (extract and check placeholders)
            placeholder_pattern = r'\{\{([A-Z_]+)\}\}'
            import re
            found_placeholders = set(re.findall(placeholder_pattern, template_content))
            
            required_placeholders = {'INVOICE_NUMBER', 'CLIENT_NAME', 'PROVIDER_NAME'}
            missing_placeholders = required_placeholders - found_placeholders
            
            return {
                'valid': is_safe and len(structure_errors) == 0 and len(missing_placeholders) == 0,
                'safe': is_safe,
                'structure_errors': structure_errors,
                'missing_placeholders': list(missing_placeholders),
                'found_placeholders': list(found_placeholders),
                'warnings': []
            }
            
        except Exception as e:
            logger.error(f"Error validating template: {str(e)}")
            return {
                'valid': False,
                'safe': False,
                'structure_errors': [f"Validation error: {str(e)}"],
                'missing_placeholders': [],
                'found_placeholders': [],
                'warnings': []
            }
    
    async def list_available_templates(self) -> List[Dict[str, Any]]:
        """List all available HTML templates"""
        try:
            templates = []
            
            # Get templates from file system
            for template_file in self.templates_dir.glob("*.html"):
                try:
                    file_id = template_file.stem
                    stat = template_file.stat()
                    
                    # Try to extract metadata from file content
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    template_type = "Professional Invoice Template"
                    model_used = "AI Generated"
                    
                    # Basic content analysis for better metadata
                    if "{{PROVIDER_NAME}}" in content:
                        template_type = "Business Invoice Template"
                    if "professional" in content.lower():
                        template_type = "Professional Invoice Template"
                    
                    templates.append({
                        'id': file_id,
                        'name': file_id.replace('-', ' ').title(),
                        'type': template_type,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'model_used': model_used,
                        'source': 'file_system',
                        'file_size': stat.st_size
                    })
                    
                except Exception as file_error:
                    logger.warning(f"Error processing template file {template_file}: {str(file_error)}")
                    continue
            
            # Try to get templates from database as well
            try:
                db_templates, _ = await self.db_service.list_invoice_templates()
                for template in db_templates:
                    # Skip if file system version exists
                    if not any(t['id'] == str(template.id) for t in templates):
                        templates.append({
                            'id': str(template.id),
                            'name': template.template_name,
                            'type': template.template_type,
                            'created_at': template.created_at.isoformat(),
                            'model_used': template.model_used or 'AI Generated',
                            'source': 'database'
                        })
            except Exception as db_error:
                logger.warning(f"Could not load database templates: {str(db_error)}")
            
            return templates
            
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            return []
    
    async def create_sample_invoice_data(self, template_id: str) -> Dict[str, Any]:
        """Create sample invoice data for template preview"""
        
        return {
            "contract_title": "Professional Services Agreement",
            "contract_number": f"DEMO-{template_id[:8].upper()}",
            "client": {
                "name": "Acme Corporation",
                "email": "billing@acme-corp.com",
                "address": "123 Business Ave\nCorporate City, CC 12345",
                "phone": "+1 (555) 123-4567",
                "tax_id": "12-3456789",
                "role": "Client"
            },
            "service_provider": {
                "name": "Professional Services LLC",
                "email": "invoices@proservices.com",
                "address": "456 Service St\nProvider City, PC 67890",
                "phone": "+1 (555) 987-6543",
                "tax_id": "98-7654321",
                "role": "Service Provider"
            },
            "payment_terms": {
                "amount": 2500.00,
                "currency": "USD",
                "frequency": "monthly",
                "due_days": 30,
                "late_fee": 50.00,
                "discount_terms": "2/10 net 30"
            },
            "services": [
                {
                    "description": "Business Consulting",
                    "quantity": 20,
                    "unit_price": 75.00,
                    "total_amount": 1500.00,
                    "unit": "hours"
                },
                {
                    "description": "Strategic Planning",
                    "quantity": 10,
                    "unit_price": 100.00,
                    "total_amount": 1000.00,
                    "unit": "hours"
                }
            ],
            "notes": "Thank you for your business. Payment is due within 30 days.",
            "generated_at": datetime.now().isoformat(),
            "preview_mode": True
        }