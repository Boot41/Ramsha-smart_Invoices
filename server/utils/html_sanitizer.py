import re
import html
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class HTMLSanitizer:
    """Utility class for sanitizing HTML templates and preventing XSS attacks"""
    
    # Allowed HTML tags for invoice templates
    ALLOWED_TAGS = {
        'html', 'head', 'title', 'meta', 'style', 'body',
        'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'ul', 'ol', 'li', 'br', 'hr', 'strong', 'b', 'em', 'i',
        'img', 'a'
    }
    
    # Allowed attributes for specific tags
    ALLOWED_ATTRIBUTES = {
        'div': ['class', 'id', 'style'],
        'span': ['class', 'id', 'style'],
        'p': ['class', 'id', 'style'],
        'h1': ['class', 'id', 'style'], 'h2': ['class', 'id', 'style'],
        'h3': ['class', 'id', 'style'], 'h4': ['class', 'id', 'style'],
        'h5': ['class', 'id', 'style'], 'h6': ['class', 'id', 'style'],
        'table': ['class', 'id', 'style'], 'thead': ['class', 'id', 'style'],
        'tbody': ['class', 'id', 'style'], 'tr': ['class', 'id', 'style'],
        'th': ['class', 'id', 'style'], 'td': ['class', 'id', 'style'],
        'ul': ['class', 'id', 'style'], 'ol': ['class', 'id', 'style'],
        'li': ['class', 'id', 'style'],
        'img': ['src', 'alt', 'class', 'style', 'width', 'height'],
        'a': ['href', 'class', 'style'],
        'meta': ['charset', 'name', 'content']
    }
    
    # Dangerous patterns that should be removed
    DANGEROUS_PATTERNS = [
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        r'on\w+\s*=',  # Event handlers like onclick, onload, etc.
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<button[^>]*>.*?</button>',
        r'<link[^>]*>'
    ]
    
    @staticmethod
    def sanitize_html_template(html_content: str) -> str:
        """
        Sanitize HTML template content to prevent XSS attacks
        
        Args:
            html_content: Raw HTML template content
            
        Returns:
            Sanitized HTML content safe for rendering
        """
        try:
            # Remove dangerous patterns
            sanitized = html_content
            for pattern in HTMLSanitizer.DANGEROUS_PATTERNS:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove dangerous attributes from inline styles
            sanitized = HTMLSanitizer._sanitize_inline_styles(sanitized)
            
            # Validate placeholders (ensure they follow expected format)
            sanitized = HTMLSanitizer._validate_placeholders(sanitized)
            
            logger.info("HTML template sanitized successfully")
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing HTML template: {str(e)}")
            raise ValueError(f"Failed to sanitize HTML template: {str(e)}")
    
    @staticmethod
    def _sanitize_inline_styles(html_content: str) -> str:
        """Remove dangerous CSS properties from inline styles"""
        
        # Dangerous CSS properties that could be used for attacks
        dangerous_css = [
            r'expression\s*\(',
            r'javascript:',
            r'@import',
            r'behavior\s*:',
            r'-moz-binding',
            r'-webkit-binding',
            r'binding\s*:'
        ]
        
        sanitized = html_content
        for pattern in dangerous_css:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def _validate_placeholders(html_content: str) -> str:
        """Validate that placeholders follow the expected {{PLACEHOLDER}} format"""
        
        # Find all placeholders
        placeholder_pattern = r'\{\{([A-Z_]+)\}\}'
        placeholders = re.findall(placeholder_pattern, html_content)
        
        # List of expected placeholders
        expected_placeholders = {
            'PROVIDER_NAME', 'CLIENT_NAME', 'INVOICE_NUMBER', 'INVOICE_DATE',
            'DUE_DATE', 'TOTAL_AMOUNT', 'SERVICE_ITEMS', 'PAYMENT_TERMS',
            'PROVIDER_ADDRESS', 'CLIENT_ADDRESS', 'STATUS', 'PROVIDER_EMAIL',
            'CLIENT_EMAIL', 'PROVIDER_PHONE', 'CLIENT_PHONE', 'SUBTOTAL',
            'TAX_AMOUNT', 'DISCOUNT', 'NOTES'
        }
        
        # Log unexpected placeholders (for debugging)
        unexpected = set(placeholders) - expected_placeholders
        if unexpected:
            logger.warning(f"Unexpected placeholders found: {unexpected}")
        
        return html_content
    
    @staticmethod
    def inject_data_safely(template_content: str, invoice_data: Dict[str, Any]) -> str:
        """
        Safely inject invoice data into HTML template placeholders
        
        Args:
            template_content: HTML template with placeholders
            invoice_data: Dictionary containing invoice data
            
        Returns:
            HTML with data injected and escaped for safety
        """
        try:
            # Create safe data dictionary with escaped values
            safe_data = HTMLSanitizer._create_safe_data_dict(invoice_data)
            
            # Replace placeholders with escaped data
            rendered_html = template_content
            
            for placeholder, value in safe_data.items():
                pattern = f'{{{{{placeholder}}}}}'
                rendered_html = rendered_html.replace(pattern, str(value))
            
            # Handle service items table rows specially
            if '{{SERVICE_ITEMS}}' in rendered_html:
                service_items_html = HTMLSanitizer._generate_service_items_html(invoice_data)
                rendered_html = rendered_html.replace('{{SERVICE_ITEMS}}', service_items_html)
            
            return rendered_html
            
        except Exception as e:
            logger.error(f"Error injecting data into template: {str(e)}")
            raise ValueError(f"Failed to inject data into template: {str(e)}")
    
    @staticmethod
    def _create_safe_data_dict(invoice_data: Dict[str, Any]) -> Dict[str, str]:
        """Create a dictionary of safely escaped data for template injection"""
        
        def safe_get(data: Dict[str, Any], key_path: str, default: str = "") -> str:
            """Safely get nested dictionary value and escape it"""
            keys = key_path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return html.escape(str(default))
            
            return html.escape(str(current) if current is not None else default)
        
        # Extract and escape all data
        safe_data = {
            'PROVIDER_NAME': safe_get(invoice_data, 'service_provider.name', 'Service Provider'),
            'CLIENT_NAME': safe_get(invoice_data, 'client.name', 'Client Name'),
            'PROVIDER_ADDRESS': safe_get(invoice_data, 'service_provider.address', ''),
            'CLIENT_ADDRESS': safe_get(invoice_data, 'client.address', ''),
            'PROVIDER_EMAIL': safe_get(invoice_data, 'service_provider.email', ''),
            'CLIENT_EMAIL': safe_get(invoice_data, 'client.email', ''),
            'PROVIDER_PHONE': safe_get(invoice_data, 'service_provider.phone', ''),
            'CLIENT_PHONE': safe_get(invoice_data, 'client.phone', ''),
            'TOTAL_AMOUNT': safe_get(invoice_data, 'payment_terms.amount', '0.00'),
            'PAYMENT_TERMS': safe_get(invoice_data, 'payment_terms.frequency', 'Net 30'),
            'NOTES': safe_get(invoice_data, 'notes', ''),
            'STATUS': 'Draft',  # Default status
            'INVOICE_NUMBER': 'INV-PREVIEW',  # Will be overridden
            'INVOICE_DATE': '',  # Will be overridden
            'DUE_DATE': '',  # Will be overridden
        }
        
        # Calculate totals if service data exists
        if 'services' in invoice_data and isinstance(invoice_data['services'], list):
            subtotal = sum(float(service.get('total_amount', 0)) for service in invoice_data['services'])
            safe_data['SUBTOTAL'] = html.escape(f"{subtotal:.2f}")
            safe_data['TAX_AMOUNT'] = "0.00"  # Default, can be calculated
            safe_data['DISCOUNT'] = "0.00"   # Default
        
        return safe_data
    
    @staticmethod
    def _generate_service_items_html(invoice_data: Dict[str, Any]) -> str:
        """Generate safe HTML for service items table rows"""
        
        if 'services' not in invoice_data or not isinstance(invoice_data['services'], list):
            return '<tr><td colspan="4">No services listed</td></tr>'
        
        rows_html = ""
        for service in invoice_data['services']:
            description = html.escape(str(service.get('description', 'Service')))
            quantity = html.escape(str(service.get('quantity', 1)))
            unit_price = html.escape(f"{float(service.get('unit_price', 0)):.2f}")
            total = html.escape(f"{float(service.get('total_amount', 0)):.2f}")
            
            rows_html += f"""
            <tr>
                <td>{description}</td>
                <td>{quantity}</td>
                <td>${unit_price}</td>
                <td>${total}</td>
            </tr>
            """
        
        return rows_html.strip()

