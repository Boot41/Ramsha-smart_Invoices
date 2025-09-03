from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid
import asyncio
from schemas.workflow_schemas import WorkflowState, ProcessingStatus
from agents.orchestrator_agent import OrchestratorAgent
from agents.contract_processing_agent import ContractProcessingAgent
from agents.validation_agent import ValidationAgent
from agents.correction_agent import CorrectionAgent
from agents.ui_invoice_generator_agent import UIInvoiceGeneratorAgent
from agents.invoice_generator_agent import InvoiceGeneratorAgent
from services.contract_rag_service import get_contract_rag_service

logger = logging.getLogger(__name__)

# Agent and Service instances
orchestrator = OrchestratorAgent()
contract_rag_service = get_contract_rag_service()
contract_processing_agent = ContractProcessingAgent()
validation_agent = ValidationAgent()
correction_agent = CorrectionAgent()
invoice_generator_agent = InvoiceGeneratorAgent()
ui_invoice_generator_agent = UIInvoiceGeneratorAgent()

async def _orchestrator_node(state: WorkflowState) -> WorkflowState:
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
    return await orchestrator.execute(state)

async def _contract_processing_node(state: WorkflowState) -> WorkflowState:
    """Node that executes the Contract Processing Agent."""
    state["attempt_count"] += 1
    return await contract_processing_agent.execute(state)

async def _validation_node(state: WorkflowState) -> WorkflowState:
    """Node that executes the Validation Agent with WebSocket integration."""
    return await validation_agent.process(state)

async def _correction_node(state: WorkflowState) -> WorkflowState:
    """Node that executes the Correction Agent to generate final invoice JSON."""
    return await correction_agent.process(state)

async def _schedule_extraction_node(state: WorkflowState) -> WorkflowState:
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

async def _invoice_generation_node(state: WorkflowState) -> WorkflowState:
    """Create invoice record in database using InvoiceGeneratorAgent"""
    return await invoice_generator_agent.process(state)

async def _quality_assurance_node(state: WorkflowState) -> WorkflowState:
    """Perform quality assurance on generated invoice"""
    logger.info("🔍 Performing quality assurance...")
    # Placeholder for QA logic
    state["quality_score"] = 0.95
    state["processing_status"] = ProcessingStatus.SUCCESS.value
    logger.info("✅ Quality assurance completed")
    return state

async def _ui_invoice_generator_node(state: WorkflowState) -> WorkflowState:
    """Generate professional invoice UI template using Gemini"""
    return await ui_invoice_generator_agent.process(state)

async def _storage_scheduling_node(state: WorkflowState) -> WorkflowState:
    """Store invoice and schedule future processing"""
    logger.info("💾 Storing invoice and scheduling...")
    # Placeholder for storage logic
    state["storage_result"] = {"status": "success", "stored_at": datetime.now().isoformat()}
    state["processing_status"] = ProcessingStatus.SUCCESS.value
    logger.info("✅ Storage and scheduling completed")
    return state

async def _feedback_learning_node(state: WorkflowState) -> WorkflowState:
    """Learn from the workflow execution for future improvements"""
    logger.info("🧠 Processing feedback and learning...")
    # Placeholder for feedback logic
    state["feedback_result"] = {"status": "success", "learned_at": datetime.now().isoformat()}
    state["workflow_completed"] = True
    logger.info("✅ Feedback learning completed - workflow marked as complete")
    return state

async def _error_recovery_node(state: WorkflowState) -> WorkflowState:
    """Handle errors and attempt recovery"""
    logger.info("🚨 Attempting error recovery...")
    # Placeholder for error recovery
    state["processing_status"] = ProcessingStatus.FAILED.value
    logger.info("💀 Error recovery attempted, but marking as failed for now.")
    return state

