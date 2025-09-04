from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from schemas.contract_schemas import ContractInvoiceData
from schemas.unified_invoice_schemas import UnifiedInvoiceData
from services.database_service import get_database_service
from services.contract_db_service import ContractDatabaseService

logger = logging.getLogger(__name__)

class CorrectionAgent(BaseAgent):
    """
    Agent responsible for correcting and finalizing invoice JSON data after validation and human input.
    
    This agent:
    1. Takes validated data with human corrections
    2. Generates complete invoice JSON
    3. Applies business rules and formatting
    4. Produces final invoice data for downstream systems
    """
    
    def __init__(self):
        super().__init__(AgentType.CORRECTION)
        self.db_service = get_database_service()
        self.contract_db_service = ContractDatabaseService()
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """
        Process and correct validated invoice data to generate final invoice JSON
        
        Args:
            state: Current workflow state containing validated invoice data and human corrections
            
        Returns:
            Updated workflow state with final invoice JSON
        """
        workflow_id = state.get('workflow_id')
        self.logger.info(f"🔧 Starting correction processing for workflow_id: {workflow_id}")
        
        # Log that correction is starting
        if workflow_id:
            self.logger.info(f'🔧 Starting invoice correction and JSON generation for workflow {workflow_id}')
        
        try:
            # Extract unified invoice data from state
            unified_invoice_data = self._extract_unified_invoice_data_from_state(state)
            
            if not unified_invoice_data:
                raise ValueError("No unified invoice data found in workflow state for correction")
            
            # Apply corrections and generate final invoice JSON
            corrected_invoice_json = await self._generate_corrected_invoice_json_unified(
                unified_invoice_data=unified_invoice_data,
                state=state
            )
            
            # Store corrected invoice data for invoice_generator_agent to save
            state["final_invoice"] = corrected_invoice_json  # Store for invoice_generator_agent
            state["unified_invoice_data_final"] = unified_invoice_data.model_dump()  # Store final unified data
            self.logger.info("✅ Invoice correction completed - data prepared for database save")
            
            # Save corrected invoice data to database
            await self._save_corrected_data_to_db(state, corrected_invoice_json, unified_invoice_data)
            
            # Store final invoice JSON in state
            state["final_invoice_json"] = corrected_invoice_json
            state["correction_completed"] = True
            state["correction_timestamp"] = datetime.now().isoformat()
            state["processing_status"] = ProcessingStatus.SUCCESS.value
            
            # Update metrics
            self.update_state_metrics(
                state,
                confidence=corrected_invoice_json.get("metadata", {}).get("confidence_score", 0.8),
                quality_score=corrected_invoice_json.get("metadata", {}).get("quality_score", 0.85)
            )
            
            # Log successful correction
            if workflow_id:
                self.logger.info(f'✅ Invoice correction and JSON generation completed successfully for workflow {workflow_id}')
            
            self.logger.info(f"✅ Correction completed successfully for workflow {workflow_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Correction failed for workflow {workflow_id}: {str(e)}")
            
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
            
            # Log failure
            if workflow_id:
                self.logger.error(f'❌ Invoice correction failed for workflow {workflow_id}: {str(e)}')
            
            return state
    
    def _extract_unified_invoice_data_from_state(self, state: WorkflowState) -> Optional[UnifiedInvoiceData]:
        """Extract the most up-to-date unified invoice data from workflow state"""
        
        self.logger.info("🔍 Starting unified data extraction from state")
        
        # Priority order: 
        # 1. Unified invoice data (new format)
        # 2. Convert from legacy formats if needed
        
        # Check if we have human corrections first - if so, we need to rebuild from corrected data
        human_corrected = state.get("human_input_resolved") or state.get("human_input_completed")
        self.logger.info(f"🔍 Human corrected flag: {human_corrected}")
        
        # Always check for unified data first, regardless of human corrections
        unified_data = state.get("unified_invoice_data")
        if unified_data:
            self.logger.info("✅ Found unified_invoice_data")
            try:
                return UnifiedInvoiceData(**unified_data)
            except Exception as e:
                self.logger.warning(f"Failed to load unified invoice data: {str(e)}")
        
        # Check for final unified data
        unified_final_data = state.get("unified_invoice_data_final")
        if unified_final_data:
            self.logger.info("✅ Found unified_invoice_data_final")
            try:
                return UnifiedInvoiceData(**unified_final_data)
            except Exception as e:
                self.logger.warning(f"Failed to load final unified invoice data: {str(e)}")
        
        # Fallback: convert from legacy formats
        self.logger.info("No unified data found, attempting conversion from legacy formats")
        
        # Try to extract legacy data
        legacy_data = None
        
        # Debug state flags
        self.logger.info(f"🔍 State flags - human_input_resolved: {state.get('human_input_resolved')}, human_input_completed: {state.get('human_input_completed')}")
        
        # First check if we have human-corrected data - prioritize the clean copy
        if (state.get("human_input_resolved") or state.get("human_input_completed")):
            self.logger.info("🔄 Human input detected - using corrected data")
            
            # First, try to use the clean human corrected data copy
            human_corrected_data = state.get("human_corrected_data")
            if human_corrected_data and isinstance(human_corrected_data, dict):
                legacy_data = human_corrected_data.get("invoice_data")
                if legacy_data:
                    self.logger.info(f"📋 Using clean human corrected data with keys: {list(legacy_data.keys()) if isinstance(legacy_data, dict) else type(legacy_data)}")
                    if isinstance(legacy_data, dict):
                        self.logger.info(f"🔍 Clean corrected data sample: {dict(list(legacy_data.items())[:5])}")  # Show first 5 items
            
            # Fallback to nested invoice_data structure
            if not legacy_data:
                invoice_data = state.get("invoice_data")
                if invoice_data and isinstance(invoice_data, dict):
                    if "invoice_response" in invoice_data and "invoice_data" in invoice_data["invoice_response"]:
                        legacy_data = invoice_data["invoice_response"]["invoice_data"]
                        self.logger.info(f"📋 Using nested corrected invoice data with keys: {list(legacy_data.keys()) if isinstance(legacy_data, dict) else type(legacy_data)}")
                        if isinstance(legacy_data, dict):
                            self.logger.info(f"🔍 Nested corrected data sample: {dict(list(legacy_data.items())[:5])}")  # Show first 5 items
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
                self.logger.info("✅ Successfully converted legacy data to unified format")
                return unified_data
            except Exception as e:
                self.logger.error(f"❌ Failed to convert legacy data to unified format: {str(e)}")
        
        return None
    
    async def _generate_corrected_invoice_json_unified(self, unified_invoice_data: UnifiedInvoiceData, state: WorkflowState) -> Dict[str, Any]:
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
        unified_invoice_data = await self._apply_business_rules_unified(unified_invoice_data, state)
        
        # Convert to the database/correction agent format
        corrected_invoice = unified_invoice_data.to_database_format()
        
        self.logger.info(f"✅ Generated corrected invoice JSON using unified format for {contract_name}")
        
        return corrected_invoice
    
    def _format_party_data(self, party_data: Dict[str, Any], party_type: str) -> Dict[str, Any]:
        """Format party (client/service_provider) data with defaults"""
        return {
            "name": party_data.get("name", ""),
            "email": party_data.get("email", ""),
            "address": party_data.get("address", ""),
            "phone": party_data.get("phone", ""),
            "tax_id": party_data.get("tax_id", ""),
            "role": party_data.get("role", party_type)
        }
    
    def _format_payment_terms(self, payment_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Format payment terms with business logic"""
        amount = payment_terms.get("amount", 0)
        if isinstance(amount, (str, Decimal)):
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                amount = 0.0
        
        return {
            "amount": amount,
            "currency": payment_terms.get("currency", "USD"),
            "frequency": payment_terms.get("frequency", "monthly"),
            "due_days": payment_terms.get("due_days", 30),
            "late_fee": float(payment_terms.get("late_fee", 0)) if payment_terms.get("late_fee") else None,
            "discount_terms": payment_terms.get("discount_terms"),
            "payment_method": payment_terms.get("payment_method", "bank_transfer")
        }
    
    def _format_services(self, services: list) -> list:
        """Format services/items list"""
        if not services:
            return [{
                "description": "Contract services",
                "quantity": 1,
                "unit_price": 0.0,
                "total_amount": 0.0,
                "unit": "service"
            }]
        
        formatted_services = []
        for service in services:
            formatted_services.append({
                "description": service.get("description", "Service"),
                "quantity": float(service.get("quantity", 1)),
                "unit_price": float(service.get("unit_price", 0)),
                "total_amount": float(service.get("total_amount", 0)),
                "unit": service.get("unit", "service")
            })
        
        return formatted_services
    
    def _calculate_due_date_unified(self, unified_data: UnifiedInvoiceData) -> str:
        """Calculate invoice due date based on payment terms from unified data"""
        from datetime import timedelta
        
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
    
    def _generate_late_fee_policy(self, payment_terms: Dict[str, Any]) -> Optional[str]:
        """Generate late fee policy text"""
        late_fee = payment_terms.get("late_fee")
        if late_fee and float(late_fee) > 0:
            return f"Late fee of ${float(late_fee):.2f} applies for payments received after due date"
        return "No late fee specified"
    
    def _calculate_invoice_totals(self, invoice_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate invoice totals and taxes"""
        payment_terms = invoice_data.get("payment_terms", {})
        base_amount = float(payment_terms.get("amount", 0))
        
        # For now, simple totals - can be enhanced with tax calculations
        return {
            "subtotal": base_amount,
            "tax_amount": 0.0,  # Can be calculated based on business rules
            "discount_amount": 0.0,
            "total_amount": base_amount
        }
    
    def _calculate_confidence_score_unified(self, unified_data: UnifiedInvoiceData, state: WorkflowState) -> float:
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
    
    def _calculate_quality_score_unified(self, unified_data: UnifiedInvoiceData, state: WorkflowState) -> float:
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
    
    def _get_nested_field(self, data_dict: Dict[str, Any], field_path: str) -> Any:
        """Get nested field value using dot notation"""
        keys = field_path.split('.')
        value = data_dict
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _calculate_processing_time(self, state: WorkflowState) -> float:
        """Calculate total processing time for the workflow"""
        start_time_str = state.get("started_at")
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                return (datetime.now() - start_time).total_seconds()
            except:
                pass
        return 0.0
    
    async def _apply_business_rules_unified(self, unified_data: UnifiedInvoiceData, state: WorkflowState) -> UnifiedInvoiceData:
        """Apply business rules and final validations to the unified invoice data"""
        
        # Business Rule 1: Ensure minimum amount
        if unified_data.payment_terms and unified_data.payment_terms.amount:
            amount = float(unified_data.payment_terms.amount)
            if amount < 1:
                self.logger.warning("Invoice amount is less than $1, setting to minimum $1")
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
                self.logger.warning(f"Invalid currency {currency_str}, defaulting to USD")
                unified_data.payment_terms.currency = CurrencyCode.USD
        
        # Business Rule 3: Ensure invoice ID uniqueness
        if unified_data.invoice_id:
            unified_data.invoice_id = f"{unified_data.invoice_id}-{int(datetime.now().timestamp())}"
            unified_data.invoice_number = unified_data.invoice_id
        
        # Business Rule 4: Update status and metadata
        from schemas.unified_invoice_schemas import InvoiceStatus
        unified_data.status = InvoiceStatus.CORRECTED
        unified_data.metadata.human_reviewed = state.get("human_input_resolved", False) or state.get("human_input_completed", False)
        
        return unified_data
    
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
    
    async def _save_corrected_data_to_db(
        self, 
        state: WorkflowState, 
        corrected_invoice_json: Dict[str, Any],
        unified_invoice_data: UnifiedInvoiceData
    ):
        """Save corrected invoice data to the database"""
        try:
            contract_id = state.get("contract_id")
            if not contract_id:
                self.logger.warning("No contract_id found in state, cannot save corrected data")
                return
            
            # Check if human input was involved
            human_corrected = (
                state.get("human_input_resolved", False) or 
                state.get("human_input_completed", False) or
                state.get("corrected_by_human", False)
            )
            
            self.logger.info(f"💾 Saving corrected invoice data to database for contract {contract_id}")
            
            # Save to database using the contract database service
            saved_data = await self.contract_db_service.save_corrected_invoice_data(
                contract_id=contract_id,
                corrected_data=corrected_invoice_json,
                corrected_by_human=human_corrected
            )
            
            # Store the database ID in state for reference
            state["extracted_invoice_data_id"] = saved_data.id
            state["corrected_data_saved"] = True
            
            self.logger.info(f"✅ Corrected invoice data saved to database with ID: {saved_data.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save corrected data to database: {str(e)}")
            # Don't fail the entire process if database save fails
            state["corrected_data_save_error"] = str(e)
    
    # Invoice saving removed - now handled by invoice_generator_agent