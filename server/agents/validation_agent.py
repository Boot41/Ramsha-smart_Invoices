from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from schemas.contract_schemas import ContractInvoiceData
from services.validation_service import get_validation_service, ValidationResult
from services.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)

class ValidationAgent(BaseAgent):
    """Agent responsible for validating extracted invoice data and handling human-in-the-loop"""
    
    def __init__(self):
        super().__init__(AgentType.VALIDATION)
        self.validation_service = get_validation_service()
        self.websocket_manager = get_websocket_manager()
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """
        Validate extracted invoice data and determine if human input is needed
        
        Args:
            state: Current workflow state containing contract and invoice data
            
        Returns:
            Updated workflow state with validation results
        """
        self.logger.info(f"🔍 Starting validation for workflow_id: {state.get('workflow_id')}")
        
        user_id = state.get("user_id")
        contract_name = state.get("contract_name") 
        
        if not user_id or not contract_name:
            raise ValueError("Missing user_id or contract_name in workflow state")
        
        # Get invoice data from previous processing step
        invoice_data = state.get("invoice_data")
        contract_data = state.get("contract_data")
        
        if not invoice_data and not contract_data:
            raise ValueError("No invoice data or contract data found in workflow state - validation requires processed contract data")
        
        # Extract the actual invoice data structure
        structured_invoice_data = self._extract_invoice_data(invoice_data, contract_data)
        
        if not structured_invoice_data:
            # Create minimal validation result for empty data
            validation_result = self._create_empty_data_validation_result()
            self._update_state_with_validation_result(state, validation_result)
            return state
        
        try:
            # Convert to ContractInvoiceData if needed
            if isinstance(structured_invoice_data, dict):
                # Preprocess data to handle Pydantic validation issues
                processed_data = self._preprocess_data_for_schema(structured_invoice_data)
                try:
                    invoice_data_obj = ContractInvoiceData(**processed_data)
                except Exception as pydantic_error:
                    self.logger.warning(f"Pydantic validation failed, using raw data for custom validation: {str(pydantic_error)}")
                    # Fall back to custom validation with raw data
                    validation_result = self.validation_service.validate_raw_invoice_data(
                        raw_data=structured_invoice_data,
                        user_id=user_id,
                        contract_name=contract_name
                    )
                    self._update_state_with_validation_result(state, validation_result)
                    if validation_result.human_input_required:
                        await self._handle_human_input_requirement_realtime(state, validation_result, user_id, contract_name)
                    else:
                        state["processing_status"] = ProcessingStatus.SUCCESS.value
                        # Notify success via WebSocket
                        workflow_id = state.get('workflow_id')
                        if workflow_id:
                            await self.websocket_manager.notify_workflow_status(
                                workflow_id, 'validation_passed',
                                'Raw data validation completed successfully'
                            )
                    return state
            else:
                invoice_data_obj = structured_invoice_data
            
            # Perform validation with Pydantic object
            validation_result = self.validation_service.validate_invoice_data(
                invoice_data=invoice_data_obj,
                user_id=user_id,
                contract_name=contract_name
            )
            
            self.logger.info(f"✅ Validation completed - Valid: {validation_result.is_valid}, Score: {validation_result.validation_score:.2f}")
            
            # Update state with validation results
            self._update_state_with_validation_result(state, validation_result)
            
            # Handle human-in-the-loop if needed
            if validation_result.human_input_required:
                await self._handle_human_input_requirement_realtime(state, validation_result, user_id, contract_name)
            else:
                # Validation passed, continue to next step
                state["processing_status"] = ProcessingStatus.SUCCESS.value
                self.logger.info("✅ Validation passed - proceeding to next step")
                
                # Notify WebSocket clients of success
                workflow_id = state.get('workflow_id')
                if workflow_id:
                    await self.websocket_manager.notify_workflow_status(
                        workflow_id, 'validation_passed', 
                        'Validation completed successfully'
                    )
            
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Validation failed: {str(e)}")
            
            # Create error validation result
            error_validation_result = ValidationResult(
                is_valid=False,
                validation_score=0.0,
                issues=[],
                missing_required_fields=[],
                human_input_required=True,
                confidence_score=0.0,
                validation_timestamp=datetime.now().isoformat()
            )
            
            self._update_state_with_validation_result(state, error_validation_result)
            state["processing_status"] = ProcessingStatus.NEEDS_RETRY.value
            
            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "validation",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return state
    
    def _extract_invoice_data(self, invoice_data: Optional[Dict], contract_data: Optional[Dict]) -> Optional[Dict]:
        """Extract structured invoice data from various possible formats"""
        
        self.logger.debug(f"Extracting invoice data - invoice_data type: {type(invoice_data)}, contract_data type: {type(contract_data)}")
        
        # Try invoice_data first (preferred source)
        if invoice_data:
            # Handle multiple nested structures more robustly
            if isinstance(invoice_data, dict):
                # Try nested structures first
                for path in ["invoice_response.invoice_data", "invoice_data", "data", "structured_data"]:
                    value = invoice_data
                    for key in path.split('.'):
                        if isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            value = None
                            break
                    if value and isinstance(value, dict) and self._has_required_structure(value):
                        self.logger.debug(f"Found structured data at path: {path}")
                        return value
                
                # Check if invoice_data itself is structured
                if self._has_required_structure(invoice_data):
                    self.logger.debug("Found structured data in root invoice_data")
                    return invoice_data
        
        # Try contract_data as fallback
        if contract_data and isinstance(contract_data, dict) and self._has_required_structure(contract_data):
            self.logger.debug("Found structured data in contract_data")
            return contract_data
        
        self.logger.warning("Could not extract structured invoice data from state")
        return None
    
    def _has_required_structure(self, data: Dict) -> bool:
        """Check if data has expected invoice structure"""
        if not isinstance(data, dict):
            return False
        
        # Check for key structural elements
        required_keys = ["client", "service_provider", "payment_terms"]
        has_structure = any(key in data for key in required_keys)
        
        # Also check for any meaningful data (not all None/empty)
        has_content = any(
            value is not None and str(value).strip() 
            for value in data.values() 
            if isinstance(value, (str, int, float, dict))
        )
        
        return has_structure and has_content
    
    def _create_empty_data_validation_result(self) -> ValidationResult:
        """Create validation result for cases where no structured data is found"""
        from services.validation_service import ValidationIssue, ValidationSeverity
        
        return ValidationResult(
            is_valid=False,
            validation_score=0.0,
            issues=[
                ValidationIssue(
                    field_name="structured_data",
                    issue_type="missing_data",
                    severity=ValidationSeverity.ERROR,
                    message="No structured invoice data found - contract processing may have failed",
                    current_value=None,
                    requires_human_input=True
                )
            ],
            missing_required_fields=["client.name", "service_provider.name", "payment_terms.amount"],
            human_input_required=True,
            confidence_score=0.0,
            validation_timestamp=datetime.now().isoformat()
        )
    
    def _update_state_with_validation_result(self, state: WorkflowState, validation_result: ValidationResult):
        """Update workflow state with validation results"""
        
        # Store validation results
        state["validation_results"] = {
            "is_valid": validation_result.is_valid,
            "validation_score": validation_result.validation_score,
            "confidence_score": validation_result.confidence_score,
            "human_input_required": validation_result.human_input_required,
            "issues_count": len(validation_result.issues),
            "missing_required_fields_count": len(validation_result.missing_required_fields),
            "validation_timestamp": validation_result.validation_timestamp,
            "issues": [
                {
                    "field_name": issue.field_name,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "current_value": issue.current_value,
                    "suggested_value": issue.suggested_value,
                    "requires_human_input": issue.requires_human_input
                }
                for issue in validation_result.issues
            ],
            "missing_required_fields": validation_result.missing_required_fields
        }
        
        # Update overall workflow metrics
        state["confidence_level"] = validation_result.confidence_score
        state["quality_score"] = validation_result.validation_score
        
        # Use the base agent method to update metrics
        self.update_state_metrics(
            state,
            confidence=validation_result.confidence_score,
            quality_score=validation_result.validation_score
        )
    
    async def _handle_human_input_requirement_realtime(self, state: WorkflowState, validation_result: ValidationResult, user_id: str, contract_name: str):
        """Handle cases where human input is required via WebSocket"""
        
        workflow_id = state.get('workflow_id')
        self.logger.info(f"🙋 Human input required for {contract_name} - workflow {workflow_id}")
        
        # Create human input request
        human_input_request = self.validation_service.create_human_input_request(
            validation_result=validation_result,
            user_id=user_id,
            contract_name=contract_name
        )
        
        # Store human input request in state
        state["human_input_request"] = human_input_request
        
        # Set processing status to indicate human input is needed
        state["processing_status"] = ProcessingStatus.NEEDS_HUMAN_INPUT.value
        
        # Add to retry reasons
        if "retry_reasons" not in state:
            state["retry_reasons"] = []
        
        retry_reason = f"Human input required: {len(validation_result.missing_required_fields)} missing fields, {len([i for i in validation_result.issues if i.requires_human_input])} validation issues"
        state["retry_reasons"].append({
            "reason": retry_reason,
            "timestamp": datetime.now().isoformat(),
            "agent": "validation"
        })
        
        # Store details for potential API response
        state["validation_summary"] = {
            "status": "requires_human_input",
            "message": f"Validation found {len(validation_result.issues)} issues requiring human review",
            "missing_fields": len(validation_result.missing_required_fields),
            "validation_score": validation_result.validation_score,
            "confidence_score": validation_result.confidence_score,
            "next_action": "Provide missing information or correct validation issues"
        }
        
        self.logger.info(f"📋 Human input request created - Priority: {human_input_request.get('priority')}")
        
        # If WebSocket connections are available, set up for real-time input but don't block
        if workflow_id and self.websocket_manager.has_active_connections(workflow_id):
            self.logger.info(f"🔄 Setting up real-time human input via WebSocket...")
            
            # Store the state for when human input arrives
            state["awaiting_human_input_websocket"] = True
            
            self.logger.info(f"✅ Set awaiting_human_input_websocket = True for workflow {workflow_id}")
            
            # The WebSocket handler will call submit_human_input when data arrives
            # This will trigger re-processing through the orchestrator
            
        else:
            self.logger.info(f"🔌 No WebSocket connections - using traditional HTTP flow")
            # No WebSocket connections, use traditional HTTP flow
    
    async def handle_human_input_response(self, state: WorkflowState, human_input_data: Dict[str, Any]) -> WorkflowState:
        """
        Process human input response and update the workflow state
        
        Args:
            state: Current workflow state
            human_input_data: Data provided by human to resolve validation issues
            
        Returns:
            Updated workflow state
        """
        self.logger.info(f"🔄 Processing human input response for workflow_id: {state.get('workflow_id')}")
        
        try:
            # Extract field values from human input data structure
            field_values = human_input_data.get('field_values', human_input_data)
            self.logger.info(f"📝 Processing field values: {field_values}")
            
            # Update invoice data with human input
            updated_invoice_data = self._merge_human_input_with_invoice_data(state, field_values)
            
            # Update state with corrected data
            state["invoice_data"]["invoice_response"]["invoice_data"] = updated_invoice_data
            
            # Re-run validation on updated data
            user_id = state.get("user_id")
            contract_name = state.get("contract_name")
            
            updated_invoice_obj = ContractInvoiceData(**updated_invoice_data)
            validation_result = self.validation_service.validate_invoice_data(
                invoice_data=updated_invoice_obj,
                user_id=user_id,
                contract_name=contract_name
            )
            
            # Update state with new validation results
            self._update_state_with_validation_result(state, validation_result)
            
            if validation_result.is_valid or not validation_result.human_input_required:
                # Validation now passes, continue workflow
                state["processing_status"] = ProcessingStatus.SUCCESS.value
                state["human_input_resolved"] = True
                state["human_input_resolution_timestamp"] = datetime.now().isoformat()
                
                # Clear the human input request
                if "human_input_request" in state:
                    state["human_input_request"]["status"] = "resolved"
                
                self.logger.info("✅ Human input resolved validation issues - continuing workflow")
            else:
                # Still issues remaining
                state["processing_status"] = ProcessingStatus.NEEDS_HUMAN_INPUT.value
                self.logger.warning("⚠️ Human input provided but validation issues remain")
            
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process human input: {str(e)}")
            state["processing_status"] = ProcessingStatus.FAILED.value
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "validation",
                "error": f"Failed to process human input: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            
            return state
    
    def _merge_human_input_with_invoice_data(self, state: WorkflowState, human_input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge human-provided data with existing invoice data
        """
        
        # Get current invoice data
        current_data = self._extract_invoice_data(
            state.get("invoice_data"),
            state.get("contract_data")
        ) or {}
        
        self.logger.info(f"🔍 Current invoice data structure: {current_data}")
        
        # Create a deep copy to avoid modifying the original
        import copy
        updated_data = copy.deepcopy(current_data)
        
        # Process human input fields
        self.logger.info(f"🔄 Merging human input: {human_input_data}")
        for field_path, new_value in human_input_data.items():
            if new_value is not None and new_value != "":
                self.logger.info(f"📝 Setting field {field_path} = {new_value}")
                self._set_nested_field(updated_data, field_path, new_value)
        
        # Update timestamp
        updated_data["extracted_at"] = datetime.now()
        updated_data["human_input_applied"] = True
        updated_data["human_input_timestamp"] = datetime.now().isoformat()
        
        self.logger.info(f"✅ Updated invoice data after merge: {updated_data}")
        
        return updated_data
    
    def _set_nested_field(self, data_dict: Dict[str, Any], field_path: str, value: Any):
        """
        Set nested field value using dot notation"""
        keys = field_path.split('.')
        current = data_dict
        
        # Navigate to the parent dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _preprocess_data_for_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess data to handle common Pydantic validation issues"""
        import copy
        processed = copy.deepcopy(data)
        
        # Add default role fields if missing
        if "client" in processed and isinstance(processed["client"], dict):
            if "role" not in processed["client"]:
                processed["client"]["role"] = "client"
        
        if "service_provider" in processed and isinstance(processed["service_provider"], dict):
            if "role" not in processed["service_provider"]:
                processed["service_provider"]["role"] = "service_provider"
        
        # Handle empty string enums
        if "contract_type" in processed and processed["contract_type"] == "":
            processed["contract_type"] = None
        
        # Handle payment terms
        if "payment_terms" in processed and isinstance(processed["payment_terms"], dict):
            payment_terms = processed["payment_terms"]
            # Convert amount to Decimal string format
            if "amount" in payment_terms and payment_terms["amount"] is not None:
                payment_terms["amount"] = str(payment_terms["amount"])
        
        # Handle invalid dates
        date_fields = ["start_date", "end_date", "effective_date", "first_invoice_date", "next_invoice_date"]
        for field in date_fields:
            if field in processed and processed[field]:
                if not self._is_valid_date_string(processed[field]):
                    processed[field] = None
        
        return processed
    
    def _is_valid_date_string(self, date_str: str) -> bool:
        """Check if string can be parsed as date"""
        if not isinstance(date_str, str):
            return False
        try:
            from dateutil.parser import parse
            parse(date_str)
            return True
        except:
            return False
