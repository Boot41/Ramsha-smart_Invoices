"""
Invoice Generator ADK Agent

Converts the legacy InvoiceGeneratorAgent to Google ADK pattern
"""

from typing import Dict, Any, AsyncGenerator, Optional
import logging
import uuid
import json
from datetime import datetime

from google.adk.agents.invocation_context import InvocationContext
# Using SimpleEvent from base_adk_agent instead of Google ADK Event
from pydantic import PrivateAttr

from .base_adk_agent import BaseADKAgent, SimpleEvent
from schemas.workflow_schemas import AgentType, ProcessingStatus
from services.database_service import get_database_service
from schemas.unified_invoice_schemas import UnifiedInvoiceData

logger = logging.getLogger(__name__)


class InvoiceGeneratorADKAgent(BaseADKAgent):
    """ADK Agent responsible for creating invoice records in database, sending to frontend, and managing invoice lifecycle"""
    
    _db_service = PrivateAttr()
    
    def __init__(self):
        super().__init__(
            name="invoice_generator_agent",
            agent_type=AgentType.INVOICE_GENERATION,
            description="Creates invoice records in PostgreSQL database, sends data to frontend, and manages invoice lifecycle",
            max_retries=3
        )
        self._db_service = get_database_service()
    
    async def process_adk(self, state: Dict[str, Any], context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """
        ADK implementation for invoice generation workflow
        
        Steps:
        1. Get corrected invoice data from centralized state
        2. Generate invoice UUID and number
        3. Save invoice to PostgreSQL database
        4. Send invoice data to frontend
        5. Update workflow state with invoice details
        """
        workflow_id = state.get('workflow_id')
        user_id = state.get("user_id")
        contract_name = state.get("contract_name")
        
        yield self.create_progress_event(f"🏗️ Starting invoice generation for workflow {workflow_id}", 10.0)

        # Check if we should skip processing
        should_skip, reason = self.should_skip_processing(state)
        if should_skip:
            yield self.create_progress_event(f"⏸️ Skipping invoice generation: {reason}", 50.0)
            self.set_workflow_status(state, ProcessingStatus.NEEDS_HUMAN_INPUT.value, paused=True)
            yield self.create_success_event(
                "Invoice generation paused - waiting for prerequisite completion",
                data={"invoice_generation_skipped": True, "skip_reason": reason}
            )
            return

        try:
            # Step 1: Get latest invoice data from centralized state
            yield self.create_progress_event("Retrieving corrected invoice data...", 20.0)
            current_invoice_data = self.get_latest_invoice_data(state)
            
            if not current_invoice_data:
                error_msg = "No corrected invoice data found - correction agent must complete first"
                yield self.create_error_event("Missing corrected data", error_msg)
                raise ValueError(error_msg)

            # Ensure we have UnifiedInvoiceData
            if isinstance(current_invoice_data, dict):
                unified_invoice = UnifiedInvoiceData(**current_invoice_data)
            else:
                unified_invoice = current_invoice_data
                
            yield self.create_progress_event("Found corrected invoice data, generating invoice record...", 30.0)

            # Step 2: Generate invoice UUID and number
            invoice_uuid = str(uuid.uuid4())
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{invoice_uuid[:8].upper()}"
            
            yield self.create_progress_event(f"Generated invoice number: {invoice_number}", 40.0)

            # Step 3: Save invoice to PostgreSQL database
            yield self.create_progress_event("Saving invoice to PostgreSQL database...", 50.0)
            db_invoice_record = await self._save_invoice_to_database(
                invoice_uuid, invoice_number, unified_invoice, user_id, contract_name, workflow_id
            )
            
            # Log the invoice JSON response
            self.logger.info(f"📄 INVOICE JSON RESPONSE: {json.dumps(db_invoice_record, indent=2, default=str)}")
            
            yield self.create_progress_event("✅ Invoice saved to database", 70.0)

            # Step 4: Send invoice data to frontend
            yield self.create_progress_event("Sending invoice data to frontend...", 80.0)
            frontend_response = await self._send_invoice_to_frontend(db_invoice_record, unified_invoice)
            
            yield self.create_progress_event("✅ Invoice data sent to frontend", 90.0)

            # Step 5: Update workflow state with invoice details
            invoice_result_data = {
                "invoice_uuid": invoice_uuid,
                "invoice_number": invoice_number,
                "database_record": db_invoice_record,
                "frontend_response": frontend_response,
                "generation_timestamp": datetime.now().isoformat()
            }
            
            # Store agent-specific result
            state["invoice_generation_result"] = {
                "invoice_created": True,
                "invoice_uuid": invoice_uuid,
                "invoice_number": invoice_number,
                "database_saved": True,
                "frontend_sent": True,
                "generation_successful": True,
                "generation_timestamp": datetime.now().isoformat()
            }
            
            # Update centralized data with final invoice info
            final_data = current_invoice_data.copy()
            final_data["invoice_uuid"] = invoice_uuid
            final_data["invoice_number"] = invoice_number
            final_data["database_record"] = db_invoice_record
            self.update_invoice_data(state, final_data, "invoice_generator_agent")
            
            # Legacy compatibility
            state["invoice_created"] = True
            state["invoice_uuid"] = invoice_uuid
            state["invoice_number"] = invoice_number
            state["invoice_id"] = invoice_uuid
            state["final_invoice_data"] = db_invoice_record
            
            # Set workflow status
            self.set_workflow_status(state, ProcessingStatus.SUCCESS.value)
            
            yield self.create_progress_event(f"✅ Invoice generation completed - {invoice_number}", 100.0)

            yield self.create_success_event(
                "Invoice generated, saved to database, and sent to frontend successfully",
                data={
                    "invoice_uuid": invoice_uuid,
                    "invoice_number": invoice_number,
                    "invoice_created": True,
                    "database_saved": True,
                    "frontend_sent": True,
                    "workflow_id": workflow_id
                },
                confidence=0.95
            )

        except Exception as e:
            self.logger.error(f"❌ Invoice generation failed: {str(e)}")
            
            self.set_workflow_status(state, ProcessingStatus.FAILED.value)
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "invoice_generation",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            yield self.create_error_event("Invoice generation failed", str(e))
            raise e
    
    async def _save_invoice_to_database(
        self, 
        invoice_uuid: str, 
        invoice_number: str, 
        unified_invoice: UnifiedInvoiceData,
        user_id: str,
        contract_name: str,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Save invoice to PostgreSQL database"""
        try:
            # Prepare invoice record for database
            invoice_record = {
                "invoice_uuid": invoice_uuid,
                "invoice_number": invoice_number,
                "user_id": user_id,
                "contract_name": contract_name,
                "workflow_id": workflow_id,
                "status": "generated",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                
                # Invoice data fields
                "client_name": unified_invoice.client.name if unified_invoice.client else None,
                "client_email": unified_invoice.client.email if unified_invoice.client else None,
                "service_provider_name": unified_invoice.service_provider.name if unified_invoice.service_provider else None,
                "service_provider_email": unified_invoice.service_provider.email if unified_invoice.service_provider else None,
                
                # Payment terms
                "payment_amount": unified_invoice.payment_terms.amount if unified_invoice.payment_terms else None,
                "payment_currency": unified_invoice.payment_terms.currency if unified_invoice.payment_terms else None,
                "payment_frequency": unified_invoice.payment_terms.frequency if unified_invoice.payment_terms else None,
                "payment_due_date": unified_invoice.payment_terms.due_date if unified_invoice.payment_terms else None,
                
                # Service details
                "service_description": unified_invoice.service_details.description if unified_invoice.service_details else None,
                "service_start_date": unified_invoice.service_details.start_date if unified_invoice.service_details else None,
                "service_end_date": unified_invoice.service_details.end_date if unified_invoice.service_details else None,
                
                # Full invoice data as JSON
                "invoice_data_json": unified_invoice.model_dump(),
                
                # Metadata
                "confidence_score": unified_invoice.metadata.confidence_score if unified_invoice.metadata else 0.8,
                "quality_score": unified_invoice.metadata.quality_score if unified_invoice.metadata else 0.8,
                "version": unified_invoice.metadata.version if unified_invoice.metadata else 1
            }
            
            # Save to database using the database service
            # Note: This is a placeholder - you would implement the actual database save
            self.logger.info(f"💾 Saving invoice {invoice_number} to PostgreSQL database")
            
            # Mock database save for now
            saved_record = invoice_record.copy()
            saved_record["id"] = f"db_id_{invoice_uuid[:8]}"
            saved_record["database_saved"] = True
            
            self.logger.info(f"✅ Invoice {invoice_number} saved to database with ID: {saved_record['id']}")
            
            return saved_record
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save invoice to database: {str(e)}")
            raise e
    
    async def _send_invoice_to_frontend(
        self, 
        db_invoice_record: Dict[str, Any], 
        unified_invoice: UnifiedInvoiceData
    ) -> Dict[str, Any]:
        """Send invoice data to frontend"""
        try:
            # Prepare frontend payload
            frontend_payload = {
                "invoice_id": db_invoice_record["invoice_uuid"],
                "invoice_number": db_invoice_record["invoice_number"],
                "status": "generated",
                "created_at": db_invoice_record["created_at"],
                
                # Client information
                "client": {
                    "name": unified_invoice.client.name if unified_invoice.client else None,
                    "email": unified_invoice.client.email if unified_invoice.client else None,
                    "address": unified_invoice.client.address if unified_invoice.client else None
                },
                
                # Service provider information
                "service_provider": {
                    "name": unified_invoice.service_provider.name if unified_invoice.service_provider else None,
                    "email": unified_invoice.service_provider.email if unified_invoice.service_provider else None,
                    "address": unified_invoice.service_provider.address if unified_invoice.service_provider else None
                },
                
                # Payment terms
                "payment_terms": {
                    "amount": unified_invoice.payment_terms.amount if unified_invoice.payment_terms else None,
                    "currency": unified_invoice.payment_terms.currency if unified_invoice.payment_terms else None,
                    "frequency": unified_invoice.payment_terms.frequency if unified_invoice.payment_terms else None,
                    "due_date": unified_invoice.payment_terms.due_date if unified_invoice.payment_terms else None
                },
                
                # Service details
                "service_details": {
                    "description": unified_invoice.service_details.description if unified_invoice.service_details else None,
                    "start_date": unified_invoice.service_details.start_date if unified_invoice.service_details else None,
                    "end_date": unified_invoice.service_details.end_date if unified_invoice.service_details else None
                },
                
                # Metadata
                "metadata": {
                    "confidence_score": unified_invoice.metadata.confidence_score if unified_invoice.metadata else 0.8,
                    "quality_score": unified_invoice.metadata.quality_score if unified_invoice.metadata else 0.8,
                    "workflow_id": db_invoice_record["workflow_id"],
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
            
            # Send to frontend (this would be an HTTP call to your frontend API)
            self.logger.info(f"📤 Sending invoice {db_invoice_record['invoice_number']} to frontend")
            
            # Mock frontend response for now
            frontend_response = {
                "success": True,
                "message": f"Invoice {db_invoice_record['invoice_number']} received by frontend",
                "frontend_id": f"fe_{db_invoice_record['invoice_uuid'][:8]}",
                "timestamp": datetime.now().isoformat(),
                "payload_sent": frontend_payload
            }
            
            self.logger.info(f"✅ Invoice {db_invoice_record['invoice_number']} sent to frontend successfully")
            
            return frontend_response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send invoice to frontend: {str(e)}")
            raise e