class TemplateValidator:
    """Validator for HTML invoice templates"""
    
    @staticmethod
    def validate_template_structure(html_content: str) -> List[str]:
        """
        Validate that the HTML template has the required structure
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for required DOCTYPE
        if not html_content.strip().startswith('<!DOCTYPE html>'):
            errors.append("Missing DOCTYPE declaration")
        
        # Check for basic HTML structure
        if '<html>' not in html_content or '</html>' not in html_content:
            errors.append("Missing HTML tags")
        
        if '<head>' not in html_content or '</head>' not in html_content:
            errors.append("Missing HEAD section")
        
        if '<body>' not in html_content or '</body>' not in html_content:
            errors.append("Missing BODY section")
        
        # Check for embedded styles (no external resources allowed)
        if '<link' in html_content.lower():
            errors.append("External stylesheets not allowed - use embedded CSS only")
        
        if 'src=' in html_content and 'http' in html_content:
            errors.append("External resources not allowed")
        
        # Check for required placeholders
        required_placeholders = ['{{INVOICE_NUMBER}}', '{{CLIENT_NAME}}', '{{PROVIDER_NAME}}']
        for placeholder in required_placeholders:
            if placeholder not in html_content:
                errors.append(f"Missing required placeholder: {placeholder}")
        
        return errors
    
    @staticmethod
    def is_template_safe(html_content: str) -> bool:
        """Quick check if template is safe for rendering"""
        dangerous_patterns = ['<script', 'javascript:', 'on=', 'onerror', 'onclick']
        content_lower = html_content.lower()
        
        return not any(pattern in content_lower for pattern in dangerous_patterns)