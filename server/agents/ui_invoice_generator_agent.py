from typing import Dict, Any, Optional
import logging
import os
from datetime import datetime
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from models.llm.base import get_model
from services.websocket_manager import get_websocket_manager
from services.database_service import get_database_service

logger = logging.getLogger(__name__)

class UIInvoiceGeneratorAgent(BaseAgent):
    """Agent responsible for generating professional React invoice components from invoice data"""
    
    def __init__(self):
        super().__init__(AgentType.UI_INVOICE_GENERATOR)
        self.model = get_model("gemini-2.0-flash", temperature=0.1, max_output_tokens=8000)
        self.websocket_manager = get_websocket_manager()
        self.db_service = get_database_service()
        # Path to client components directory
        self.client_components_path = os.path.join(os.path.dirname(__file__), "../../client/src/components/invoices")
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """
        Generate professional React invoice component from corrected invoice data
        
        Args:
            state: Current workflow state containing validated/corrected invoice data
            
        Returns:
            Updated workflow state with generated React component file path
        """
        workflow_id = state.get('workflow_id')
        self.logger.info(f"🎨 Starting UI invoice generation for workflow_id: {workflow_id}")
        
        # Notify WebSocket clients that UI generation is starting
        if workflow_id:
            await self.websocket_manager.broadcast_workflow_event(workflow_id, 'agent_started', {
                'agent': 'ui_invoice_generator',
                'message': 'Starting professional invoice template generation with Gemini-2.0-flash'
            })
        
        try:
            # Notify that we're extracting invoice data
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'ui_generation_progress', {
                    'step': 'data_extraction',
                    'message': 'Extracting invoice data for template generation'
                })
            
            # Try to retrieve invoice from database first
            invoice_data = await self._retrieve_invoice_from_database(state)
            
            # If not found in database, extract from state
            if not invoice_data:
                invoice_data = self._extract_invoice_data(state)
            
            if not invoice_data:
                raise ValueError("No invoice data found for UI generation")
            
            # Notify that we're calling Gemini API
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'ui_generation_progress', {
                    'step': 'gemini_generation',
                    'message': 'Generating professional React invoice component with Gemini-2.0-flash AI model'
                })
            
            # Generate React component using Gemini
            component_data = await self._generate_invoice_component(invoice_data, state)
            
            # Create the React component file
            component_file_path = await self._create_component_file(component_data, workflow_id)
            
            # Save template info to database
            template_saved = await self._save_template_to_database(state, component_data, component_file_path)
            
            # Notify component generation completion
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'ui_generation_progress', {
                    'step': 'component_completed',
                    'message': 'Professional React invoice component generated successfully',
                    'component_name': component_data.get("component_name", "InvoiceTemplate"),
                    'file_path': component_file_path
                })
            
            # Store generated component info in state
            state["ui_invoice_component"] = {
                "component_name": component_data["component_name"],
                "file_path": component_file_path,
                "component_type": component_data["component_type"],
                "generated_at": datetime.now().isoformat(),
                "model_used": "gemini-2.0-flash"
            }
            
            # Update state metrics
            state["processing_status"] = ProcessingStatus.SUCCESS.value
            self.update_state_metrics(state, confidence=0.95, quality_score=0.9)
            
            # Notify completion
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'agent_completed', {
                    'agent': 'ui_invoice_generator',
                    'message': 'React invoice component generation completed successfully',
                    'component_ready': True,
                    'component_path': component_file_path
                })
            
            self.logger.info("✅ React invoice component generated successfully")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ UI invoice generation failed: {str(e)}")
            
            # Notify error via WebSocket
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'agent_error', {
                    'agent': 'ui_invoice_generator',
                    'message': f'React component generation failed: {str(e)}',
                    'error_type': 'component_generation_error'
                })
            
            state["processing_status"] = ProcessingStatus.FAILED.value
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "ui_invoice_generator",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return state
    
    def _extract_invoice_data(self, state: WorkflowState) -> Optional[Dict[str, Any]]:
        """Extract invoice data from various possible sources in state"""
        
        # Try to get corrected invoice data first (from correction agent)
        if state.get("final_invoice"):
            self.logger.debug("Using final invoice data from correction agent")
            return state["final_invoice"]
        
        # Try validated invoice data (after human input)
        if state.get("invoice_data") and isinstance(state["invoice_data"], dict):
            invoice_data = state["invoice_data"]
            
            # Check for nested structures
            if "invoice_response" in invoice_data:
                if isinstance(invoice_data["invoice_response"], dict) and "invoice_data" in invoice_data["invoice_response"]:
                    self.logger.debug("Using nested invoice data from invoice_response")
                    return invoice_data["invoice_response"]["invoice_data"]
                elif hasattr(invoice_data["invoice_response"], "dict"):
                    # Pydantic model
                    return invoice_data["invoice_response"].dict()
            
            self.logger.debug("Using root invoice data")
            return invoice_data
        
        # Try contract data as fallback
        if state.get("contract_data"):
            self.logger.debug("Using contract data as fallback")
            return state["contract_data"]
        
        self.logger.warning("No invoice data found for UI generation")
        return None
    
    async def _generate_invoice_component(self, invoice_data: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
        """Generate professional React invoice component using Gemini"""
        
        # Create prompt for React component generation
        prompt = self._create_invoice_component_prompt(invoice_data, state)
        
        try:
            response = await self.model.generate_content_async(prompt)
            response_text = response.text
            
            # Parse the response to extract React component code and info
            component_data = self._parse_component_response(response_text)
            
            return component_data
            
        except Exception as e:
            self.logger.error(f"❌ Gemini API error: {str(e)}")
            raise Exception(f"Failed to generate React invoice component: {str(e)}")
    
    def _create_invoice_component_prompt(self, invoice_data: Dict[str, Any], state: WorkflowState) -> str:
        """Create detailed prompt for Gemini to generate HTML/CSS invoice template with placeholders"""
        
        # Extract key information
        client_name = self._safe_get(invoice_data, "client.name", "{{CLIENT_NAME}}")
        service_provider_name = self._safe_get(invoice_data, "service_provider.name", "{{PROVIDER_NAME}}")
        contract_title = invoice_data.get("contract_title", "{{SERVICE_DESCRIPTION}}")
        payment_amount = self._safe_get(invoice_data, "payment_terms.amount", "{{AMOUNT}}")
        payment_frequency = self._safe_get(invoice_data, "payment_terms.frequency", "{{FREQUENCY}}")
        workflow_id = state.get("workflow_id", "N/A")
        quality_score = state.get("quality_score", 0.0)
        
        prompt = f"""
Generate a professional, secure HTML invoice template with embedded CSS and placeholder system for dynamic data injection. Create a clean, business-appropriate design that can be safely rendered in a preview container and converted to PDF.

INVOICE DETAILS (for context):
- Service Provider: {service_provider_name}
- Client: {client_name}
- Service: {contract_title}
- Amount: ${payment_amount}
- Billing Frequency: {payment_frequency}
- Invoice Data: {invoice_data}

REQUIREMENTS:

1. Create a complete HTML template with:
   - Embedded CSS in <style> tags (NO external resources)
   - Professional header with company branding area
   - Clear invoice number and date fields using placeholders
   - Bill-to and bill-from sections
   - Itemized services table with dynamic rows
   - Payment terms and due date
   - Professional footer with payment instructions
   - NO JavaScript code (HTML/CSS only)

2. Use secure placeholder system with double curly braces:
   - {{{{PROVIDER_NAME}}}} - Service provider name
   - {{{{CLIENT_NAME}}}} - Client name  
   - {{{{INVOICE_NUMBER}}}} - Invoice number
   - {{{{INVOICE_DATE}}}} - Invoice date
   - {{{{DUE_DATE}}}} - Payment due date
   - {{{{TOTAL_AMOUNT}}}} - Total invoice amount
   - {{{{SERVICE_ITEMS}}}} - Itemized services (will be replaced with table rows)
   - {{{{PAYMENT_TERMS}}}} - Payment terms and conditions
   - {{{{PROVIDER_ADDRESS}}}} - Provider address
   - {{{{CLIENT_ADDRESS}}}} - Client address
   - {{{{STATUS}}}} - Invoice status (paid/unpaid/overdue)

3. CSS styling requirements:
   - Professional typography (Arial, Helvetica, sans-serif)
   - Clean layout with proper spacing
   - Print-friendly styles (@media print)
   - Professional color scheme (blues, grays)
   - Responsive design that works in containers
   - No external fonts or resources

4. Security considerations:
   - NO script tags or event handlers
   - NO external resource loading (images, fonts, etc.)
   - NO data attributes or custom properties
   - Clean, sanitizable HTML structure
   - Use only safe HTML elements (div, p, table, span, etc.)

5. Template structure:
   - Company header section
   - Invoice metadata (number, date, due date)
   - Billing addresses section
   - Itemized services table
   - Totals section
   - Payment terms section
   - Professional footer

RESPONSE FORMAT:
Please provide your response in this exact format:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Invoice {{{{INVOICE_NUMBER}}}}</title>
    <style>
        /* ALL CSS STYLES HERE */
    </style>
</head>
<body>
    <!-- COMPLETE HTML TEMPLATE WITH PLACEHOLDERS -->
</body>
</html>
```

Template Name: [Descriptive template name]
Template Type: [Brief description of the template style]

Generate a professional, secure HTML invoice template now.
"""
        
        return prompt
    
    def _parse_component_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response to extract HTML template and info"""
        
        import re
        
        # Extract HTML template content
        html_match = re.search(r'```html\s*(.*?)\s*```', response_text, re.DOTALL | re.IGNORECASE)
        component_code = html_match.group(1).strip() if html_match else ""
        
        # Extract template name
        template_name_match = re.search(r'Template Name:\s*(.+)', response_text, re.IGNORECASE)
        component_name = template_name_match.group(1).strip() if template_name_match else "InvoiceTemplate"
        
        # Extract template type
        template_type_match = re.search(r'Template Type:\s*(.+)', response_text, re.IGNORECASE)
        component_type = template_type_match.group(1).strip() if template_type_match else "Professional Invoice Template"
        
        # Validate extracted content
        if not component_code:
            raise ValueError("No HTML template code extracted from Gemini response")
        
        # Basic security validation - ensure no script tags or dangerous content
        if '<script' in component_code.lower() or 'javascript:' in component_code.lower():
            raise ValueError("Generated template contains potentially unsafe content")
        
        return {
            "component_code": component_code,
            "component_name": component_name,
            "component_type": component_type
        }
    
    async def _create_component_file(self, component_data: Dict[str, Any], workflow_id: str) -> str:
        """Create HTML template file in the server templates directory"""
        
        # Create templates directory in server
        templates_dir = os.path.join(os.path.dirname(__file__), "../templates/invoices")
        os.makedirs(templates_dir, exist_ok=True)
        
        # Generate filename from template name or workflow_id
        template_name = component_data["component_name"]
        # Convert to kebab-case for filename
        filename = ''.join(['-' + c.lower() if c.isupper() else c for c in template_name]).lstrip('-')
        filename = f"{filename}-{workflow_id[:8]}.html"  # Add workflow ID for uniqueness
        
        file_path = os.path.join(templates_dir, filename)
        
        # Write the template code to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(component_data["component_code"])
            
            self.logger.info(f"✅ HTML template file created: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create template file: {str(e)}")
            raise Exception(f"Failed to create template file: {str(e)}")
    
    def _safe_get(self, data: Dict[str, Any], key_path: str, default: str = "") -> str:
        """Safely get nested dictionary value using dot notation"""
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return str(current) if current is not None else default
    
    async def _retrieve_invoice_from_database(self, state: WorkflowState) -> Optional[Dict[str, Any]]:
        """Retrieve invoice data from database using invoice_id or workflow_id"""
        try:
            # Try to get invoice by database ID first
            invoice_id = state.get("invoice_id")
            if invoice_id:
                invoice_record = await self.db_service.get_invoice_by_id(invoice_id)
                if invoice_record:
                    self.logger.info(f"✅ Retrieved invoice from database: {invoice_record.invoice_number}")
                    return invoice_record.invoice_data
            
            # Try to get by workflow_id as fallback
            workflow_id = state.get("workflow_id")
            if workflow_id:
                invoice_record = await self.db_service.get_invoice_by_workflow_id(workflow_id)
                if invoice_record:
                    self.logger.info(f"✅ Retrieved invoice from database by workflow_id: {invoice_record.invoice_number}")
                    return invoice_record.invoice_data
                    
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error retrieving invoice from database: {str(e)}")
            return None
    
    async def _save_template_to_database(self, state: WorkflowState, component_data: Dict[str, Any], file_path: str) -> bool:
        """Save template information to database"""
        try:
            # Get invoice ID from state
            invoice_id = state.get("invoice_id")
            if not invoice_id:
                # Try to get from workflow_id
                workflow_id = state.get("workflow_id")
                if workflow_id:
                    invoice_record = await self.db_service.get_invoice_by_workflow_id(workflow_id)
                    if invoice_record:
                        invoice_id = invoice_record.id
                        
            if not invoice_id:
                self.logger.warning("No invoice_id found for template saving")
                return False
            
            # Create template record
            template_name = f"{component_data['component_name']}-{state.get('workflow_id', 'unknown')[:8]}"
            
            template_record = await self.db_service.create_invoice_template(
                invoice_id=invoice_id,
                template_name=template_name,
                component_name=component_data["component_name"],
                template_type=component_data["component_type"],
                file_path=file_path,
                component_code=component_data["component_code"],
                model_used="gemini-2.0-flash"
            )
            
            if template_record:
                self.logger.info(f"✅ Template saved to database: {template_name}")
                return True
            else:
                self.logger.warning("❌ Failed to save template to database")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error saving template to database: {str(e)}")
            return False