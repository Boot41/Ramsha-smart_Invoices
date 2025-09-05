from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid
import asyncio
from schemas.workflow_schemas import WorkflowState, ProcessingStatus
from adk_agents.orchestrator_adk_workflow import InvoiceProcessingADKWorkflow
from adk_agents.contract_processing_adk_agent import ContractProcessingADKAgent
from adk_agents.correction_adk_agent import CorrectionADKAgent
from adk_agents.ui_generation_adk_agent import UIGenerationADKAgent
from adk_agents.invoice_generator_adk_agent import InvoiceGeneratorADKAgent
from services.contract_rag_service import get_contract_rag_service
from adk_agents.schedule_retrieval_adk_agent import ScheduleRetrievalADKAgent

logger = logging.getLogger(__name__)

# Agent and Service instances
adk_workflow = InvoiceProcessingADKWorkflow()
contract_rag_service = get_contract_rag_service()
contract_processing_agent = ContractProcessingADKAgent()
correction_agent = CorrectionADKAgent()
invoice_generator_agent = InvoiceGeneratorADKAgent()
ui_invoice_generator_agent = UIGenerationADKAgent()
schedule_retrieval_agent = ScheduleRetrievalADKAgent()

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
    # Correctly call the execute_workflow method with arguments from the state
    return await adk_workflow.execute_workflow(
        user_id=state.get("user_id"),
        contract_file=state.get("contract_file"),
        contract_name=state.get("contract_name"),
        max_attempts=state.get("max_attempts", 3),
        options=state.get("options"),
        workflow_id=state.get("workflow_id")
    )

async def run_invoice_workflow(state: WorkflowState, orchestrator_service=None):
    """
    Runs the invoice generation workflow by orchestrating calls to different agents.
    This replaces the LangGraph implementation with a direct Python control flow.
    """
    # The entire workflow is now managed by the InvoiceProcessingADKWorkflow.
    # We just need to call it and return the final state.
    final_state = await _orchestrator_node(state)
    return final_state

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