from typing import Dict, Any
import logging
from datetime import datetime
import uuid
from schemas.workflow_schemas import WorkflowState, ProcessingStatus
from agents.orchestrator_agent import OrchestratorAgent
from agents.contract_processing_agent import ContractProcessingAgent
from services.contract_rag_service import get_contract_rag_service
from utils.langsmith_config import get_langsmith_config, trace_workflow_step

logger = logging.getLogger(__name__)

# Agent and Service instances
orchestrator = OrchestratorAgent()
contract_rag_service = get_contract_rag_service()
contract_processing_agent = ContractProcessingAgent()

def _orchestrator_node(state: WorkflowState) -> WorkflowState:
    """Orchestrator node - routes to appropriate agents"""
    state["orchestrator_decision_count"] = state.get("orchestrator_decision_count", 0) + 1
    if state["orchestrator_decision_count"] > 20:
        logger.warning(f"🚨 Orchestrator decision count exceeded 20, forcing workflow termination")
        state["processing_status"] = ProcessingStatus.FAILED.value
        state["workflow_completed"] = True
        state["errors"].append({
            "agent": "orchestrator",
            "error": "Too many orchestrator decisions - workflow forced to terminate",
            "timestamp": datetime.now().isoformat()
        })
        return state
    return orchestrator.execute(state)

def _contract_processing_node(state: WorkflowState) -> WorkflowState:
    """Node that executes the Contract Processing Agent."""
    state["attempt_count"] += 1
    return contract_processing_agent.execute(state)

def _schedule_extraction_node(state: WorkflowState) -> WorkflowState:
    """Extract scheduling information from contract"""
    logger.info("📅 Extracting schedule data...")
    try:
        # This is a placeholder, actual implementation would use an agent or service
        schedule_data = {
            "frequency": "monthly",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "due_day": 1,
            "extracted_at": datetime.now().isoformat(),
            "confidence": 0.7
        }
        state["schedule_data"] = schedule_data
        state["processing_status"] = ProcessingStatus.SUCCESS.value
        logger.info("✅ Schedule extraction completed")
    except Exception as e:
        logger.error(f"❌ Schedule extraction failed: {str(e)}")
        state["processing_status"] = ProcessingStatus.FAILED.value
    return state

def _invoice_generation_node(state: WorkflowState) -> WorkflowState:
    """Generate invoice using existing RAG service"""
    logger.info("📄 Generating invoice data...")
    try:
        user_id = state["user_id"]
        contract_name = state["contract_name"]
        invoice_response = contract_rag_service.generate_invoice_data(user_id, contract_name)
        state["invoice_data"] = {
            "invoice_response": invoice_response.dict(),
            "generated_at": datetime.now().isoformat(),
            "confidence": invoice_response.confidence_score
        }
        state["confidence_level"] = invoice_response.confidence_score
        state["processing_status"] = ProcessingStatus.SUCCESS.value
        logger.info("✅ Invoice generation completed")
    except Exception as e:
        logger.error(f"❌ Invoice generation failed: {str(e)}")
        state["processing_status"] = ProcessingStatus.FAILED.value
    return state

def _quality_assurance_node(state: WorkflowState) -> WorkflowState:
    """Perform quality assurance on generated invoice"""
    logger.info("🔍 Performing quality assurance...")
    # Placeholder for QA logic
    state["quality_score"] = 0.95
    state["processing_status"] = ProcessingStatus.SUCCESS.value
    logger.info("✅ Quality assurance completed")
    return state

def _storage_scheduling_node(state: WorkflowState) -> WorkflowState:
    """Store invoice and schedule future processing"""
    logger.info("💾 Storing invoice and scheduling...")
    # Placeholder for storage logic
    state["storage_result"] = {"status": "success", "stored_at": datetime.now().isoformat()}
    state["processing_status"] = ProcessingStatus.SUCCESS.value
    logger.info("✅ Storage and scheduling completed")
    return state

def _feedback_learning_node(state: WorkflowState) -> WorkflowState:
    """Learn from the workflow execution for future improvements"""
    logger.info("🧠 Processing feedback and learning...")
    # Placeholder for feedback logic
    state["feedback_result"] = {"status": "success", "learned_at": datetime.now().isoformat()}
    state["workflow_completed"] = True
    logger.info("✅ Feedback learning completed - workflow marked as complete")
    return state

def _error_recovery_node(state: WorkflowState) -> WorkflowState:
    """Handle errors and attempt recovery"""
    logger.info("🚨 Attempting error recovery...")
    # Placeholder for error recovery
    state["processing_status"] = ProcessingStatus.FAILED.value
    logger.info("💀 Error recovery attempted, but marking as failed for now.")
    return state


def run_invoice_workflow(state: WorkflowState):
    """
    Runs the invoice generation workflow by orchestrating calls to different agents.
    This replaces the LangGraph implementation with a direct Python control flow.
    """
    max_steps = 10  # Safety break to prevent infinite loops
    for i in range(max_steps):
        state = _orchestrator_node(state)
        next_agent = state.get("current_agent")

        if next_agent == "contract_processing":
            state = _contract_processing_node(state)
        elif next_agent == "schedule_extraction":
            state = _schedule_extraction_node(state)
        elif next_agent == "invoice_generation":
            state = _invoice_generation_node(state)
        elif next_agent == "quality_assurance":
            state = _quality_assurance_node(state)
        elif next_agent == "storage_scheduling":
            state = _storage_scheduling_node(state)
        elif next_agent == "feedback_learning":
            state = _feedback_learning_node(state)
            break  # End of workflow
        elif next_agent == "error_recovery":
            state = _error_recovery_node(state)
            break # End of workflow
        elif next_agent == "__end__":
            logger.info("Workflow finished successfully.")
            break
        else:
            logger.error(f"Unknown agent: {next_agent}. Terminating workflow.")
            state['errors'].append({"agent": "workflow", "error": f"Unknown agent {next_agent}"})
            break
    else:
        logger.warning(f"Workflow reached max steps ({max_steps}). Terminating.")
        state['errors'].append({"agent": "workflow", "error": "Max steps reached"})

    return state


def create_invoice_workflow():
    """
    Factory function to create a new invoice workflow instance.
    In this native implementation, it returns the main workflow function.
    """
    return run_invoice_workflow


def initialize_workflow_state(user_id: str, contract_file: str, contract_name: str, max_attempts: int = 3) -> WorkflowState:
    """Initialize a new workflow state"""
    workflow_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    return {
        "workflow_id": workflow_id,
        "user_id": user_id,
        "contract_file": contract_file,
        "contract_name": contract_name,
        "contract_data": None,
        "validation_results": None,
        "invoice_data": None,
        "schedule_data": None,
        "final_invoice": None,
        "attempt_count": 0,
        "max_attempts": max_attempts,
        "errors": [],
        "feedback_history": [],
        "quality_score": 0.0,
        "confidence_level": 0.0,
        "processing_status": ProcessingStatus.PENDING.value,
        "current_agent": "orchestrator",
        "orchestrator_decision_count": 0,
        "retry_reasons": [],
        "learned_patterns": {},
        "improvement_suggestions": [],
        "success_metrics": {},
        "started_at": now,
        "last_updated_at": now,
        "workflow_completed": False,
    }
