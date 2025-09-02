from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime, date
from decimal import Decimal
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from schemas.contract_schemas import ContractInvoiceData
from services.websocket_manager import get_websocket_manager
from services.database_service import get_database_service

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
        self.websocket_manager = get_websocket_manager()
        self.db_service = get_database_service()
    
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
        
        # Notify WebSocket clients that correction is starting
        if workflow_id:
            await self.websocket_manager.broadcast_workflow_event(workflow_id, 'agent_started', {
                'agent': 'correction',
                'message': 'Starting invoice correction and JSON generation'
            })
        
        try:
            # Extract invoice data from state
            invoice_data = self._extract_invoice_data_from_state(state)
            
            if not invoice_data:
                raise ValueError("No invoice data found in workflow state for correction")
            
            # Apply corrections and generate final invoice JSON
            corrected_invoice_json = await self._generate_corrected_invoice_json(
                invoice_data=invoice_data,
                state=state
            )
            
            # Save invoice to database
            invoice_record = await self._save_invoice_to_database(corrected_invoice_json)
            if invoice_record:
                state["invoice_id"] = invoice_record.id
                state["final_invoice"] = corrected_invoice_json  # Store for UI agent
                self.logger.info(f"✅ Invoice saved to database with ID: {invoice_record.id}")
            else:
                self.logger.warning("⚠️ Failed to save invoice to database, but continuing with workflow")
            
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
            
            # Notify WebSocket clients of successful correction
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'correction_completed', {
                    'message': 'Invoice correction and JSON generation completed successfully',
                    'invoice_data': corrected_invoice_json,
                    'confidence_score': corrected_invoice_json.get("metadata", {}).get("confidence_score"),
                    'quality_score': corrected_invoice_json.get("metadata", {}).get("quality_score")
                })
            
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
            
            # Notify WebSocket clients of failure
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'correction_failed', {
                    'message': f'Invoice correction failed: {str(e)}',
                    'error': str(e)
                })
            
            return state
    
    def _extract_invoice_data_from_state(self, state: WorkflowState) -> Optional[Dict[str, Any]]:
        """Extract the most up-to-date invoice data from workflow state"""
        
        # Priority order: 
        # 1. Data after validation with human input
        # 2. Raw processed data from validation results
        # 3. Original contract processing output
        
        # First check if we have human-corrected data
        if "human_input_resolved" in state and state["human_input_resolved"]:
            invoice_data = state.get("invoice_data")
            if invoice_data and isinstance(invoice_data, dict):
                if "invoice_response" in invoice_data and "invoice_data" in invoice_data["invoice_response"]:
                    return invoice_data["invoice_response"]["invoice_data"]
                elif "invoice_data" in invoice_data:
                    return invoice_data["invoice_data"]
        
        # Check validation results for processed data
        validation_results = state.get("validation_results")
        if validation_results and validation_results.get("is_valid"):
            # If validation passed, use the validated data
            contract_data = state.get("contract_data")
            if contract_data:
                return contract_data
        
        # Fallback to original processed data
        invoice_data = state.get("invoice_data")
        if invoice_data:
            if isinstance(invoice_data, dict):
                if "invoice_response" in invoice_data and "invoice_data" in invoice_data["invoice_response"]:
                    return invoice_data["invoice_response"]["invoice_data"]
                return invoice_data
        
        return None
    
    async def _generate_corrected_invoice_json(self, invoice_data: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
        """Generate the final corrected invoice JSON with all business rules applied"""
        
        workflow_id = state.get('workflow_id')
        contract_name = state.get('contract_name', 'Unknown Contract')
        user_id = state.get('user_id', 'Unknown User')
        
        # Create base invoice structure
        corrected_invoice = {
            "invoice_header": {
                "invoice_id": f"INV-{workflow_id[:8]}-{datetime.now().strftime('%Y%m%d')}",
                "invoice_date": datetime.now().strftime('%Y-%m-%d'),
                "due_date": self._calculate_due_date(invoice_data),
                "contract_reference": contract_name,
                "workflow_id": workflow_id,
                "generated_at": datetime.now().isoformat()
            },
            "parties": {
                "client": self._format_party_data(invoice_data.get("client", {}), "client"),
                "service_provider": self._format_party_data(invoice_data.get("service_provider", {}), "service_provider")
            },
            "contract_details": {
                "contract_type": invoice_data.get("contract_type", "service_agreement"),
                "start_date": invoice_data.get("start_date"),
                "end_date": invoice_data.get("end_date"),
                "effective_date": invoice_data.get("effective_date")
            },
            "payment_information": self._format_payment_terms(invoice_data.get("payment_terms", {})),
            "services_and_items": self._format_services(invoice_data.get("services", [])),
            "invoice_schedule": {
                "frequency": invoice_data.get("invoice_frequency", "monthly"),
                "first_invoice_date": invoice_data.get("first_invoice_date"),
                "next_invoice_date": invoice_data.get("next_invoice_date")
            },
            "additional_terms": {
                "special_terms": invoice_data.get("special_terms"),
                "notes": invoice_data.get("notes"),
                "late_fee_policy": self._generate_late_fee_policy(invoice_data.get("payment_terms", {}))
            },
            "totals": self._calculate_invoice_totals(invoice_data),
            "metadata": {
                "generated_by": "smart_invoice_scheduler",
                "agent_version": "1.0.0",
                "user_id": user_id,
                "confidence_score": self._calculate_confidence_score(invoice_data, state),
                "quality_score": self._calculate_quality_score(invoice_data, state),
                "human_input_applied": state.get("human_input_resolved", False),
                "validation_score": state.get("validation_results", {}).get("validation_score", 0.0),
                "processing_time_seconds": self._calculate_processing_time(state)
            }
        }
        
        # Apply business rules and validations
        corrected_invoice = await self._apply_business_rules(corrected_invoice, state)
        
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
    
    def _calculate_due_date(self, invoice_data: Dict[str, Any]) -> str:
        """Calculate invoice due date based on payment terms"""
        from datetime import timedelta
        
        due_days = invoice_data.get("payment_terms", {}).get("due_days", 30)
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
    
    def _calculate_confidence_score(self, invoice_data: Dict[str, Any], state: WorkflowState) -> float:
        """Calculate confidence score for the corrected invoice"""
        base_confidence = 0.7
        
        # Boost confidence if human input was provided
        if state.get("human_input_resolved"):
            base_confidence += 0.2
        
        # Boost confidence based on validation results
        validation_results = state.get("validation_results", {})
        if validation_results.get("is_valid"):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _calculate_quality_score(self, invoice_data: Dict[str, Any], state: WorkflowState) -> float:
        """Calculate quality score based on data completeness and accuracy"""
        base_quality = 0.6
        
        # Check required fields completeness
        required_fields = ["client.name", "service_provider.name", "payment_terms.amount", "payment_terms.currency"]
        completed_fields = 0
        
        for field_path in required_fields:
            value = self._get_nested_field(invoice_data, field_path)
            if value is not None and str(value).strip():
                completed_fields += 1
        
        completeness_score = completed_fields / len(required_fields)
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
    
    async def _apply_business_rules(self, invoice_json: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
        """Apply business rules and final validations to the invoice JSON"""
        
        # Business Rule 1: Ensure minimum amount
        payment_info = invoice_json.get("payment_information", {})
        if payment_info.get("amount", 0) < 1:
            self.logger.warning("Invoice amount is less than $1, setting to minimum $1")
            invoice_json["payment_information"]["amount"] = 1.0
            invoice_json["totals"]["subtotal"] = 1.0
            invoice_json["totals"]["total_amount"] = 1.0
        
        # Business Rule 2: Validate currency
        valid_currencies = ["USD", "EUR", "INR", "GBP", "CAD", "AUD"]
        if payment_info.get("currency") not in valid_currencies:
            self.logger.warning(f"Invalid currency {payment_info.get('currency')}, defaulting to USD")
            invoice_json["payment_information"]["currency"] = "USD"
        
        # Business Rule 3: Ensure invoice ID uniqueness
        invoice_id = invoice_json["invoice_header"]["invoice_id"]
        invoice_json["invoice_header"]["invoice_id"] = f"{invoice_id}-{int(datetime.now().timestamp())}"
        
        # Business Rule 4: Add compliance notes
        invoice_json["compliance"] = {
            "generated_under": "Automated Smart Invoice Scheduler",
            "human_reviewed": state.get("human_input_resolved", False),
            "validation_passed": state.get("validation_results", {}).get("is_valid", False),
            "compliance_version": "1.0"
        }
        
        return invoice_json
    
    async def _save_invoice_to_database(self, invoice_json: Dict[str, Any]) -> Optional[Any]:
        """Save the corrected invoice to the database"""
        try:
            invoice_record = await self.db_service.create_invoice(invoice_json)
            return invoice_record
        except Exception as e:
            self.logger.error(f"❌ Failed to save invoice to database: {str(e)}")
            return None