from typing import Dict, Any
import logging
from datetime import datetime
import uuid
from langgraph.graph import StateGraph, END
from schemas.workflow_schemas import WorkflowState, ProcessingStatus
from agents.orchestrator_agent import OrchestratorAgent, route_from_orchestrator
from agents.contract_processing_agent import ContractProcessingAgent
from services.contract_rag_service import get_contract_rag_service
from utils.langsmith_config import get_langsmith_config, trace_workflow_step

logger = logging.getLogger(__name__)

class InvoiceWorkflow:
    """Complete agentic invoice processing workflow using LangGraph"""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.contract_rag_service = get_contract_rag_service()
        self.contract_processing_agent = ContractProcessingAgent()
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the complete LangGraph workflow with all agents and feedback loops"""
        
        # Create the state graph
        workflow = StateGraph(WorkflowState)
        
        # Add all nodes (agents)
        workflow.add_node("orchestrator", self._orchestrator_node)
        workflow.add_node("contract_processing", self._contract_processing_node)
        # workflow.add_node("validation", self._validation_node)
        workflow.add_node("schedule_extraction", self._schedule_extraction_node) 
        workflow.add_node("invoice_generation", self._invoice_generation_node)
        workflow.add_node("quality_assurance", self._quality_assurance_node)
        workflow.add_node("storage_scheduling", self._storage_scheduling_node)
        workflow.add_node("feedback_learning", self._feedback_learning_node)
        workflow.add_node("error_recovery", self._error_recovery_node)
        
        # Set entry point
        workflow.set_entry_point("orchestrator")
        
        # Add conditional edges from orchestrator (the main router)
        workflow.add_conditional_edges(
            "orchestrator",
            route_from_orchestrator,
            {
                "contract_processing": "contract_processing",
                # "validation": "validation",
                "schedule_extraction": "schedule_extraction", 
                "invoice_generation": "invoice_generation",
                "quality_assurance": "quality_assurance",
                "storage_scheduling": "storage_scheduling",
                "feedback_learning": "feedback_learning",
                "error_recovery": "error_recovery",
                "__end__": END
            }
        )
        
        # All agents return to orchestrator for next decision (agentic loops)
        workflow.add_edge("contract_processing", "orchestrator")
        # workflow.add_edge("validation", "orchestrator") 
        workflow.add_edge("schedule_extraction", "orchestrator")
        workflow.add_edge("invoice_generation", "orchestrator")
        workflow.add_edge("quality_assurance", "orchestrator")
        workflow.add_edge("storage_scheduling", "orchestrator")
        workflow.add_edge("feedback_learning", "orchestrator")
        workflow.add_edge("error_recovery", "orchestrator")
        
        return workflow.compile(
            checkpointer=None,
            interrupt_before=None,
            interrupt_after=None,
            debug=False
        ).with_config({"recursion_limit": 100})
    
    # Agent Node Implementations
    def _orchestrator_node(self, state: WorkflowState) -> WorkflowState:
        """Orchestrator node - routes to appropriate agents"""
        # Increment orchestrator decision counter to prevent infinite loops
        state["orchestrator_decision_count"] = state.get("orchestrator_decision_count", 0) + 1
        
        # Emergency brake: if orchestrator has made too many decisions, force termination
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
            
        return self.orchestrator.execute(state)
    
    def _contract_processing_node(self, state: WorkflowState) -> WorkflowState:
        """Node that executes the Contract Processing Agent."""
        # Increment attempt counter before execution
        state["attempt_count"] += 1
        return self.contract_processing_agent.execute(state)
    
    def _validation_node(self, state: WorkflowState) -> WorkflowState:
        """Validate processed contract data"""
        logger.info("🔍 Validating contract data...")
        
        try:
            contract_data = state.get("contract_data", {})
            context = contract_data.get("context", "")
            
            # Validation rules
            validation_results = {
                "has_content": len(context) > 50,
                "has_parties": "tenant" in context.lower() or "client" in context.lower(),
                "has_payment_terms": "payment" in context.lower() or "rent" in context.lower(),
                "has_dates": any(word in context.lower() for word in ["date", "month", "year"]),
                "overall_score": 0.0
            }
            
            # Calculate overall validation score
            passed_checks = sum(validation_results.values()) - validation_results["overall_score"]
            total_checks = len(validation_results) - 1
            validation_results["overall_score"] = passed_checks / total_checks
            
            # Determine validation status
            if validation_results["overall_score"] >= 0.7:
                validation_results["status"] = "passed"
                state["processing_status"] = ProcessingStatus.SUCCESS.value
            else:
                validation_results["status"] = "failed"
                state["processing_status"] = ProcessingStatus.FAILED.value
            
            state["validation_results"] = validation_results
            state["confidence_level"] = validation_results["overall_score"]
            
            logger.info(f"✅ Validation completed - Score: {validation_results['overall_score']:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {str(e)}")
            state["validation_results"] = {"status": "failed", "error": str(e)}
            state["processing_status"] = ProcessingStatus.FAILED.value
        
        return state
    
    def _schedule_extraction_node(self, state: WorkflowState) -> WorkflowState:
        """Extract scheduling information from contract"""
        logger.info("📅 Extracting schedule data...")
        
        try:
            contract_data = state.get("contract_data", {})
            context = contract_data.get("context", "")
            
            # Use LLM to extract schedule data
            schedule_prompt = f"""
            Extract scheduling information from this contract:
            
            {context}
            
            Return JSON with:
            - frequency (monthly/quarterly/annually)
            - start_date
            - end_date 
            - due_day
            """
            
            # This could use your existing LLM service
            from models.llm.base import get_model
            model = get_model()
            response = model.invoke(schedule_prompt)
            
            # For now, create basic schedule data
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
    
    def _invoice_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Generate invoice using existing RAG service"""
        logger.info("📄 Generating invoice data...")
        
        try:
            # Use your existing invoice generation service
            user_id = state["user_id"]
            contract_name = state["contract_name"]
            
            invoice_response = self.contract_rag_service.generate_invoice_data(
                user_id, contract_name
            )
            
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
    
    def _quality_assurance_node(self, state: WorkflowState) -> WorkflowState:
        """Perform quality assurance on generated invoice"""
        logger.info("🔍 Performing quality assurance...")
        
        try:
            invoice_data = state.get("invoice_data", {})
            invoice_response = invoice_data.get("invoice_response", {})
            
            # Quality checks
            quality_checks = {
                "has_invoice_data": bool(invoice_response.get("invoice_data")),
                "has_client_info": bool(invoice_response.get("invoice_data", {}).get("client")),
                "has_amount": bool(invoice_response.get("invoice_data", {}).get("payment_terms", {}).get("amount")),
                "confidence_acceptable": invoice_data.get("confidence", 0) > 0.5
            }
            
            # Calculate quality score
            passed_checks = sum(quality_checks.values())
            total_checks = len(quality_checks)
            quality_score = passed_checks / total_checks
            
            qa_result = {
                "quality_score": quality_score,
                "checks": quality_checks,
                "status": "passed" if quality_score >= 0.7 else "failed",
                "assessed_at": datetime.now().isoformat()
            }
            
            state["quality_assurance_result"] = qa_result
            state["quality_score"] = quality_score
            state["processing_status"] = ProcessingStatus.SUCCESS.value
            
            logger.info(f"✅ Quality assurance completed - Score: {quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Quality assurance failed: {str(e)}")
            state["processing_status"] = ProcessingStatus.FAILED.value
            
        return state
    
    def _storage_scheduling_node(self, state: WorkflowState) -> WorkflowState:
        """Store invoice and schedule future processing"""
        logger.info("💾 Storing invoice and scheduling...")
        
        try:
            # Store the final invoice
            final_invoice = {
                "workflow_id": state["workflow_id"],
                "user_id": state["user_id"],
                "contract_name": state["contract_name"],
                "invoice_data": state.get("invoice_data"),
                "schedule_data": state.get("schedule_data"),
                "quality_score": state.get("quality_score", 0.0),
                "stored_at": datetime.now().isoformat()
            }
            
            state["final_invoice"] = final_invoice
            state["storage_result"] = {
                "status": "success",
                "stored_at": datetime.now().isoformat()
            }
            state["processing_status"] = ProcessingStatus.SUCCESS.value
            
            logger.info("✅ Storage and scheduling completed")
            
        except Exception as e:
            logger.error(f"❌ Storage failed: {str(e)}")
            state["processing_status"] = ProcessingStatus.FAILED.value
            
        return state
    
    def _feedback_learning_node(self, state: WorkflowState) -> WorkflowState:
        """Learn from the workflow execution for future improvements"""
        logger.info("🧠 Processing feedback and learning...")
        
        try:
            # Analyze what worked and what didn't
            success_factors = []
            improvement_areas = []
            
            if state.get("quality_score", 0) > 0.8:
                success_factors.append("High quality invoice generation")
            if state.get("confidence_level", 0) > 0.7:
                success_factors.append("Good confidence in processing")
            if len(state.get("errors", [])) == 0:
                success_factors.append("Error-free processing")
                
            if state.get("quality_score", 0) < 0.7:
                improvement_areas.append("Invoice quality needs improvement")
            if state.get("attempt_count", 0) > 1:
                improvement_areas.append("Multiple attempts needed - optimize first-pass success")
            
            feedback_result = {
                "success_factors": success_factors,
                "improvement_areas": improvement_areas,
                "overall_success": state.get("quality_score", 0) > 0.7,
                "learned_at": datetime.now().isoformat()
            }
            
            state["feedback_result"] = feedback_result
            state["processing_status"] = ProcessingStatus.SUCCESS.value
            state["workflow_completed"] = True  # Mark workflow as completed after feedback
            
            logger.info("✅ Feedback learning completed - workflow marked as complete")
            
        except Exception as e:
            logger.error(f"❌ Feedback learning failed: {str(e)}")
            state["processing_status"] = ProcessingStatus.FAILED.value
            state["workflow_completed"] = True  # Still mark as completed even on failure
            
        return state
    
    def _error_recovery_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and attempt recovery"""
        logger.info("🚨 Attempting error recovery...")
        
        try:
            errors = state.get("errors", [])
            
            # Analyze errors and suggest recovery
            recovery_actions = []
            
            for error in errors:
                error_msg = error.get("error", "").lower()
                if "file" in error_msg or "not found" in error_msg:
                    recovery_actions.append("Check file availability and permissions")
                elif "database" in error_msg:
                    recovery_actions.append("Verify database connection")
                elif "validation" in error_msg:
                    recovery_actions.append("Review validation criteria")
                else:
                    recovery_actions.append("General error recovery needed")
            
            # Attempt basic recovery if possible
            if state["attempt_count"] < state["max_attempts"]:
                state["retry_reasons"] = recovery_actions
                state["processing_status"] = ProcessingStatus.NEEDS_RETRY.value
                logger.info(f"🔄 Preparing for retry {state['attempt_count'] + 1}/{state['max_attempts']}")
            else:
                state["processing_status"] = ProcessingStatus.FAILED.value
                logger.info(f"💀 Max attempts ({state['max_attempts']}) reached, marking as failed")
            
            logger.info(f"🔧 Error recovery attempted - Actions: {recovery_actions}")
            
        except Exception as e:
            logger.error(f"❌ Error recovery failed: {str(e)}")
            state["processing_status"] = ProcessingStatus.FAILED.value
            
        return state


def create_invoice_workflow() -> InvoiceWorkflow:
    """Factory function to create a new invoice workflow instance"""
    return InvoiceWorkflow()


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
        "retry_reasons": [],
        "learned_patterns": {},
        "improvement_suggestions": [],
        "success_metrics": {},
        "started_at": now,
        "last_updated_at": now
    }