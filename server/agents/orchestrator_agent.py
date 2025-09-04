from typing import Dict, Any
import logging
import asyncio
from datetime import datetime
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from services.internal_http_client import get_internal_http_client

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    """Master orchestrator agent that controls the entire workflow"""
    
    def __init__(self):
        super().__init__(AgentType.ORCHESTRATOR)
        self.decision_rules = self._initialize_decision_rules()
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Main orchestrator logic - routes to appropriate agents"""
        self.logger.info(f"🎯 Orchestrator analyzing state for workflow_id: {state.get('workflow_id')}")
        
        # Analyze current workflow state
        decision = self._analyze_workflow_state(state)
        
        # Get current agent before updating
        from_agent = state.get("current_agent", "start")
        
        # Set the current agent to the next action decided by orchestrator
        state["current_agent"] = decision["next_action"]
        state["processing_status"] = ProcessingStatus.IN_PROGRESS.value
        
        # Log decision
        self.logger.info(f"📋 Orchestrator decision: {decision['next_action']} (Reason: {decision['reason']})")
        
        # Store decision in state for workflow routing
        state["orchestrator_decision"] = decision
        
        # Log agent transition
        self.logger.info(f'🔄 Agent transition: {from_agent} -> {decision["next_action"]} for workflow {state["workflow_id"]}')
        
        return state
    
    def _analyze_workflow_state(self, state: WorkflowState) -> Dict[str, Any]:
        """Analyze current state and decide next action"""
        
        # Completed workflow check
        if (state.get("workflow_completed") and 
            not state.get("awaiting_websocket_connection")):
            return {
                "next_action": "complete_with_errors",
                "reason": "Workflow already marked as completed",
                "confidence": 0.1
            }
        
        # Decision count guard
        decision_count = state.get("orchestrator_decision_count", 0)
        if decision_count > 15:
            return {
                "next_action": "complete_with_errors", 
                "reason": f"Too many orchestrator decisions ({decision_count}) - terminating",
                "confidence": 0.1
            }
        
        # Max attempts exceeded
        if state["attempt_count"] >= state["max_attempts"]:
            return {
                "next_action": "complete_with_errors",
                "reason": f"Maximum attempts ({state['max_attempts']}) exceeded",
                "confidence": 0.1
            }
        
        # Critical errors
        if self._has_critical_errors(state):
            return {
                "next_action": "error_recovery",
                "reason": "Critical errors detected requiring recovery",
                "confidence": 0.3
            }
        
        # Retry handling
        if state["processing_status"] == ProcessingStatus.NEEDS_RETRY.value:
            if state["attempt_count"] >= state["max_attempts"]:
                return {
                    "next_action": "complete_with_errors",
                    "reason": f"Cannot retry - max attempts ({state['max_attempts']}) already reached",
                    "confidence": 0.1
                }
            state["processing_status"] = ProcessingStatus.IN_PROGRESS.value
            return {
                "next_action": "contract_processing",
                "reason": f"Retrying after error recovery (attempt {state['attempt_count'] + 1})",
                "confidence": 0.6
            }
        
        # Paused for human input - workflow should pause here
        if state["processing_status"] == "PAUSED_FOR_HUMAN_INPUT":
            return {
                "next_action": "paused_for_validation",
                "reason": "Workflow paused for human input validation - waiting for corrections",
                "confidence": 1.0
            }
        
        # Failed
        if state["processing_status"] == ProcessingStatus.FAILED.value:
            return {
                "next_action": "complete_with_errors",
                "reason": "Processing failed - ending workflow",
                "confidence": 0.1
            }
        
        # Initial state → contract processing
        if not state.get("contract_data") and state["processing_status"] in [
            ProcessingStatus.PENDING.value, 
            ProcessingStatus.IN_PROGRESS.value
        ]:
            return {
                "next_action": "contract_processing",
                "reason": "Starting workflow - contract needs processing",
                "confidence": 0.9
            }
        
        # Contract processed → validation
        if (state.get("contract_data") and state.get("invoice_data") and 
            not state.get("validation_results")):
            return {
                "next_action": "validation",
                "reason": "Contract processed - proceeding to validation",
                "confidence": 0.9
            }
        
        # Validation passed → correction
        if (state.get("validation_results") and 
            state["validation_results"].get("is_valid") and
            not state["validation_results"].get("human_input_required") and
            not state.get("correction_completed")):
            return {
                "next_action": "correction", 
                "reason": "Validation passed - generating final invoice JSON",
                "confidence": 0.9
            }
        
        # Correction completed → invoice generation
        if (state.get("correction_completed") and 
            state.get("final_invoice_json") and
            not state.get("invoice_created")):
            return {
                "next_action": "invoice_generation",
                "reason": "Correction completed - creating invoice record in database",
                "confidence": 0.9
            }
        
        # Invoice created → invoice design generation
        if (state.get("invoice_created") and 
            state.get("invoice_id") and
            not state.get("design_generation_completed")):
            return {
                "next_action": "invoice_design",
                "reason": "Invoice created - generating adaptive UI designs",
                "confidence": 0.9
            }
        
        # Design generation completed → quality assurance
        if (state.get("design_generation_completed") and 
            state.get("invoice_created") and 
            state.get("invoice_id") and
            not state.get("quality_score")):
            return {
                "next_action": "quality_assurance",
                "reason": "Design generation completed - quality check required",
                "confidence": 0.8
            }
        
        # Invoice created and quality checked → complete workflow
        if (state.get("quality_score") and 
            state.get("invoice_created") and
            state.get("invoice_id")):
            state["workflow_completed"] = True
            return {
                "next_action": "complete_success", 
                "reason": "Invoice created and quality checked - workflow completed successfully",
                "confidence": 0.95
            }
        
        # Validation needs human input
        if (state.get("validation_results") and 
            state["validation_results"].get("human_input_required")):
            
            workflow_id = state.get("workflow_id")
            if workflow_id:
                if state.get("awaiting_websocket_connection"):
                    state["awaiting_websocket_connection"] = False
                    state["workflow_completed"] = False
                return {
                    "next_action": "waiting_for_human_input",
                    "reason": "Validation agent is handling human input via WebSocket",
                    "confidence": 0.9
                }
            else:
                state["awaiting_websocket_connection"] = True
                return {
                    "next_action": "waiting_for_human_input", 
                    "reason": "Human input required but no WebSocket connections - waiting",
                    "confidence": 0.8
                }
        
        # Human input resolved → correction
        if (state.get("human_input_resolved") and 
            state["processing_status"] == ProcessingStatus.SUCCESS.value and
            state.get("validation_results") and
            state["validation_results"].get("is_valid") and
            not state.get("correction_completed")):
            return {
                "next_action": "correction",
                "reason": "Human input resolved and validation passed - generating final invoice JSON",
                "confidence": 0.9
            }
        
        # Storage completed → feedback
        if state.get("storage_result") and state["storage_result"].get("status") == "success":
            if not state.get("feedback_result"):
                return {
                    "next_action": "feedback_learning",
                    "reason": "Successful completion - capture learnings",
                    "confidence": 0.8
                }
            else:
                state["workflow_completed"] = True
                return {
                    "next_action": "complete_success",
                    "reason": "All processing completed successfully",
                    "confidence": 0.9
                }
        
        # Learning completed → workflow done
        if state.get("feedback_result"):
            state["workflow_completed"] = True
            return {
                "next_action": "complete_success", 
                "reason": "Workflow completed successfully with learning",
                "confidence": 0.9
            }
        
        # Default
        return {
            "next_action": "error_recovery",
            "reason": "Unexpected state - requires investigation",
            "confidence": 0.2
        }
    
    def _has_critical_errors(self, state: WorkflowState) -> bool:
        """Check if state has critical errors that need immediate attention"""
        errors = state.get("errors", [])
        if len(errors) > 3:
            return True
        critical_keywords = ["authentication", "permission", "database", "file_not_found"]
        for error in errors:
            error_msg = error.get("error", "").lower()
            if any(keyword in error_msg for keyword in critical_keywords):
                return True
        return False
    
    def _initialize_decision_rules(self) -> Dict[str, Any]:
        """Initialize decision-making rules for the orchestrator"""
        return {
            "max_quality_retries": 2,
            "min_confidence_threshold": 0.7,
            "critical_error_keywords": ["auth", "permission", "database", "file"],
            "quality_thresholds": {
                "excellent": 0.9,
                "good": 0.7,
                "acceptable": 0.5,
                "poor": 0.3
            }
        }


def route_from_orchestrator(state: WorkflowState) -> str:
    """LangGraph routing function for orchestrator decisions"""
    decision = state.get("orchestrator_decision", {})
    next_action = decision.get("next_action", "error_recovery")
    
    if not decision:
        logger.warning("🚨 No orchestrator decision found in state - running fallback analysis")
        from agents.orchestrator_agent import OrchestratorAgent
        temp_orchestrator = OrchestratorAgent()
        fallback_decision = temp_orchestrator._analyze_workflow_state(state)
        next_action = fallback_decision.get("next_action", "error_recovery")
        logger.info(f"🔧 Fallback routing decision: {next_action}")
    elif next_action == "error_recovery" and decision.get("reason", "").startswith("Unexpected"):
        logger.warning("🚨 Default error_recovery routing detected - using fallback analysis")
        from agents.orchestrator_agent import OrchestratorAgent
        temp_orchestrator = OrchestratorAgent()
        fallback_decision = temp_orchestrator._analyze_workflow_state(state)
        next_action = fallback_decision.get("next_action", "error_recovery")
        logger.info(f"🔧 Fallback routing decision: {next_action}")
    
    routing_map = {
        "contract_processing": "contract_processing",
        "validation": "validation", 
        "schedule_extraction": "schedule_extraction",
        "invoice_generation": "invoice_generation",
        "invoice_design": "invoice_design",
        "quality_assurance": "quality_assurance",
        # "ui_invoice_generator": "ui_invoice_generator",  # Replaced by invoice_design
        "storage_scheduling": "storage_scheduling",
        "feedback_learning": "feedback_learning",
        "error_recovery": "error_recovery",
        "complete_success": "__end__",
        "complete_with_errors": "__end__"
    }
    
    routed_node = routing_map.get(next_action, "error_recovery")
    logger.info(f"🎯 Routing to node: {routed_node}")
    
    return routed_node
