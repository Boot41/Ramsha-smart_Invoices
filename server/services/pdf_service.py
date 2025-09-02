from typing import Dict, Any, Optional
import io
import logging
from datetime import datetime

# Graceful import handling for weasyprint
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("WeasyPrint not available. PDF generation will be disabled.")
    HTML = CSS = FontConfiguration = None
    WEASYPRINT_AVAILABLE = False

from utils.html_sanitizer import HTMLSanitizer
from services.template_service import TemplateService

logger = logging.getLogger(__name__)

class PDFService:
    """Service for generating PDF documents from HTML templates"""
    
    def __init__(self):
        self.template_service = TemplateService()
        
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is not available. PDF generation is disabled.")
        
        self.font_config = FontConfiguration()
        
        # Default CSS for PDF generation
        self.pdf_css = CSS(string="""
            @page {
                margin: 0.5in;
                size: letter;
            }
            
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
                color: #333;
            }
            
            .preview-watermark {
                display: none !important;
            }
            
            table {
                border-collapse: collapse;
                width: 100%;
            }
            
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            
            .status-draft { background-color: #f8f9fa; color: #6c757d; }
            .status-pending { background-color: #fff3cd; color: #856404; }
            .status-paid { background-color: #d1edff; color: #0c5460; }
            .status-overdue { background-color: #f8d7da; color: #721c24; }
            
            @media print {
                .no-print { display: none !important; }
                .preview-watermark { display: none !important; }
            }
        """, font_config=self.font_config)
    
    async def generate_invoice_pdf(
        self,
        template_id: str,
        invoice_data: Dict[str, Any],
        invoice_number: str,
        invoice_date: datetime,
        due_date: datetime,
        status: str = "Pending"
    ) -> bytes:
        """
        Generate PDF from invoice template and data
        
        Args:
            template_id: ID of the HTML template
            invoice_data: Invoice data dictionary
            invoice_number: Invoice number
            invoice_date: Invoice date
            due_date: Due date
            status: Invoice status
            
        Returns:
            PDF content as bytes
        """
        try:
            # Get rendered HTML from template service
            rendered_html = await self.template_service.render_final_invoice(
                template_id=template_id,
                invoice_data=invoice_data,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                due_date=due_date,
                status=status
            )
            
            # Additional sanitization for PDF generation
            safe_html = self._prepare_html_for_pdf(rendered_html)
            
            # Generate PDF
            html_doc = HTML(string=safe_html)
            pdf_buffer = io.BytesIO()
            
            html_doc.write_pdf(
                pdf_buffer, 
                stylesheets=[self.pdf_css],
                font_config=self.font_config
            )
            
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            logger.info(f"Successfully generated PDF for invoice {invoice_number}")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF for invoice {invoice_number}: {str(e)}")
            raise ValueError(f"Failed to generate PDF: {str(e)}")
    
    async def generate_preview_pdf(
        self,
        template_id: str,
        invoice_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate a preview PDF with sample data"""
        
        # Use sample data if none provided
        if not invoice_data:
            invoice_data = await self.template_service.create_sample_invoice_data(template_id)
        
        # Generate with preview settings
        return await self.generate_invoice_pdf(
            template_id=template_id,
            invoice_data=invoice_data,
            invoice_number=f"PREVIEW-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            invoice_date=datetime.now(),
            due_date=datetime.now(),
            status="Draft"
        )
    
    def _prepare_html_for_pdf(self, html_content: str) -> str:
        """Prepare HTML content for PDF generation"""
        
        # Remove or modify elements that don't work well in PDF
        processed_html = html_content
        
        # Remove preview watermarks for final PDF
        processed_html = processed_html.replace('<div class="preview-watermark">PREVIEW</div>', '')
        
        # Ensure proper encoding
        if '<!DOCTYPE html>' not in processed_html:
            processed_html = '<!DOCTYPE html>\n' + processed_html
        
        # Add meta tag for proper encoding if missing
        if '<meta charset="UTF-8">' not in processed_html and '<meta charset=' not in processed_html:
            if '<head>' in processed_html:
                processed_html = processed_html.replace(
                    '<head>', 
                    '<head>\n    <meta charset="UTF-8">'
                )
        
        # Add print-friendly styles
        pdf_print_styles = """
        <style>
            @media print {
                .no-print { display: none !important; }
                .preview-watermark { display: none !important; }
            }
            
            /* Ensure good PDF formatting */
            body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            /* Page breaks */
            .page-break-before { page-break-before: always; }
            .page-break-after { page-break-after: always; }
            .page-break-avoid { page-break-inside: avoid; }
        </style>
        """
        
        if '</head>' in processed_html:
            processed_html = processed_html.replace('</head>', f'{pdf_print_styles}</head>')
        
        return processed_html
    
    def validate_pdf_generation(self, html_content: str) -> Dict[str, Any]:
        """
        Validate HTML content for PDF generation compatibility
        
        Returns:
            Validation result
        """
        try:
            # Check for common PDF generation issues
            issues = []
            warnings = []
            
            # Check for external resources
            if 'http://' in html_content or 'https://' in html_content:
                if 'src=' in html_content:
                    issues.append("External images may not render in PDF")
                if '<link' in html_content:
                    issues.append("External stylesheets not supported in PDF")
            
            # Check for JavaScript
            if '<script' in html_content.lower():
                issues.append("JavaScript is not supported in PDF generation")
            
            # Check for complex CSS
            if 'position: fixed' in html_content:
                warnings.append("Fixed positioning may not work as expected in PDF")
            
            if 'transform:' in html_content:
                warnings.append("CSS transforms may not render correctly in PDF")
            
            # Check document structure
            if '<!DOCTYPE html>' not in html_content:
                warnings.append("Missing DOCTYPE declaration")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'warnings': warnings,
                'pdf_ready': len(issues) == 0
            }
            
        except Exception as e:
            logger.error(f"Error validating HTML for PDF: {str(e)}")
            return {
                'valid': False,
                'issues': [f"Validation error: {str(e)}"],
                'warnings': [],
                'pdf_ready': False
            }
    
    async def generate_bulk_invoices_pdf(
        self,
        invoices: list[Dict[str, Any]]
    ) -> bytes:
        """Generate a single PDF containing multiple invoices"""
        
        try:
            combined_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Invoice Batch</title>
                <style>
                    .invoice-page {
                        page-break-after: always;
                    }
                    .invoice-page:last-child {
                        page-break-after: auto;
                    }
                </style>
            </head>
            <body>
            """
            
            for i, invoice_data in enumerate(invoices):
                # Get rendered HTML for each invoice
                rendered_html = await self.template_service.render_final_invoice(
                    template_id=invoice_data['template_id'],
                    invoice_data=invoice_data['data'],
                    invoice_number=invoice_data['invoice_number'],
                    invoice_date=invoice_data['invoice_date'],
                    due_date=invoice_data['due_date'],
                    status=invoice_data.get('status', 'Pending')
                )
                
                # Extract body content (without html/head tags)
                import re
                body_match = re.search(r'<body[^>]*>(.*?)</body>', rendered_html, re.DOTALL | re.IGNORECASE)
                if body_match:
                    body_content = body_match.group(1)
                    combined_html += f'<div class="invoice-page">{body_content}</div>\n'
            
            combined_html += """
            </body>
            </html>
            """
            
            # Generate PDF
            html_doc = HTML(string=combined_html)
            pdf_buffer = io.BytesIO()
            
            html_doc.write_pdf(
                pdf_buffer,
                stylesheets=[self.pdf_css],
                font_config=self.font_config
            )
            
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            logger.info(f"Successfully generated bulk PDF with {len(invoices)} invoices")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating bulk PDF: {str(e)}")
            raise ValueError(f"Failed to generate bulk PDF: {str(e)}")