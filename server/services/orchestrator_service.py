from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import uuid
from schemas.workflow_schemas import WorkflowRequest, WorkflowResponse, WorkflowStatus, ProcessingStatus
from workflows.invoice_workflow import create_invoice_workflow, initialize_workflow_state

logger = logging.getLogger(__name__)

class OrchestratorService:
    """Service layer for orchestrating agentic invoice workflows"""
    
    def __init__(self):
        self.workflow = create_invoice_workflow()
        self.active_workflows: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
    
    async def start_invoice_workflow(self, request: WorkflowRequest) -> WorkflowResponse:
        """
        Start a new agentic invoice processing workflow
        
        Args:
            request: WorkflowRequest with user_id, contract details, etc.
            
        Returns:
            WorkflowResponse with workflow_id and initial status
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🚀 Starting invoice workflow for user: {request.user_id}")
            
            # Initialize workflow state
            state = initialize_workflow_state(
                user_id=request.user_id,
                contract_file=request.contract_file,
                contract_name=request.contract_name,
                max_attempts=request.max_attempts
            )
            
            workflow_id = state["workflow_id"]
            
            # Store in active workflows
            self.active_workflows[workflow_id] = {
                "state": state,
                "started_at": start_time,
                "request": request.model_dump()
            }
            
            # Execute the workflow asynchronously
            result = await self._execute_workflow(workflow_id, state)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create response
            response = WorkflowResponse(
                workflow_id=workflow_id,
                status=ProcessingStatus(result["processing_status"]),
                message=self._generate_status_message(result),
                result=self._extract_workflow_results(result),
                errors=self._extract_errors(result),
                quality_score=result.get("quality_score", 0.0),
                confidence_level=result.get("confidence_level", 0.0),
                attempt_count=result.get("attempt_count", 0),
                processing_time_seconds=processing_time
            )
            
            self.logger.info(f"✅ Workflow {workflow_id} completed with status: {response.status}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start workflow: {str(e)}")
            
            # Return error response
            return WorkflowResponse(
                workflow_id=str(uuid.uuid4()),
                status=ProcessingStatus.FAILED,
                message=f"Failed to start workflow: {str(e)}",
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_workflow(self, workflow_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the LangGraph workflow"""
        try:
            self.logger.info(f"🔄 Executing workflow {workflow_id}")
            
            # Set recursion limit for the workflow execution
            config = {
                "recursion_limit": 50,  # Increased from default 25 to allow more workflow steps
                "thread_id": workflow_id
            }
            
            # Run the LangGraph workflow with configuration
            # This executes the entire agentic pipeline with feedback loops
            final_state = await asyncio.to_thread(
                self.workflow.workflow.invoke,
                initial_state,
                config=config
            )
            
            # Update stored state
            self.active_workflows[workflow_id]["state"] = final_state
            self.active_workflows[workflow_id]["completed_at"] = datetime.now()
            
            return final_state
            
        except Exception as e:
            self.logger.error(f"❌ Workflow execution failed for {workflow_id}: {str(e)}")
            
            # Update state with error
            error_state = initial_state.copy()
            error_state["processing_status"] = ProcessingStatus.FAILED.value
            error_state["errors"].append({
                "agent": "workflow_execution",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return error_state
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """Get the current status of a workflow"""
        try:
            workflow_info = self.active_workflows.get(workflow_id)
            if not workflow_info:
                return None
            
            state = workflow_info["state"]
            
            # Calculate progress percentage
            progress = self._calculate_progress(state)
            
            return WorkflowStatus(
                workflow_id=workflow_id,
                status=ProcessingStatus(state["processing_status"]),
                current_agent=state["current_agent"],
                progress_percentage=progress,
                last_updated=datetime.fromisoformat(state["last_updated_at"]),
                errors=self._extract_errors(state)
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get workflow status for {workflow_id}: {str(e)}")
            return None
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        try:
            if workflow_id in self.active_workflows:
                # Update state to cancelled
                self.active_workflows[workflow_id]["state"]["processing_status"] = ProcessingStatus.FAILED.value
                self.active_workflows[workflow_id]["cancelled_at"] = datetime.now()
                
                self.logger.info(f"🛑 Workflow {workflow_id} cancelled")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cancel workflow {workflow_id}: {str(e)}")
            return False
    
    def _generate_status_message(self, state: Dict[str, Any]) -> str:
        """Generate a human-readable status message"""
        status = state["processing_status"]
        attempt_count = state.get("attempt_count", 0)
        quality_score = state.get("quality_score", 0.0)
        
        if status == ProcessingStatus.SUCCESS.value:
            if state.get("final_invoice"):
                return f"✅ Invoice processed successfully with quality score {quality_score:.2f} in {attempt_count} attempts"
            else:
                return f"✅ Workflow completed successfully in {attempt_count} attempts"
        elif status == ProcessingStatus.FAILED.value:
            errors_count = len(state.get("errors", []))
            return f"❌ Workflow failed after {attempt_count} attempts with {errors_count} errors"
        elif status == ProcessingStatus.IN_PROGRESS.value:
            current_agent = state.get("current_agent", "unknown")
            return f"🔄 Processing in progress - currently at {current_agent}"
        else:
            return f"ℹ️ Workflow status: {status}"
    
    def _extract_workflow_results(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract key results from the workflow state"""
        results = {}
        
        # Prioritize invoice_data since validation is disabled
        if state.get("invoice_data"):
            results["invoice_data"] = state["invoice_data"]
        
        if state.get("contract_data"):
            results["contract_data"] = state["contract_data"] 
        
        if state.get("final_invoice"):
            results["final_invoice"] = state["final_invoice"]
        
        if state.get("schedule_data"):
            results["schedule_data"] = state["schedule_data"]
        
        if state.get("feedback_result"):
            results["feedback_summary"] = state["feedback_result"]
        
        return results if results else None
    
    def _extract_errors(self, state: Dict[str, Any]) -> list:
        """Extract error messages from workflow state"""
        errors = []
        for error in state.get("errors", []):
            if isinstance(error, dict):
                error_msg = f"{error.get('agent', 'unknown')}: {error.get('error', 'Unknown error')}"
                errors.append(error_msg)
            else:
                errors.append(str(error))
        
        return errors
    
    def _calculate_progress(self, state: Dict[str, Any]) -> float:
        """Calculate workflow progress percentage"""
        # Define workflow stages and their completion weights
        stages = {
            "contract_processing": 15,
            "validation": 25,  
            "schedule_extraction": 40,
            "invoice_generation": 55,
            "quality_assurance": 75,
            "storage_scheduling": 90,
            "feedback_learning": 100
        }
        
        current_agent = state.get("current_agent", "orchestrator")
        
        if current_agent == "orchestrator":
            # Look at what's been completed
            if state.get("feedback_result"):
                return 100.0
            elif state.get("final_invoice"):
                return 90.0
            elif state.get("quality_assurance_result"):
                return 75.0
            elif state.get("invoice_data"):
                return 55.0
            elif state.get("schedule_data"):
                return 40.0
            elif state.get("validation_results"):
                return 25.0
            elif state.get("contract_data"):
                return 15.0
            else:
                return 5.0
        
        return stages.get(current_agent, 5.0)
    
    def cleanup_completed_workflows(self, hours_old: int = 24):
        """Clean up completed workflows older than specified hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            workflows_to_remove = []
            
            for workflow_id, workflow_info in self.active_workflows.items():
                completed_at = workflow_info.get("completed_at")
                if completed_at and completed_at < cutoff_time:
                    workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                del self.active_workflows[workflow_id]
            
            if workflows_to_remove:
                self.logger.info(f"🧹 Cleaned up {len(workflows_to_remove)} old workflows")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup workflows: {str(e)}")


# Singleton instance
_orchestrator_service = None

def get_orchestrator_service() -> OrchestratorService:
    """Get singleton orchestrator service instance"""
    global _orchestrator_service
    if _orchestrator_service is None:
        _orchestrator_service = OrchestratorService()
    return _orchestrator_service