"""
Validation ADK Agent

Converts the legacy ValidationAgent to Google ADK pattern
"""

from typing import Dict, Any, Optional, AsyncGenerator
import logging
from datetime import datetime
from enum import Enum

from google.adk.agents.invocation_context import InvocationContext
# Using SimpleEvent from base_adk_agent instead of Google ADK Event
from pydantic import PrivateAttr

from .base_adk_agent import BaseADKAgent, SimpleEvent
from schemas.workflow_schemas import AgentType, ProcessingStatus
from schemas.unified_invoice_schemas import UnifiedInvoiceData
from services.validation_service import get_validation_service, ValidationResult

logger = logging.getLogger(__name__)


class ValidationADKAgent(BaseADKAgent):
    """ADK Agent responsible for validating extracted invoice data and handling human-in-the-loop"""
    _validation_service = PrivateAttr()
    
    def __init__(self):
        super().__init__(
            name="validation_agent",
            agent_type=AgentType.VALIDATION,
            description="Validates extracted invoice data using business rules and triggers human-in-the-loop when needed",
            max_retries=2
        )
        self._validation_service = get_validation_service()
    
    async def process_adk(self, state: Dict[str, Any], context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """
        ADK implementation for invoice data validation workflow
        
        Steps:
        1. Validate required input data
        2. Convert data to unified format
        3. Run validation checks
        4. Handle human-in-the-loop if needed
        5. Update workflow state with results
        """
        workflow_id = state.get('workflow_id')
        yield self.create_progress_event(f"🔍 Starting ADK validation for workflow_id: {workflow_id}", 5.0)

        yield self.create_progress_event("Starting invoice data validation...", 10.0)

        # Extract required parameters
        user_id = state.get("user_id")
        contract_name = state.get("contract_name")

        if not user_id or not contract_name:
            error_msg = "Missing user_id or contract_name in workflow state"
            yield self.create_error_event("Validation input error", error_msg)
            raise ValueError(error_msg)

        # Get invoice data from previous processing step
        invoice_data = state.get("invoice_data")
        contract_data = state.get("contract_data")

        if not invoice_data and not contract_data:
            error_msg = "No invoice data or contract data found in workflow state - validation requires processed contract data"
            yield self.create_error_event("Missing data error", error_msg)
            raise ValueError(error_msg)

        yield self.create_progress_event("Input validation completed, converting to unified format...", 20.0)

        # Convert to unified format
        unified_invoice_data = None
        async for event in self._convert_to_unified_format(invoice_data, contract_data):
            if event.data.get("unified_invoice_data"):
                unified_invoice_data = event.data.get("unified_invoice_data")
            yield event

        if not unified_invoice_data:
            # Create minimal validation result for empty data
            yield self.create_progress_event("No structured data found, creating fallback validation...", 30.0)
            validation_result = self._create_empty_data_validation_result()
            self._update_state_with_validation_result(state, validation_result)
            context.state.update(state)

            yield self.create_error_event(
                "No structured data found",
                "Contract processing may have failed - no structured data to validate",
                data={"validation_result": validation_result.model_dump()}
            )
            return

        try:
            yield self.create_progress_event("Running validation checks...", 50.0)

            # Perform validation with unified data
            validation_result = self._validation_service.validate_unified_invoice_data(
                invoice_data=unified_invoice_data,
                user_id=user_id,
                contract_name=contract_name
            )

            yield self.create_progress_event(f"✅ Validation completed - Valid: {validation_result.is_valid}, Score: {validation_result.validation_score:.2f}", 80.0)

            yield self.create_progress_event(
                f"Validation completed - Valid: {validation_result.is_valid}",
                80.0,
                data={
                    "is_valid": validation_result.is_valid,
                    "validation_score": validation_result.validation_score,
                    "issues_count": len(validation_result.issues)
                }
            )

            # Store agent-specific result
            state["validation_result"] = {
                "validation_result": {
                    "is_valid": validation_result.is_valid,
                    "validation_score": validation_result.validation_score,
                    "confidence_score": validation_result.confidence_score,
                    "human_input_required": validation_result.human_input_required,
                    "issues": [
                        {
                            "field_name": issue.field_name,
                            "issue_type": issue.issue_type,
                            "severity": issue.severity.value,
                            "message": issue.message,
                            "current_value": issue.current_value,
                            "suggested_value": issue.suggested_value,
                            "requires_human_input": issue.requires_human_input
                        } for issue in validation_result.issues
                    ],
                    "missing_required_fields": validation_result.missing_required_fields,
                    "validation_timestamp": validation_result.validation_timestamp
                },
                "is_valid": validation_result.is_valid,
                "validation_score": validation_result.validation_score,
                "confidence_score": validation_result.confidence_score,
                "human_input_required": validation_result.human_input_required,
                "issues_count": len(validation_result.issues),
                "missing_fields_count": len(validation_result.missing_required_fields),
                "validation_timestamp": validation_result.validation_timestamp
            }
            
            # Update state with validation results (legacy compatibility)
            self._update_state_with_validation_result(state, validation_result)

            # Handle human-in-the-loop if needed
            if validation_result.human_input_required:
                yield self.create_progress_event("Human input required - setting up validation pause...", 90.0)
                
                # Use centralized status management
                self.set_workflow_status(
                    state, 
                    ProcessingStatus.NEEDS_HUMAN_INPUT, 
                    paused=True, 
                    human_input_required=True, 
                    correction_pending=True
                )
                
                async for event in self._handle_human_input_requirement_realtime(state, validation_result, user_id, contract_name):
                    yield event

                yield self.create_success_event(
                    "Validation completed - human input required",
                    data={
                        "human_input_required": True,
                        "validation_score": validation_result.validation_score,
                        "issues_count": len(validation_result.issues),
                        "missing_fields_count": len(validation_result.missing_required_fields),
                        "workflow_paused": True
                    },
                    confidence=validation_result.confidence_score
                )
            else:
                # Validation passed, continue to next step
                self.set_workflow_status(state, ProcessingStatus.SUCCESS)
                yield self.create_progress_event("✅ Validation passed - proceeding to next step", 95.0)

                workflow_id = state.get('workflow_id')
                if workflow_id:
                    yield self.create_progress_event(f'✅ Validation completed successfully for workflow {workflow_id}', 100.0)

                yield self.create_success_event(
                    "Validation completed successfully - no human input required",
                    data={
                        "human_input_required": False,
                        "validation_score": validation_result.validation_score,
                        "confidence_score": validation_result.confidence_score,
                        "issues_resolved": len(validation_result.issues) == 0
                    },
                    confidence=validation_result.confidence_score
                )

            # Update ADK context state
            context.state.update(state)

        except Exception as e:
            yield self.create_error_event(f"❌ Validation failed: {str(e)}", str(e))

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
            state["processing_status"] = ProcessingStatus.NEEDS_RETRY

            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "validation",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            # Update ADK context state
            context.state.update(state)

            yield self.create_error_event("Validation processing failed", str(e))
            raise e

    async def _convert_to_unified_format(self, invoice_data: Optional[Dict], contract_data: Optional[Dict]) -> AsyncGenerator[SimpleEvent, None]:
        """Convert various invoice data formats to unified format"""

        yield self.create_progress_event(f"Converting to unified format - invoice_data type: {type(invoice_data)}, contract_data type: {type(contract_data)}", 0.0, {"debug": True})

        # Try to find data to convert
        source_data = None

        # Try invoice_data first (preferred source)
        if invoice_data:
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
                        yield self.create_progress_event(f"Found structured data at path: {path}", 0.0, {"debug": True})
                        source_data = value
                        break

                # Check if invoice_data itself is structured
                if not source_data and self._has_required_structure(invoice_data):
                    yield self.create_progress_event("Found structured data in root invoice_data", 0.0, {"debug": True})
                    source_data = invoice_data

        # Try contract_data as fallback
        if not source_data and contract_data and isinstance(contract_data, dict) and self._has_required_structure(contract_data):
            yield self.create_progress_event("Found structured data in contract_data", 0.0, {"debug": True})
            source_data = contract_data

        if not source_data:
            yield self.create_progress_event("Could not find structured invoice data to convert", 0.0, {"warning": True})
            return

        try:
            # Convert to unified format
            unified_data = UnifiedInvoiceData.from_legacy_format(source_data)
            yield self.create_progress_event("✅ Successfully converted to unified invoice format", 0.0, {"unified_invoice_data": unified_data})
        except Exception as e:
            yield self.create_error_event(f"❌ Failed to convert to unified format: {str(e)}", str(e))

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

    def _apply_field_values_to_invoice_data(self, unified_invoice_data: UnifiedInvoiceData, field_values: Dict[str, Any]) -> UnifiedInvoiceData:
        """
        Apply structured field values to unified invoice data
        
        Args:
            unified_invoice_data: Current unified invoice data
            field_values: Dictionary of field paths and values to update
            
        Returns:
            Updated UnifiedInvoiceData instance
        """
        try:
            logger.info(f"📝 Applying {len(field_values)} field updates to invoice data")
            
            # Convert any enum values to their string representation
            processed_field_values = {}
            for key, value in field_values.items():
                if isinstance(value, Enum):
                    processed_field_values[key] = value.value
                else:
                    processed_field_values[key] = value
            
            # Apply the corrections using the unified format's built-in method
            corrected_unified_data = unified_invoice_data.apply_manual_corrections(processed_field_values)
            
            logger.info(f"✅ Successfully applied field corrections to invoice data")
            return corrected_unified_data
            
        except Exception as e:
            logger.error(f"❌ Error applying field values to invoice data: {str(e)}")
            raise e

    
    def _update_state_with_validation_result(self, state: Dict[str, Any], validation_result: ValidationResult):
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

    async def _handle_human_input_requirement_realtime(self, state: Dict[str, Any], validation_result: ValidationResult, user_id: str, contract_name: str) -> AsyncGenerator[SimpleEvent, None]:
        """Handle cases where human input is required via HTTP"""

        workflow_id = state.get('workflow_id')
        yield self.create_progress_event(f"🙋 Human input required for {contract_name} - workflow {workflow_id}", 0.0)

        # Create human input request
        human_input_request = self._validation_service.create_human_input_request(
            validation_result=validation_result,
            user_id=user_id,
            contract_name=contract_name
        )

        # Store human input request in state
        state["human_input_request"] = human_input_request

        # Create structured field requirements for specific updates
        required_fields = []
        
        # Add missing required fields
        for field_name in validation_result.missing_required_fields:
            required_fields.append({
                "field_name": field_name,
                "field_type": "missing",
                "current_value": None,
                "description": f"Missing required field: {field_name}",
                "required": True
            })
        
        # Add validation issues that require human input
        for issue in validation_result.issues:
            if issue.requires_human_input:
                required_fields.append({
                    "field_name": issue.field_name,
                    "field_type": "validation_issue",
                    "current_value": issue.current_value,
                    "suggested_value": issue.suggested_value,
                    "description": issue.message,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity.value,
                    "required": issue.severity.value in ["ERROR", "CRITICAL"]
                })
        
        # Store structured field requirements in state
        state["required_field_updates"] = required_fields
        
        yield self.create_progress_event(f"📝 Identified {len(required_fields)} fields requiring human input", 0.0)

        # Set processing status to indicate human input is needed
        state["processing_status"] = ProcessingStatus.NEEDS_HUMAN_INPUT

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
            "required_field_count": len(required_fields),
            "next_action": "Update the specified fields using field_values key-value pairs",
            "input_format": "Provide corrections as: {'field_values': {'field.name': 'new_value', ...}}"
        }

        yield self.create_progress_event(f"📋 Human input request created - Priority: {human_input_request.get('priority')}", 0.0)

        # Set up for manual human input handling - workflow will pause here
        if workflow_id:
            yield self.create_progress_event(f"⏸️ Pausing workflow for manual human input validation...", 0.0)

            # Store the state and pause workflow
            state["awaiting_human_input"] = True
            state["processing_status"] = "PAUSED_FOR_HUMAN_INPUT"
            state["workflow_paused"] = True
            state["pause_reason"] = "validation_requires_human_input"

            # Protect workflow from cleanup
            from services.orchestrator_service import get_orchestrator_service
            orchestrator_service = get_orchestrator_service()
            orchestrator_service.ensure_workflow_persists(workflow_id)

            yield self.create_progress_event(f"📝 Human input required for {contract_name}. Use GET /api/v1/validation/requirements/{workflow_id} to see what needs correction.", 0.0)

    async def handle_human_input_response(self, state: Dict[str, Any], context: InvocationContext, human_input_data: Dict[str, Any]) -> AsyncGenerator[SimpleEvent, None]:
        """
        ADK implementation for processing human input response and updating workflow state

        Args:
            state: Current workflow state
            context: ADK InvocationContext
            human_input_data: Dictionary containing 'field_values' with field corrections
        """
        workflow_id = state.get('workflow_id')
        yield self.create_progress_event(f"🔄 Processing human input response for workflow_id: {workflow_id}", 10.0)

        try:
            # Extract field values from human input data
            if isinstance(human_input_data, dict):
                field_values = human_input_data.get('field_values', {})
            else:
                error_msg = "Invalid human input format - expected dictionary with 'field_values'"
                yield self.create_error_event("Invalid input format", error_msg)
                raise ValueError(error_msg)
            
            if not field_values:
                error_msg = "No field values provided in human input"
                yield self.create_error_event("Missing field values", error_msg)
                raise ValueError(error_msg)
            
            yield self.create_progress_event(f"📝 Processing {len(field_values)} field corrections", 20.0)
            yield self.create_progress_event("Applying corrections...", 40.0)

            # Get current unified invoice data
            current_unified_data = state.get("unified_invoice_data")
            if current_unified_data:
                unified_invoice = UnifiedInvoiceData(**current_unified_data)
            else:
                # Fallback: convert from legacy format
                unified_invoice = None
                async for event in self._convert_to_unified_format(
                    state.get("invoice_data"),
                    state.get("contract_data")
                ):
                    if event.data.get("unified_invoice_data"):
                        unified_invoice = event.data.get("unified_invoice_data")
                    yield event

            if not unified_invoice:
                error_msg = "No invoice data found to apply corrections to"
                yield self.create_error_event("Correction failed", error_msg)
                raise ValueError(error_msg)

            # Apply field corrections using the helper function
            corrected_unified_data = self._apply_field_values_to_invoice_data(unified_invoice, field_values)

            # Update state with corrected unified data
            state["unified_invoice_data"] = corrected_unified_data.model_dump()

            # Also update legacy formats for backward compatibility
            state["invoice_data"] = {
                "invoice_response": {
                    "invoice_data": corrected_unified_data.to_legacy_contract_invoice_data()
                }
            }

            yield self.create_progress_event("Re-running validation on corrected data...", 70.0)

            # Re-run validation on updated data
            user_id = state.get("user_id")
            contract_name = state.get("contract_name")

            validation_result = self._validation_service.validate_unified_invoice_data(
                invoice_data=corrected_unified_data,
                user_id=user_id,
                contract_name=contract_name
            )

            # Update state with new validation results
            self._update_state_with_validation_result(state, validation_result)

            if validation_result.is_valid or not validation_result.human_input_required:
                # Validation now passes, continue workflow
                state["processing_status"] = ProcessingStatus.SUCCESS
                state["human_input_resolved"] = True
                state["human_input_resolution_timestamp"] = datetime.now().isoformat()

                # Clear the human input request
                if "human_input_request" in state:
                    state["human_input_request"]["status"] = "resolved"

                yield self.create_progress_event("✅ Human input resolved validation issues - continuing workflow", 90.0)

                yield self.create_success_event(
                    "Human input resolved validation issues successfully",
                    data={
                        "validation_score": validation_result.validation_score,
                        "confidence_score": validation_result.confidence_score,
                        "human_input_resolved": True,
                        "workflow_can_continue": True
                    },
                    confidence=validation_result.confidence_score
                )
            else:
                # Still issues remaining
                state["processing_status"] = ProcessingStatus.NEEDS_HUMAN_INPUT
                yield self.create_progress_event("⚠️ Human input provided but validation issues remain", 90.0, {"warning": True})

                yield self.create_progress_event(
                    "Human input processed but validation issues remain",
                    100.0,
                    data={
                        "validation_score": validation_result.validation_score,
                        "remaining_issues": len(validation_result.issues),
                        "still_needs_human_input": True
                    }
                )

            # Update ADK context state
            context.state.update(state)

        except Exception as e:
            yield self.create_error_event(f"❌ Failed to process human input: {str(e)}", str(e))
            state["processing_status"] = ProcessingStatus.FAILED

            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "validation",
                "error": f"Failed to process human input: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

            # Update ADK context state
            context.state.update(state)

            yield self.create_error_event("Human input processing failed", str(e))
            raise e