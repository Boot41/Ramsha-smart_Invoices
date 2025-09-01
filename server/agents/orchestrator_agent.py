from typing import Dict, Any
import logging
from datetime import datetime
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    """Master orchestrator agent that controls the entire workflow"""
    
    def __init__(self):
        super().__init__(AgentType.ORCHESTRATOR)
        self.decision_rules = self._initialize_decision_rules()
    
    def process(self, state: WorkflowState) -> WorkflowState:
        """Main orchestrator logic - routes to appropriate agents"""
        self.logger.info(f"🎯 Orchestrator analyzing state for workflow_id: {state.get('workflow_id')}")
        
        # Analyze current workflow state
        decision = self._analyze_workflow_state(state)
        
        # Update orchestrator metrics
        state["current_agent"] = "orchestrator"
        state["processing_status"] = ProcessingStatus.IN_PROGRESS.value
        
        # Log decision
        self.logger.info(f"📋 Orchestrator decision: {decision['next_action']} (Reason: {decision['reason']})")
        
        # Store decision in state for workflow routing
        state["orchestrator_decision"] = decision
        
        return state
    
    def _analyze_workflow_state(self, state: WorkflowState) -> Dict[str, Any]:
        """Analyze current state and decide next action"""
        
        # FIRST: Check if workflow should be marked as completed
        if state.get("workflow_completed"):
            return {
                "next_action": "complete_with_errors",
                "reason": "Workflow already marked as completed",
                "confidence": 0.1
            }
        
        # Check orchestrator decision count to prevent infinite loops
        decision_count = state.get("orchestrator_decision_count", 0)
        if decision_count > 15:  # Lower threshold in orchestrator logic
            return {
                "next_action": "complete_with_errors", 
                "reason": f"Too many orchestrator decisions ({decision_count}) - terminating",
                "confidence": 0.1
            }
        
        # Check if max attempts exceeded - CRITICAL GUARD
        if state["attempt_count"] >= state["max_attempts"]:
            return {
                "next_action": "complete_with_errors",
                "reason": f"Maximum attempts ({state['max_attempts']}) exceeded",
                "confidence": 0.1
            }
        
        # Check for critical errors
        if self._has_critical_errors(state):
            return {
                "next_action": "error_recovery",
                "reason": "Critical errors detected requiring recovery",
                "confidence": 0.3
            }
        
        # Handle retry status from error recovery - BUT CHECK ATTEMPTS FIRST
        if state["processing_status"] == ProcessingStatus.NEEDS_RETRY.value:
            # Double-check attempts before allowing retry
            if state["attempt_count"] >= state["max_attempts"]:
                return {
                    "next_action": "complete_with_errors",
                    "reason": f"Cannot retry - max attempts ({state['max_attempts']}) already reached",
                    "confidence": 0.1
                }
            # Reset processing status and attempt contract processing again
            state["processing_status"] = ProcessingStatus.IN_PROGRESS.value
            return {
                "next_action": "contract_processing",
                "reason": f"Retrying after error recovery (attempt {state['attempt_count'] + 1})",
                "confidence": 0.6
            }
        
        # Handle failed status - end workflow
        if state["processing_status"] == ProcessingStatus.FAILED.value:
            return {
                "next_action": "complete_with_errors",
                "reason": "Processing failed - ending workflow",
                "confidence": 0.1
            }
        
        # Quality check results - handle first (we're past initial processing)
        if state.get("quality_assurance_result"):
            qa_result = state["quality_assurance_result"]
            quality_score = qa_result.get("quality_score", 0.0)
            
            if quality_score >= 0.9:
                return {
                    "next_action": "storage_scheduling",
                    "reason": f"High quality score ({quality_score}) - approve for storage",
                    "confidence": 0.9
                }
            elif quality_score >= 0.7 and state["attempt_count"] >= 2:
                return {
                    "next_action": "storage_scheduling",
                    "reason": f"Acceptable quality ({quality_score}) after multiple attempts",
                    "confidence": 0.7
                }
            elif state["attempt_count"] < state["max_attempts"]:
                return {
                    "next_action": "feedback_learning",
                    "reason": f"Low quality ({quality_score}) - learn and retry",
                    "confidence": 0.5
                }
            else:
                return {
                    "next_action": "error_recovery",
                    "reason": f"Persistent low quality ({quality_score}) - escalate",
                    "confidence": 0.3
                }
        
        # Initial state or failed contract processing - start/restart processing
        if not state.get("contract_data") and state["processing_status"] in [
            ProcessingStatus.PENDING.value, 
            ProcessingStatus.IN_PROGRESS.value
        ]:
            return {
                "next_action": "contract_processing",
                "reason": "Starting workflow - contract needs processing",
                "confidence": 0.9
            }
        
        # Contract processed - go straight to completion (validation disabled)
        if state.get("contract_data") and state.get("invoice_data"):
            # Mark workflow as completed since we have the required data
            state["workflow_completed"] = True
            return {
                "next_action": "complete_success",
                "reason": "Contract processing completed - returning invoice data",
                "confidence": 0.9
            }
        
        # Schedule extracted - generate invoice
        if (state.get("schedule_data") and 
            not state.get("invoice_data")):
            return {
                "next_action": "invoice_generation",
                "reason": "Schedule extracted - generate invoice",
                "confidence": 0.8
            }
        
        # Invoice generated - quality check
        if (state.get("invoice_data") and 
            not state.get("final_invoice")):
            return {
                "next_action": "quality_assurance",
                "reason": "Invoice generated - quality check required",
                "confidence": 0.7
            }
        
        # Storage completed - final feedback
        if state.get("storage_result") and state["storage_result"].get("status") == "success":
            # Only proceed to feedback if we haven't done it yet
            if not state.get("feedback_result"):
                return {
                    "next_action": "feedback_learning",
                    "reason": "Successful completion - capture learnings",
                    "confidence": 0.8
                }
            else:
                # Storage and feedback both done - complete workflow
                state["workflow_completed"] = True
                return {
                    "next_action": "complete_success",
                    "reason": "All processing completed successfully",
                    "confidence": 0.9
                }
        
        # Learning completed - workflow done
        if state.get("feedback_result"):
            # Mark workflow as completed to prevent further orchestrator cycles
            state["workflow_completed"] = True
            return {
                "next_action": "complete_success", 
                "reason": "Workflow completed successfully with learning",
                "confidence": 0.9
            }
        
        # Default case - something unexpected
        return {
            "next_action": "error_recovery",
            "reason": "Unexpected state - requires investigation",
            "confidence": 0.2
        }
    
    def _has_critical_errors(self, state: WorkflowState) -> bool:
        """Check if state has critical errors that need immediate attention"""
        errors = state.get("errors", [])
        
        # More than 3 errors is critical
        if len(errors) > 3:
            return True
        
        # Check for specific critical error types
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
    
    # CRITICAL FIX: If no decision is found, it means there's a state sync issue
    # Re-run the orchestrator decision logic directly as a fallback
    if not decision:
        logger.warning("🚨 No orchestrator decision found in state - running fallback analysis")
        from agents.orchestrator_agent import OrchestratorAgent
        temp_orchestrator = OrchestratorAgent()
        fallback_decision = temp_orchestrator._analyze_workflow_state(state)
        next_action = fallback_decision.get("next_action", "error_recovery")
        logger.info(f"🔧 Fallback routing decision: {next_action}")
    elif next_action == "error_recovery" and decision.get("reason", "").startswith("Unexpected"):
        # Only use fallback for truly unexpected default routing, not legitimate error recovery
        logger.warning("🚨 Default error_recovery routing detected - using fallback analysis")
        from agents.orchestrator_agent import OrchestratorAgent
        temp_orchestrator = OrchestratorAgent()
        fallback_decision = temp_orchestrator._analyze_workflow_state(state)
        next_action = fallback_decision.get("next_action", "error_recovery")
        logger.info(f"🔧 Fallback routing decision: {next_action}")
    
    # Map orchestrator decisions to LangGraph node names
    routing_map = {
        "contract_processing": "contract_processing",
        "validation": "validation", 
        "schedule_extraction": "schedule_extraction",
        "invoice_generation": "invoice_generation",
        "quality_assurance": "quality_assurance",
        "storage_scheduling": "storage_scheduling",
        "feedback_learning": "feedback_learning",
        "error_recovery": "error_recovery",
        "complete_success": "__end__",
        "complete_with_errors": "__end__"
    }
    
    routed_node = routing_map.get(next_action, "error_recovery")
    logger.info(f"🎯 Routing to node: {routed_node}")
    
    return routed_node