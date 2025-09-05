"""
Correction ADK Agent

Converts the legacy CorrectionAgent to Google ADK pattern
"""

from typing import Dict, Any, Optional, AsyncGenerator
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from google.adk.agents.invocation_context import InvocationContext
# Using SimpleEvent from base_adk_agent instead of Google ADK Event
from pydantic import PrivateAttr

from .base_adk_agent import BaseADKAgent, SimpleEvent
from schemas.workflow_schemas import AgentType, ProcessingStatus
from schemas.unified_invoice_schemas import UnifiedInvoiceData
from services.database_service import get_database_service
from services.contract_db_service import ContractDatabaseService

logger = logging.getLogger(__name__)


class CorrectionADKAgent(BaseADKAgent):
    """
    ADK Agent responsible for correcting and finalizing invoice JSON data after validation and human input.
    
    This agent:
    1. Takes validated data with human corrections
    2. Generates complete invoice JSON
    3. Applies business rules and formatting
    4. Produces final invoice data for downstream systems
    """
    _db_service = PrivateAttr()
    _contract_db_service = PrivateAttr()
    
    def __init__(self):
        super().__init__(
            name="correction_agent",
            agent_type=AgentType.CORRECTION,
            description="Corrects and finalizes invoice JSON data by applying business rules, formatting, and generating complete invoice structures",
            max_retries=2
        )
        self._db_service = get_database_service()
        self._contract_db_service = ContractDatabaseService()
    
    async def process_adk(self, state: Dict[str, Any], context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """
        ADK implementation for invoice correction and finalization workflow
        
        Steps:
        1. Extract unified invoice data from state
        2. Apply corrections and business rules
        3. Generate final invoice JSON
        4. Save corrected data to database
        5. Update workflow state with final results
        """
        workflow_id = state.get('workflow_id')
        yield self.create_progress_event(f"🔧 Starting ADK correction processing for workflow_id: {workflow_id}", 10.0)

        # Check if we should skip processing using centralized logic
        should_skip, reason = self.should_skip_processing(state)
        if should_skip:
            yield self.create_progress_event(f"⏸️ Skipping correction: {reason}", 50.0)
            self.set_workflow_status(
                state, 
                ProcessingStatus.NEEDS_HUMAN_INPUT.value, 
                paused=True, 
                human_input_required=True
            )
            yield self.create_success_event(
                "Correction paused - awaiting human input",
                data={
                    "human_input_required": True,
                    "correction_skipped": True,
                    "workflow_paused": True,
                    "skip_reason": reason
                }
            )
            return

        try:
            # Get latest invoice data using centralized method
            yield self.create_progress_event("Retrieving latest invoice data...", 20.0)
            current_data = self.get_latest_invoice_data(state)
            
            if not current_data:
                # Fallback to extraction method for legacy compatibility
                yield self.create_progress_event("Fallback: Extracting unified invoice data from workflow state...", 25.0)
                unified_invoice_data = None
                async for event in self._extract_unified_invoice_data_from_state(state):
                    if event.data.get("unified_invoice_data"):
                        unified_invoice_data = event.data.get("unified_invoice_data")
                    yield event
                current_data = unified_invoice_data

            if not current_data:
                error_msg = "No invoice data found in workflow state for correction"
                yield self.create_error_event("Missing data error", error_msg)
                raise ValueError(error_msg)
            
            # Ensure we have a UnifiedInvoiceData object
            from schemas.unified_invoice_schemas import UnifiedInvoiceData
            if isinstance(current_data, dict):
                unified_invoice_data = UnifiedInvoiceData(**current_data)
            else:
                unified_invoice_data = current_data

            yield self.create_progress_event("Found unified invoice data, applying corrections...", 40.0)

            # Apply corrections and generate final invoice JSON
            corrected_invoice_json = None
            async for event in self._generate_corrected_invoice_json_unified(
                unified_invoice_data=unified_invoice_data,
                state=state
            ):
                if event.data.get("corrected_invoice_json"):
                    corrected_invoice_json = event.data.get("corrected_invoice_json")
                yield event
            
            if not corrected_invoice_json:
                error_msg = "Failed to generate corrected invoice JSON"
                yield self.create_error_event("JSON generation failed", error_msg)
                raise ValueError(error_msg)

            yield self.create_progress_event("Invoice JSON generated, preparing for database save...", 60.0)

            # Update with corrected data using centralized management
            corrected_unified_data = unified_invoice_data.model_dump()
            corrected_unified_data["final_invoice_json"] = corrected_invoice_json
            self.update_invoice_data(state, corrected_unified_data, "correction_agent")
            
            # Store agent-specific result
            state["correction_result"] = {
                "corrected_invoice_json": corrected_invoice_json,
                "correction_timestamp": datetime.now().isoformat(),
                "correction_successful": True,
                "confidence_score": corrected_invoice_json.get("metadata", {}).get("confidence_score", 0.8),
                "quality_score": corrected_invoice_json.get("metadata", {}).get("quality_score", 0.85)
            }
            
            # Legacy compatibility storage
            state["final_invoice"] = corrected_invoice_json  # Store for invoice_generator_agent
            state["unified_invoice_data_final"] = unified_invoice_data.model_dump()  # Store final unified data
            yield self.create_progress_event("✅ Invoice correction completed - data prepared for database save", 70.0)

            yield self.create_progress_event("Saving corrected data to database...", 80.0)

            # Save corrected invoice data to database
            async for event in self._save_corrected_data_to_db(state, corrected_invoice_json, unified_invoice_data):
                yield event

            # Store final invoice JSON in state (legacy compatibility)
            state["final_invoice_json"] = corrected_invoice_json
            state["correction_completed"] = True
            state["correction_timestamp"] = datetime.now().isoformat()
            
            # Use centralized status management
            self.set_workflow_status(state, ProcessingStatus.SUCCESS.value)

            # Update metrics
            confidence_score = corrected_invoice_json.get("metadata", {}).get("confidence_score", 0.8)
            quality_score = corrected_invoice_json.get("metadata", {}).get("quality_score", 0.85)

            self.update_state_metrics(
                state,
                confidence=confidence_score,
                quality_score=quality_score
            )

            # Update ADK context state
            context.state.update(state)

            yield self.create_progress_event(f"✅ ADK Correction completed successfully for workflow {workflow_id}", 100.0)

            yield self.create_success_event(
                "Invoice correction and finalization completed successfully",
                data={
                    "final_invoice_generated": True,
                    "confidence_score": confidence_score,
                    "quality_score": quality_score,
                    "correction_timestamp": state["correction_timestamp"],
                    "database_saved": state.get("corrected_data_saved", False),
                    "workflow_id": workflow_id
                },
                confidence=confidence_score
            )

        except Exception as e:
            yield self.create_error_event(f"❌ ADK Correction failed for workflow {workflow_id}: {str(e)}", str(e))

            # Update state with error
            state["processing_status"] = ProcessingStatus.FAILED.value
            state["correction_completed"] = False

            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "correction",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            # Update ADK context state
            context.state.update(state)

            yield self.create_error_event("Correction processing failed", str(e))
            raise e

    async def _extract_unified_invoice_data_from_state(self, state: Dict[str, Any]) -> AsyncGenerator[SimpleEvent, None]:
        """Extract the most up-to-date unified invoice data from workflow state"""

        yield self.create_progress_event("🔍 Starting unified data extraction from state", 0.0, {"debug": True})

        # Priority order:
        # 1. Unified invoice data (new format)
        # 2. Convert from legacy formats if needed

        # Check if we have human corrections first - if so, we need to rebuild from corrected data
        human_corrected = state.get("human_input_resolved") or state.get("human_input_completed")
        yield self.create_progress_event(f"🔍 Human corrected flag: {human_corrected}", 0.0, {"debug": True})

        # Always check for unified data first, regardless of human corrections
        unified_data = state.get("unified_invoice_data")
        if unified_data:
            yield self.create_progress_event("✅ Found unified_invoice_data", 0.0, {"debug": True})
            try:
                yield self.create_progress_event("Found unified invoice data", 0.0, {"unified_invoice_data": UnifiedInvoiceData(**unified_data)})
                return
            except Exception as e:
                yield self.create_progress_event(f"Failed to load unified invoice data: {str(e)}", 0.0, {"warning": True})

        # Check for final unified data
        unified_final_data = state.get("unified_invoice_data_final")
        if unified_final_data:
            yield self.create_progress_event("✅ Found unified_invoice_data_final", 0.0, {"debug": True})
            try:
                yield self.create_progress_event("Found final unified invoice data", 0.0, {"unified_invoice_data": UnifiedInvoiceData(**unified_final_data)})
                return
            except Exception as e:
                yield self.create_progress_event(f"Failed to load final unified invoice data: {str(e)}", 0.0, {"warning": True})

        # Fallback: convert from legacy formats
        yield self.create_progress_event("No unified data found, attempting conversion from legacy formats", 0.0, {"debug": True})

        # Try to extract legacy data
        legacy_data = None

        # Debug state flags
        yield self.create_progress_event(f"🔍 State flags - human_input_resolved: {state.get('human_input_resolved')}, human_input_completed: {state.get('human_input_completed')}", 0.0, {"debug": True})

        # First check if we have human-corrected data - prioritize the clean copy
        if (state.get("human_input_resolved") or state.get("human_input_completed")):
            yield self.create_progress_event("🔄 Human input detected - using corrected data", 0.0, {"debug": True})

            # First, try to use the clean human corrected data copy
            human_corrected_data = state.get("human_corrected_data")
            if human_corrected_data and isinstance(human_corrected_data, dict):
                legacy_data = human_corrected_data.get("invoice_data")
                if legacy_data:
                    yield self.create_progress_event(f"📋 Using clean human corrected data with keys: {list(legacy_data.keys()) if isinstance(legacy_data, dict) else type(legacy_data)}", 0.0, {"debug": True})
                    if isinstance(legacy_data, dict):
                        yield self.create_progress_event(f"🔍 Clean corrected data sample: {dict(list(legacy_data.items())[:5])}", 0.0, {"debug": True})  # Show first 5 items

            # Fallback to nested invoice_data structure
            if not legacy_data:
                invoice_data = state.get("invoice_data")
                if invoice_data and isinstance(invoice_data, dict):
                    if "invoice_response" in invoice_data and "invoice_data" in invoice_data["invoice_response"]:
                        legacy_data = invoice_data["invoice_response"]["invoice_data"]
                        yield self.create_progress_event(f"📋 Using nested corrected invoice data with keys: {list(legacy_data.keys()) if isinstance(legacy_data, dict) else type(legacy_data)}", 0.0, {"debug": True})
                        if isinstance(legacy_data, dict):
                            yield self.create_progress_event(f"🔍 Nested corrected data sample: {dict(list(legacy_data.items())[:5])}", 0.0, {"debug": True})  # Show first 5 items
                    elif "invoice_data" in invoice_data:
                        legacy_data = invoice_data["invoice_data"]

        # Check validation results for processed data
        if not legacy_data:
            validation_results = state.get("validation_results")
            if validation_results and validation_results.get("is_valid"):
                # If validation passed, use the validated data
                contract_data = state.get("contract_data")
                if contract_data:
                    legacy_data = contract_data

        # Fallback to original processed data
        if not legacy_data:
            invoice_data = state.get("invoice_data")
            if invoice_data:
                if isinstance(invoice_data, dict):
                    if "invoice_response" in invoice_data and "invoice_data" in invoice_data["invoice_response"]:
                        legacy_data = invoice_data["invoice_response"]["invoice_data"]
                    else:
                        legacy_data = invoice_data

        # Convert legacy data to unified format
        if legacy_data:
            try:
                unified_data = UnifiedInvoiceData.from_legacy_format(legacy_data)
                yield self.create_progress_event("✅ Successfully converted legacy data to unified format", 0.0, {"unified_invoice_data": unified_data})
            except Exception as e:
                yield self.create_error_event(f"❌ Failed to convert legacy data to unified format: {str(e)}", str(e))

    async def _generate_corrected_invoice_json_unified(self, unified_invoice_data: UnifiedInvoiceData, state: Dict[str, Any]) -> AsyncGenerator[SimpleEvent, None]:
        """Generate the final corrected invoice JSON using unified invoice data"""

        workflow_id = state.get('workflow_id')
        contract_name = state.get('contract_name', 'Unknown Contract')
        user_id = state.get('user_id', 'Unknown User')

        # Update metadata in unified data
        unified_invoice_data.metadata.workflow_id = workflow_id
        unified_invoice_data.metadata.user_id = user_id
        unified_invoice_data.metadata.updated_at = datetime.now()

        # Set invoice dates if not set
        if not unified_invoice_data.invoice_date:
            unified_invoice_data.invoice_date = datetime.now().strftime('%Y-%m-%d')

        if not unified_invoice_data.due_date:
            unified_invoice_data.due_date = self._calculate_due_date_unified(unified_invoice_data)

        # Set contract reference
        if not unified_invoice_data.contract_reference:
            unified_invoice_data.contract_reference = contract_name

        # Update scores and metadata
        unified_invoice_data.metadata.confidence_score = self._calculate_confidence_score_unified(unified_invoice_data, state)
        unified_invoice_data.metadata.quality_score = self._calculate_quality_score_unified(unified_invoice_data, state)
        unified_invoice_data.metadata.human_input_applied = state.get("human_input_resolved", False) or state.get("human_input_completed", False)
        unified_invoice_data.metadata.validation_score = state.get("validation_results", {}).get("validation_score", 0.0)
        unified_invoice_data.metadata.processing_time_seconds = self._calculate_processing_time(state)

        # Calculate totals if not set
        if not unified_invoice_data.totals or unified_invoice_data.totals.total_amount == 0:
            unified_invoice_data.totals = self._calculate_invoice_totals_unified(unified_invoice_data)

        # Generate late fee policy if not set
        if not unified_invoice_data.late_fee_policy and unified_invoice_data.payment_terms:
            unified_invoice_data.late_fee_policy = self._generate_late_fee_policy_unified(unified_invoice_data.payment_terms)

        # Apply business rules to unified data
        async for event in self._apply_business_rules_unified(unified_invoice_data, state):
            if event.data.get("unified_invoice_data"):
                unified_invoice_data = event.data.get("unified_invoice_data")
            yield event

        # Convert to the database/correction agent format
        corrected_invoice = unified_invoice_data.to_database_format()

        yield self.create_progress_event(f"✅ Generated corrected invoice JSON using unified format for {contract_name}", 0.0, {"corrected_invoice_json": corrected_invoice})

    def _calculate_due_date_unified(self, unified_data: UnifiedInvoiceData) -> str:
        """Calculate invoice due date based on payment terms from unified data"""
        due_days = 30  # default
        if unified_data.payment_terms and unified_data.payment_terms.due_days:
            due_days = unified_data.payment_terms.due_days
        
        try:
            due_date = datetime.now() + timedelta(days=int(due_days))
            return due_date.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            # Default to 30 days
            due_date = datetime.now() + timedelta(days=30)
            return due_date.strftime('%Y-%m-%d')
    
    def _calculate_confidence_score_unified(self, unified_data: UnifiedInvoiceData, state: Dict[str, Any]) -> float:
        """Calculate confidence score for the corrected invoice using unified data"""
        base_confidence = 0.7
        
        # Boost confidence if human input was provided
        if state.get("human_input_resolved") or state.get("human_input_completed"):
            base_confidence += 0.2
        
        # Boost confidence based on validation results
        validation_results = state.get("validation_results", {})
        if validation_results.get("is_valid"):
            base_confidence += 0.1
        
        # Boost confidence based on data completeness in unified format
        completeness_score = self._calculate_data_completeness_unified(unified_data)
        base_confidence += completeness_score * 0.1
        
        return min(1.0, base_confidence)
    
    def _calculate_quality_score_unified(self, unified_data: UnifiedInvoiceData, state: Dict[str, Any]) -> float:
        """Calculate quality score based on data completeness and accuracy using unified data"""
        base_quality = 0.6
        
        # Check required fields completeness using unified format
        completeness_score = self._calculate_data_completeness_unified(unified_data)
        base_quality += completeness_score * 0.3
        
        # Boost quality if validation passed
        validation_results = state.get("validation_results", {})
        if validation_results.get("is_valid"):
            base_quality += 0.1
        
        return min(1.0, base_quality)
    
    def _calculate_data_completeness_unified(self, unified_data: UnifiedInvoiceData) -> float:
        """Calculate data completeness score for unified invoice data"""
        required_fields = [
            unified_data.client and unified_data.client.name,
            unified_data.service_provider and unified_data.service_provider.name,
            unified_data.payment_terms and unified_data.payment_terms.amount,
            unified_data.payment_terms and unified_data.payment_terms.currency
        ]
        
        completed_fields = sum(1 for field in required_fields if field)
        return completed_fields / len(required_fields)
    
    def _calculate_invoice_totals_unified(self, unified_data: UnifiedInvoiceData):
        """Calculate invoice totals from unified data"""
        from schemas.unified_invoice_schemas import UnifiedInvoiceTotals
        
        base_amount = 0.0
        if unified_data.payment_terms and unified_data.payment_terms.amount:
            base_amount = float(unified_data.payment_terms.amount)
        
        return UnifiedInvoiceTotals(
            subtotal=base_amount,
            tax_amount=0.0,
            discount_amount=0.0,
            late_fee_amount=0.0,
            total_amount=base_amount
        )
    
    def _generate_late_fee_policy_unified(self, payment_terms) -> Optional[str]:
        """Generate late fee policy text from unified payment terms"""
        if payment_terms and payment_terms.late_fee and float(payment_terms.late_fee) > 0:
            return f"Late fee of ${float(payment_terms.late_fee):.2f} applies for payments received after due date"
        return "No late fee specified"
    
    def _calculate_processing_time(self, state: Dict[str, Any]) -> float:
        """Calculate total processing time for the workflow"""
        start_time_str = state.get("started_at")
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                return (datetime.now() - start_time).total_seconds()
            except:
                pass
        return 0.0
    
    async def _apply_business_rules_unified(self, unified_data: UnifiedInvoiceData, state: Dict[str, Any]) -> AsyncGenerator[SimpleEvent, None]:
        """Apply business rules and final validations to the unified invoice data"""
        
        # Business Rule 1: Ensure minimum amount
        if unified_data.payment_terms and unified_data.payment_terms.amount:
            amount = float(unified_data.payment_terms.amount)
            if amount < 1:
                yield self.create_progress_event("Invoice amount is less than $1, setting to minimum $1", 0.0, {"warning": True})
                unified_data.payment_terms.amount = 1.0
                if unified_data.totals:
                    unified_data.totals.subtotal = 1.0
                    unified_data.totals.total_amount = 1.0
        
        # Business Rule 2: Validate currency
        if unified_data.payment_terms:
            from schemas.unified_invoice_schemas import CurrencyCode
            valid_currencies = [c.value for c in CurrencyCode]
            
            # Get currency value - handle both enum and string cases
            current_currency = unified_data.payment_terms.currency
            if hasattr(current_currency, 'value'):
                currency_str = current_currency.value
            else:
                currency_str = str(current_currency)
            
            if currency_str not in valid_currencies:
                yield self.create_progress_event(f"Invalid currency {currency_str}, defaulting to USD", 0.0, {"warning": True})
                unified_data.payment_terms.currency = CurrencyCode.USD
        
        # Business Rule 3: Ensure invoice ID uniqueness
        if unified_data.invoice_id:
            unified_data.invoice_id = f"{unified_data.invoice_id}-{int(datetime.now().timestamp())}"
            unified_data.invoice_number = unified_data.invoice_id
        
        # Business Rule 4: Update status and metadata
        from schemas.unified_invoice_schemas import InvoiceStatus
        unified_data.status = InvoiceStatus.CORRECTED
        unified_data.metadata.human_reviewed = state.get("human_input_resolved", False) or state.get("human_input_completed", False)
        
        yield self.create_progress_event("Applied business rules", 0.0, {"unified_invoice_data": unified_data})

    async def _save_corrected_data_to_db(
        self, 
        state: Dict[str, Any], 
        corrected_invoice_json: Dict[str, Any],
        unified_invoice_data: UnifiedInvoiceData
    ) -> AsyncGenerator[SimpleEvent, None]:
        """Save corrected invoice data to the database"""
        try:
            contract_id = state.get("contract_id")
            if not contract_id:
                yield self.create_progress_event("No contract_id found in state, cannot save corrected data", 0.0, {"warning": True})
                return
            
            # Check if human input was involved
            human_corrected = (
                state.get("human_input_resolved", False) or 
                state.get("human_input_completed", False) or
                state.get("corrected_by_human", False)
            )
            
            yield self.create_progress_event(f"💾 Saving corrected invoice data to database for contract {contract_id}", 0.0)
            
            # Save to database using the contract database service
            saved_data = await self._contract_db_service.save_corrected_invoice_data(
                contract_id=contract_id,
                corrected_data=corrected_invoice_json,
                corrected_by_human=human_corrected
            )
            
            # Store the database ID in state for reference
            state["extracted_invoice_data_id"] = saved_data.id
            state["corrected_data_saved"] = True
            
            yield self.create_progress_event(f"✅ Corrected invoice data saved to database with ID: {saved_data.id}", 0.0)
            
        except Exception as e:
            yield self.create_error_event(f"❌ Failed to save corrected data to database: {str(e)}", str(e))
            # Don't fail the entire process if database save fails
            state["corrected_data_save_error"] = str(e)