async def run_invoice_workflow(state: WorkflowState, orchestrator_service=None):
    """
    Runs the invoice generation workflow by orchestrating calls to different agents.
    This replaces the LangGraph implementation with a direct Python control flow.
    """
    max_steps = 10  # Safety break to prevent infinite loops
    for i in range(max_steps):
        state = await _orchestrator_node(state)
        next_agent = state.get("current_agent")

        if next_agent in ("contract_processing", "enhanced_contract_processing"):
            # Both the legacy contract_processing and the newer enhanced_contract_processing
            # should execute the contract processing node. Prefer the existing agent implementation
            # for now to keep behavior consistent.
            state = await _contract_processing_node(state)
        elif next_agent == "validation":
            state = await _validation_node(state)
        elif next_agent == "correction":
            state = await _correction_node(state)
        elif next_agent == "schedule_extraction":
            state = await _schedule_extraction_node(state)
        elif next_agent == "invoice_generation":
            state = await _invoice_generation_node(state)
        elif next_agent == "quality_assurance":
            state = await _quality_assurance_node(state)
        # Removed ui_invoice_generator - workflow completes after quality assurance
        elif next_agent == "storage_scheduling":
            state = await _storage_scheduling_node(state)
        elif next_agent == "feedback_learning":
            state = await _feedback_learning_node(state)
            break  # End of workflow
        elif next_agent == "error_recovery":
            state = await _error_recovery_node(state)
            break # End of workflow
        elif next_agent == "waiting_for_human_input":
            if orchestrator_service:
                # Use the new wait_for_human_input method
                logger.info("⏳ Waiting for human input using orchestrator service...")
                workflow_id = state.get("workflow_id")
                user_id = state.get("user_id")
                
                # Get the prompt from state if available
                prompt = state.get("human_input_prompt", "Please provide input to continue the workflow")
                
                try:
                    user_input = await orchestrator_service.wait_for_human_input(
                        task_id=workflow_id,
                        prompt=prompt,
                        user_id=user_id
                    )
                    
                    # Store the user input in state for agents to use
                    state["human_input"] = user_input
                    state["human_input_received_at"] = datetime.now().isoformat()
                    
                    # Reset the agent to continue workflow
                    state["current_agent"] = "orchestrator"
                    
                    logger.info(f"✅ Received human input: {len(user_input)} characters")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to wait for human input: {str(e)}")
                    state["processing_status"] = ProcessingStatus.FAILED.value
                    state["errors"].append({
                        "agent": "human_input",
                        "error": f"Failed to get human input: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
                    break
            else:
                # Fallback to old behavior
                logger.warning("⚠️ No orchestrator service available, using legacy wait method")
                logger.info("⏳ Waiting for human input via WebSocket...")
                # Sleep briefly to avoid busy loop, then re-evaluate
                await asyncio.sleep(0.1)
        elif next_agent in ["complete_success", "complete_with_errors", "__end__"]:
            logger.info(f"Workflow finished with status: {next_agent}")
            state["workflow_completed"] = True
            
            # Prepare final response data for frontend
            if next_agent == "complete_success" and state.get("final_invoice_data"):
                state["final_response"] = {
                    "status": "success",
                    "message": "Invoice generated successfully",
                    "workflow_id": state.get("workflow_id"),
                    "invoice_uuid": state.get("invoice_uuid"),
                    "invoice_number": state.get("invoice_number"),
                    "contract_uuid": state.get("contract_id"),
                    "invoice_data": state.get("final_invoice_data"),
                    "completed_at": datetime.now().isoformat(),
                    "quality_score": state.get("quality_score", 0.0),
                    "confidence_score": state.get("confidence_level", 0.0)
                }
                logger.info(f"✅ Final invoice data prepared for frontend - Invoice UUID: {state.get('invoice_uuid')}")
            break
        else:
            logger.error(f"Unknown agent: {next_agent}. Terminating workflow.")
            state['errors'].append({"agent": "workflow", "error": f"Unknown agent {next_agent}"})
            break
    else:
        logger.warning(f"Workflow reached max steps ({max_steps}). Terminating.")
        state['errors'].append({"agent": "workflow", "error": "Max steps reached"})

    return state

def create_invoice_workflow(orchestrator_service=None):
    """
    Factory function to create a new invoice workflow instance.
    In this native implementation, it returns the main workflow function with orchestrator service.
    """
    async def workflow_with_service(state: WorkflowState):
        return await run_invoice_workflow(state, orchestrator_service)
    
    return workflow_with_service

def initialize_workflow_state(user_id: str, contract_file: Any, contract_name: str, max_attempts: int = 3, workflow_id: Optional[str] = None) -> WorkflowState:
    """Initialize a new workflow state"""
    w_id = workflow_id if workflow_id else str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    return {
        "workflow_id": w_id,
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