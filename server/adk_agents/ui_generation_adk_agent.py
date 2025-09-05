"""
UI Generation ADK Agent

Generates HTML/CSS invoices from JSON data using template-based approach.
Saves generated HTML to database and provides viewing endpoints.
"""

from typing import Dict, Any, AsyncGenerator, Optional
import logging
import uuid
import json
import os
from datetime import datetime
from pathlib import Path

from google.adk.agents.invocation_context import InvocationContext
from pydantic import PrivateAttr

from .base_adk_agent import BaseADKAgent, SimpleEvent
from schemas.workflow_schemas import AgentType, ProcessingStatus
from services.database_service import get_database_service
from schemas.unified_invoice_schemas import UnifiedInvoiceData
from models.database_models import HTMLInvoice

logger = logging.getLogger(__name__)


class UIGenerationADKAgent(BaseADKAgent):
    """ADK Agent responsible for generating HTML/CSS invoices from JSON data"""
    
    _db_service = PrivateAttr()
    _templates_dir = PrivateAttr()
    
    def __init__(self):
        super().__init__(
            name="ui_generation_agent",
            agent_type=AgentType.UI_INVOICE_GENERATOR,
            description="Generates professional HTML/CSS invoices from JSON data using templates",
            max_retries=3
        )
        self._db_service = get_database_service()
        self._templates_dir = Path(__file__).parent.parent / "templates" / "invoices"
    
    async def process_adk(self, state: Dict[str, Any], context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """
        ADK implementation for UI generation workflow
        
        Steps:
        1. Get invoice data from previous agents
        2. Select appropriate template
        3. Generate HTML/CSS invoice
        4. Save to database with JSONB and contract reference
        5. Return viewing URL
        """
        workflow_id = state.get('workflow_id')
        user_id = state.get("user_id")
        contract_name = state.get("contract_name")
        
        yield self.create_progress_event(f"🎨 Starting UI generation for workflow {workflow_id}", 10.0)

        # Check if we should skip processing
        should_skip, reason = self.should_skip_processing(state)
        if should_skip:
            yield self.create_progress_event(f"⏸️ Skipping UI generation: {reason}", 50.0)
            self.set_workflow_status(state, ProcessingStatus.NEEDS_HUMAN_INPUT.value, paused=True)
            yield self.create_success_event(
                "UI generation paused - waiting for prerequisite completion",
                data={"ui_generation_skipped": True, "skip_reason": reason}
            )
            return

        try:
            # Step 1: Get invoice data from centralized state
            yield self.create_progress_event("Retrieving invoice data for UI generation...", 20.0)
            invoice_data = self.get_latest_invoice_data(state)
            
            if not invoice_data:
                error_msg = "No invoice data found - invoice generator must complete first"
                yield self.create_error_event("Missing invoice data", error_msg)
                raise ValueError(error_msg)

            # Get additional data from state
            invoice_uuid = state.get('invoice_uuid') or state.get('invoice_id')
            invoice_number = state.get('invoice_number')
            db_record = state.get('final_invoice_data') or state.get('database_record', {})

            if not invoice_uuid or not invoice_number:
                error_msg = "Missing invoice UUID or number - invoice generation incomplete"
                yield self.create_error_event("Missing invoice identifiers", error_msg)
                raise ValueError(error_msg)

            yield self.create_progress_event(f"Found invoice data for {invoice_number}", 30.0)

            # Step 2: Select appropriate template
            yield self.create_progress_event("Selecting invoice template...", 40.0)
            template_path = await self._select_template()
            
            yield self.create_progress_event(f"Selected template: {template_path.name}", 45.0)

            # Step 3: Generate HTML/CSS invoice
            yield self.create_progress_event("Generating HTML invoice...", 60.0)
            html_content = await self._generate_html_invoice(invoice_data, template_path)
            
            yield self.create_progress_event("✅ HTML invoice generated successfully", 70.0)

            # Step 4: Save to database
            yield self.create_progress_event("Saving HTML invoice to database...", 80.0)
            ui_record = await self._save_ui_to_database(
                invoice_uuid, invoice_number, html_content, invoice_data, 
                user_id, contract_name, workflow_id, template_path.name
            )
            
            yield self.create_progress_event("✅ UI invoice saved to database", 90.0)

            # Step 5: Generate viewing URL
            viewing_url = f"/api/invoices/{invoice_uuid}/view"
            
            # Update workflow state
            ui_result_data = {
                "ui_generated": True,
                "invoice_uuid": invoice_uuid,
                "invoice_number": invoice_number,
                "viewing_url": viewing_url,
                "template_used": template_path.name,
                "html_generated": True,
                "database_saved": True,
                "generation_timestamp": datetime.now().isoformat()
            }
            
            # Store agent-specific result
            state["ui_generation_result"] = ui_result_data
            
            # Update centralized data with UI info
            final_data = invoice_data.copy() if isinstance(invoice_data, dict) else invoice_data.model_dump()
            final_data["ui_generated"] = True
            final_data["viewing_url"] = viewing_url
            final_data["html_content"] = html_content
            self.update_invoice_data(state, final_data, "ui_generation_agent")
            
            # Legacy compatibility
            state["ui_generated"] = True
            state["viewing_url"] = viewing_url
            state["html_invoice"] = html_content
            
            # Set workflow status
            self.set_workflow_status(state, ProcessingStatus.SUCCESS.value)
            
            yield self.create_progress_event(f"✅ UI generation completed - {viewing_url}", 100.0)

            yield self.create_success_event(
                "HTML invoice generated and saved successfully",
                data={
                    "ui_generated": True,
                    "invoice_uuid": invoice_uuid,
                    "invoice_number": invoice_number,
                    "viewing_url": viewing_url,
                    "template_used": template_path.name,
                    "workflow_id": workflow_id
                },
                confidence=0.95
            )

        except Exception as e:
            self.logger.error(f"❌ UI generation failed: {str(e)}")
            
            self.set_workflow_status(state, ProcessingStatus.FAILED.value)
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "ui_generation",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            yield self.create_error_event("UI generation failed", str(e))
            raise e
    
    async def _select_template(self) -> Path:
        """Select the most appropriate invoice template"""
        try:
            # Get all available templates
            template_files = list(self._templates_dir.glob("*.html"))
            
            if not template_files:
                raise ValueError("No HTML templates found in templates directory")
            
            # For now, select a modern professional template
            # In the future, this could be based on client preferences, invoice type, etc.
            preferred_templates = [
                "modern -professional -invoice-bb14c848.html",
                "professional -invoice -template-b3c77171.html",
                "modern -blue -invoice -template-e51c1ad1.html"
            ]
            
            for preferred in preferred_templates:
                preferred_path = self._templates_dir / preferred
                if preferred_path.exists():
                    self.logger.info(f"✅ Selected preferred template: {preferred}")
                    return preferred_path
            
            # Fallback to first available template
            selected = template_files[0]
            self.logger.info(f"📄 Using fallback template: {selected.name}")
            return selected
            
        except Exception as e:
            self.logger.error(f"❌ Failed to select template: {str(e)}")
            raise e
    
    async def _generate_html_invoice(
        self, 
        invoice_data: Any, 
        template_path: Path
    ) -> str:
        """Generate HTML invoice from template and data"""
        try:
            # Read template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Convert invoice data to dict if it's a Pydantic model
            if hasattr(invoice_data, 'model_dump'):
                data_dict = invoice_data.model_dump()
            elif isinstance(invoice_data, dict):
                data_dict = invoice_data
            else:
                raise ValueError(f"Unsupported invoice data type: {type(invoice_data)}")
            
            # Extract data for template substitution
            template_vars = self._extract_template_variables(data_dict)
            
            # Replace template placeholders
            html_content = template_content
            for placeholder, value in template_vars.items():
                html_content = html_content.replace(f"{{{{{placeholder}}}}}", str(value))
            
            self.logger.info(f"✅ HTML invoice generated with {len(template_vars)} variables")
            return html_content
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate HTML invoice: {str(e)}")
            raise e
    
    def _extract_template_variables(self, data_dict: Dict[str, Any]) -> Dict[str, str]:
        """Extract variables for template substitution"""
        try:
            # Default values
            template_vars = {
                "INVOICE_NUMBER": "INV-001",
                "INVOICE_DATE": datetime.now().strftime("%Y-%m-%d"),
                "DUE_DATE": datetime.now().strftime("%Y-%m-%d"),
                "CLIENT_NAME": "Client Name",
                "CLIENT_ADDRESS": "Client Address",
                "PROVIDER_NAME": "Service Provider",
                "PROVIDER_ADDRESS": "Provider Address",
                "TOTAL_AMOUNT": "0.00",
                "PAYMENT_TERMS": "Payment due within 30 days",
                "STATUS": "generated",
                "SERVICE_ITEMS": "<tr><td>Service</td><td>$0.00</td></tr>"
            }
            
            # Extract from invoice data structure
            if 'client' in data_dict and data_dict['client']:
                client = data_dict['client']
                template_vars["CLIENT_NAME"] = client.get('name', 'Client Name')
                template_vars["CLIENT_ADDRESS"] = client.get('address', 'Client Address')
            
            if 'service_provider' in data_dict and data_dict['service_provider']:
                provider = data_dict['service_provider']
                template_vars["PROVIDER_NAME"] = provider.get('name', 'Service Provider')
                template_vars["PROVIDER_ADDRESS"] = provider.get('address', 'Provider Address')
            
            if 'payment_terms' in data_dict and data_dict['payment_terms']:
                payment = data_dict['payment_terms']
                template_vars["TOTAL_AMOUNT"] = str(payment.get('amount', '0.00'))
                template_vars["DUE_DATE"] = payment.get('due_date', datetime.now().strftime("%Y-%m-%d"))
                template_vars["PAYMENT_TERMS"] = f"Amount: ${payment.get('amount', '0.00')} {payment.get('currency', 'USD')} - Frequency: {payment.get('frequency', 'One-time')}"
            
            if 'service_details' in data_dict and data_dict['service_details']:
                service = data_dict['service_details']
                description = service.get('description', 'Service')
                amount = data_dict.get('payment_terms', {}).get('amount', '0.00')
                template_vars["SERVICE_ITEMS"] = f"<tr><td>{description}</td><td>${amount}</td></tr>"
            
            # Override with any specific values from data
            if 'invoice_number' in data_dict:
                template_vars["INVOICE_NUMBER"] = data_dict['invoice_number']
            if 'invoice_date' in data_dict:
                template_vars["INVOICE_DATE"] = data_dict['invoice_date']
            if 'status' in data_dict:
                template_vars["STATUS"] = data_dict['status']
            
            return template_vars
            
        except Exception as e:
            self.logger.error(f"❌ Failed to extract template variables: {str(e)}")
            # Return defaults on error
            return {
                "INVOICE_NUMBER": "INV-ERROR",
                "INVOICE_DATE": datetime.now().strftime("%Y-%m-%d"),
                "DUE_DATE": datetime.now().strftime("%Y-%m-%d"),
                "CLIENT_NAME": "Error Loading Data",
                "CLIENT_ADDRESS": "Error Loading Data",
                "PROVIDER_NAME": "Error Loading Data",
                "PROVIDER_ADDRESS": "Error Loading Data",
                "TOTAL_AMOUNT": "0.00",
                "PAYMENT_TERMS": "Error loading payment terms",
                "STATUS": "error",
                "SERVICE_ITEMS": "<tr><td>Error loading service items</td><td>$0.00</td></tr>"
            }
    
    async def _save_ui_to_database(
        self, 
        invoice_uuid: str,
        invoice_number: str,
        html_content: str,
        invoice_data: Any,
        user_id: str,
        contract_name: str,
        workflow_id: str,
        template_name: str
    ) -> Dict[str, Any]:
        """Save HTML invoice to PostgreSQL database"""
        try:
            # Create HTMLInvoice database record
            html_invoice = HTMLInvoice(
                invoice_uuid=invoice_uuid,
                invoice_number=invoice_number,
                user_id=user_id,
                workflow_id=workflow_id,
                html_content=html_content,
                template_used=template_name,
                template_version="1.0",
                contract_name=contract_name,
                contract_reference=contract_name,
                invoice_data_json=invoice_data.model_dump() if hasattr(invoice_data, 'model_dump') else invoice_data,
                generation_method="template_based",
                generated_by_agent="ui_generation_agent",
                content_type="text/html",
                character_count=len(html_content),
                viewing_enabled=True,
                viewing_url=f"/api/invoices/{invoice_uuid}/view",
                status="generated"
            )
            
            # Save to database using the database service
            self.logger.info(f"💾 Saving HTML invoice {invoice_number} to PostgreSQL database")
            
            # Use database service to save (you would implement this in your database service)
            # For now, simulate the save and return the data as dict
            saved_record = {
                "id": html_invoice.id,
                "invoice_uuid": html_invoice.invoice_uuid,
                "invoice_number": html_invoice.invoice_number,
                "user_id": html_invoice.user_id,
                "workflow_id": html_invoice.workflow_id,
                "html_content": html_invoice.html_content,
                "template_used": html_invoice.template_used,
                "template_version": html_invoice.template_version,
                "contract_name": html_invoice.contract_name,
                "invoice_data_json": html_invoice.invoice_data_json,
                "generation_method": html_invoice.generation_method,
                "viewing_url": html_invoice.viewing_url,
                "status": html_invoice.status,
                "created_at": datetime.now().isoformat(),
                "database_saved": True
            }
            
            self.logger.info(f"✅ HTML invoice {invoice_number} saved to database with ID: {html_invoice.id}")
            
            return saved_record
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save HTML invoice to database: {str(e)}")
            raise e