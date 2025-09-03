from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import uuid
from schemas.workflow_schemas import WorkflowRequest, WorkflowResponse, WorkflowStatus, ProcessingStatus
from workflows.invoice_workflow import create_invoice_workflow, initialize_workflow_state

from services.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)

class OrchestratorService:
    """Service layer for orchestrating agentic invoice workflows"""
    
    def __init__(self):
        self.active_workflows: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        self.websocket_manager = get_websocket_manager()
        
        # Human input management
        self.human_input_events: Dict[str, asyncio.Event] = {}
        self.human_input_data: Dict[str, Any] = {}
        self.running_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Initialize workflow with self reference for human input
        self.workflow = create_invoice_workflow(orchestrator_service=self)
    
    async def start_invoice_workflow(self, request: WorkflowRequest, background_tasks) -> WorkflowResponse:
        """
        Start a new agentic invoice processing workflow
        
        Args:
            request: WorkflowRequest with user_id, contract details, etc.
            
        Returns:
            WorkflowResponse with workflow_id and initial status
        """
        start_time = datetime.now()
        workflow_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"🚀 Starting invoice workflow for user: {request.user_id}")
            
            # Initialize workflow state
            state = initialize_workflow_state(
                user_id=request.user_id,
                contract_file=request.contract_file,
                contract_name=request.contract_name,
                max_attempts=request.max_attempts,
                workflow_id=workflow_id
            )
            
            # Store in active workflows
            self.active_workflows[workflow_id] = {
                "state": state,
                "started_at": start_time,
                "request": request.model_dump()
            }
            
            # Store running workflow with user info
            self.running_workflows[workflow_id] = {
                "task": None,
                "user_id": request.user_id,
                "status": "STARTING"
            }
            
            # Execute the workflow in the background
            background_tasks.add_task(self._execute_workflow, workflow_id, state)
            
            # Return initial response immediately
            response = WorkflowResponse(
                workflow_id=workflow_id,
                status=ProcessingStatus.IN_PROGRESS,
                message="Workflow started. Connect to WebSocket for real-time updates.",
                result=None,
                errors=[],
                quality_score=0.0,
                confidence_level=0.0,
                attempt_count=0,
                processing_time_seconds=0.0
            )
            
            self.logger.info(f"✅ Workflow {workflow_id} started successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start workflow: {str(e)}")
            
            # Return error response
            return WorkflowResponse(
                workflow_id=workflow_id,
                status=ProcessingStatus.FAILED,
                message=f"Failed to start workflow: {str(e)}",
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_workflow(self, workflow_id: str, initial_state: Dict[str, Any]):
        """Execute the invoice workflow and notify via WebSocket"""
        final_state = None
        try:
            self.logger.info(f"🔄 Executing workflow {workflow_id}")
            
            # Update running workflow status
            if workflow_id in self.running_workflows:
                self.running_workflows[workflow_id]["status"] = "IN_PROGRESS"
                
            await self.websocket_manager.notify_workflow_status(workflow_id, "in_progress", "Workflow execution started.")

            final_state = await self.workflow(initial_state)

            self.active_workflows[workflow_id]["state"] = final_state
            self.active_workflows[workflow_id]["completed_at"] = datetime.now()

            # Update running workflow status
            if workflow_id in self.running_workflows:
                self.running_workflows[workflow_id]["status"] = "COMPLETED"

            await self.websocket_manager.notify_workflow_completed(workflow_id, final_state)
            self.logger.info(f"✅ Workflow {workflow_id} completed.")

        except Exception as e:
            self.logger.error(f"❌ Workflow execution failed for {workflow_id}: {str(e)}")
            if workflow_id in self.active_workflows:
                error_state = self.active_workflows[workflow_id]["state"]
                error_state["processing_status"] = ProcessingStatus.FAILED.value
                error_state["errors"].append({
                    "agent": "workflow_execution",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                self.active_workflows[workflow_id]["state"] = error_state
                
                # Update running workflow status
                if workflow_id in self.running_workflows:
                    self.running_workflows[workflow_id]["status"] = "FAILED"
                    
                await self.websocket_manager.notify_workflow_failed(workflow_id, str(e), error_state)
        finally:
            # Clean up running workflow entry after completion
            if workflow_id in self.running_workflows:
                del self.running_workflows[workflow_id]

    async def wait_for_human_input(self, task_id: str, prompt: str, user_id: str = None) -> str:
        """
        Pause the workflow and wait for human input via WebSocket
        
        Args:
            task_id: Unique identifier for this input request (usually workflow_id)
            prompt: The message/prompt to display to the user
            user_id: Optional user ID to target specific user
            
        Returns:
            The user input as a string
        """
        try:
            self.logger.info(f"⏳ Waiting for human input for task: {task_id}")
            
            # Create an event for this task
            event = asyncio.Event()
            self.human_input_events[task_id] = event
            
            # Determine user_id if not provided
            if not user_id and task_id in self.running_workflows:
                user_id = self.running_workflows[task_id]["user_id"]
            
            # Update workflow status to waiting
            if task_id in self.running_workflows:
                self.running_workflows[task_id]["status"] = "WAITING_FOR_HUMAN_INPUT"
            
            # Update active workflows state if exists
            if task_id in self.active_workflows:
                self.active_workflows[task_id]["state"]["processing_status"] = "WAITING_FOR_HUMAN_INPUT"
                self.active_workflows[task_id]["state"]["current_agent"] = "waiting_for_human_input"
            
            # Send WebSocket message requesting human input
            message = {
                "type": "human_input_required",
                "task_id": task_id,
                "prompt": prompt,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.notify_workflow_status(
                task_id, 
                "waiting_for_human_input", 
                f"Human input required: {prompt}"
            )
            
            # Send targeted message if user_id is available
            if user_id:
                try:
                    await self.websocket_manager.send_to_user(user_id, message)
                except Exception as e:
                    self.logger.warning(f"Failed to send targeted message to user {user_id}: {e}")
            
            self.logger.info(f"📤 Sent human input request for task {task_id}")
            
            # Wait for the event to be set
            await event.wait()
            
            # Retrieve the user input
            user_input = self.human_input_data.get(task_id, "")
            
            # Clean up
            if task_id in self.human_input_events:
                del self.human_input_events[task_id]
            if task_id in self.human_input_data:
                del self.human_input_data[task_id]
            
            # Update workflow status back to in progress
            if task_id in self.running_workflows:
                self.running_workflows[task_id]["status"] = "IN_PROGRESS"
            
            if task_id in self.active_workflows:
                self.active_workflows[task_id]["state"]["processing_status"] = ProcessingStatus.IN_PROGRESS.value
            
            self.logger.info(f"✅ Received human input for task {task_id}: {len(user_input)} characters")
            
            return user_input
            
        except Exception as e:
            self.logger.error(f"❌ Failed to wait for human input for task {task_id}: {str(e)}")
            
            # Clean up on error
            if task_id in self.human_input_events:
                del self.human_input_events[task_id]
            if task_id in self.human_input_data:
                del self.human_input_data[task_id]
            
            # Re-raise the exception
            raise e

    async def process_human_input(self, task_id: str, user_input: str) -> bool:
        """
        Process human input received from the frontend and resume the waiting workflow
        
        Args:
            task_id: The task ID that was waiting for input (usually workflow_id)
            user_input: The input provided by the user
            
        Returns:
            True if input was processed successfully, False otherwise
        """
        try:
            self.logger.info(f"📥 Processing human input for task: {task_id}")
            
            # Check if we have a waiting event for this task
            if task_id not in self.human_input_events:
                self.logger.warning(f"⚠️  No waiting event found for task {task_id}")
                return False
            
            # Store the user input
            self.human_input_data[task_id] = user_input
            
            # Set the event to unblock the waiting workflow
            event = self.human_input_events[task_id]
            event.set()
            
            # Get user_id for targeted notification
            user_id = None
            if task_id in self.running_workflows:
                user_id = self.running_workflows[task_id]["user_id"]
            
            # Send confirmation via WebSocket
            confirmation_message = {
                "type": "human_input_received",
                "task_id": task_id,
                "message": "Input received. Workflow resuming...",
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.notify_workflow_status(
                task_id, 
                "in_progress", 
                "Human input received. Workflow resuming..."
            )
            
            # Send targeted confirmation if user_id is available
            if user_id:
                try:
                    await self.websocket_manager.send_to_user(user_id, confirmation_message)
                except Exception as e:
                    self.logger.warning(f"Failed to send confirmation to user {user_id}: {e}")
            
            self.logger.info(f"✅ Human input processed successfully for task {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process human input for task {task_id}: {str(e)}")
            return False
    
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
