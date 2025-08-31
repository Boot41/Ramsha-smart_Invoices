from typing import Optional
import logging
from fastapi import HTTPException, BackgroundTasks
from schemas.workflow_schemas import WorkflowRequest, WorkflowResponse, WorkflowStatus
from services.orchestrator_service import get_orchestrator_service

logger = logging.getLogger(__name__)

class OrchestratorController:
    """Controller for handling orchestrator workflow requests"""
    
    def __init__(self):
        self.orchestrator_service = get_orchestrator_service()
        self.logger = logging.getLogger(__name__)
    
    async def start_invoice_workflow(self, request: WorkflowRequest, background_tasks: BackgroundTasks) -> WorkflowResponse:
        """
        Start a new agentic invoice processing workflow
        
        Args:
            request: WorkflowRequest containing user_id, contract details
            background_tasks: FastAPI background tasks for cleanup
            
        Returns:
            WorkflowResponse with workflow status and results
        """
        try:
            self.logger.info(f"📋 Controller: Starting workflow for user {request.user_id}, contract {request.contract_name}")
            
            # Validate request
            self._validate_workflow_request(request)
            
            # Start the workflow through service layer
            response = await self.orchestrator_service.start_invoice_workflow(request)
            
            # Schedule cleanup of old workflows
            background_tasks.add_task(self.orchestrator_service.cleanup_completed_workflows)
            
            self.logger.info(f"✅ Controller: Workflow {response.workflow_id} started successfully")
            
            return response
            
        except ValueError as e:
            self.logger.error(f"❌ Controller: Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"❌ Controller: Failed to start workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def get_workflow_status(self, workflow_id: str) -> WorkflowStatus:
        """
        Get the current status of a workflow
        
        Args:
            workflow_id: UUID of the workflow
            
        Returns:
            WorkflowStatus with current state information
        """
        try:
            self.logger.info(f"🔍 Controller: Getting status for workflow {workflow_id}")
            
            status = await self.orchestrator_service.get_workflow_status(workflow_id)
            
            if not status:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Workflow {workflow_id} not found"
                )
            
            return status
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"❌ Controller: Failed to get workflow status: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def cancel_workflow(self, workflow_id: str) -> dict:
        """
        Cancel a running workflow
        
        Args:
            workflow_id: UUID of the workflow to cancel
            
        Returns:
            Dictionary with cancellation result
        """
        try:
            self.logger.info(f"🛑 Controller: Cancelling workflow {workflow_id}")
            
            success = await self.orchestrator_service.cancel_workflow(workflow_id)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workflow {workflow_id} not found or cannot be cancelled"
                )
            
            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "message": "Workflow cancelled successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"❌ Controller: Failed to cancel workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def list_active_workflows(self, user_id: Optional[str] = None) -> dict:
        """
        List active workflows, optionally filtered by user
        
        Args:
            user_id: Optional user ID to filter workflows
            
        Returns:
            Dictionary with list of active workflows
        """
        try:
            self.logger.info(f"📋 Controller: Listing workflows for user: {user_id or 'all'}")
            
            active_workflows = self.orchestrator_service.active_workflows
            workflows = []
            
            for workflow_id, workflow_info in active_workflows.items():
                state = workflow_info["state"]
                
                # Filter by user if specified
                if user_id and state.get("user_id") != user_id:
                    continue
                
                workflows.append({
                    "workflow_id": workflow_id,
                    "user_id": state.get("user_id"),
                    "contract_name": state.get("contract_name"),
                    "status": state.get("processing_status"),
                    "current_agent": state.get("current_agent"),
                    "attempt_count": state.get("attempt_count", 0),
                    "quality_score": state.get("quality_score", 0.0),
                    "started_at": workflow_info.get("started_at"),
                    "last_updated": state.get("last_updated_at")
                })
            
            return {
                "active_workflows": workflows,
                "total_count": len(workflows),
                "filtered_by_user": user_id
            }
            
        except Exception as e:
            self.logger.error(f"❌ Controller: Failed to list workflows: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    def _validate_workflow_request(self, request: WorkflowRequest) -> None:
        """
        Validate workflow request parameters
        
        Args:
            request: WorkflowRequest to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not request.user_id or not request.user_id.strip():
            raise ValueError("user_id is required and cannot be empty")
        
        if not request.contract_name or not request.contract_name.strip():
            raise ValueError("contract_name is required and cannot be empty")
        
        if not request.contract_file or not request.contract_file.strip():
            raise ValueError("contract_file is required and cannot be empty")
        
        if request.max_attempts <= 0 or request.max_attempts > 10:
            raise ValueError("max_attempts must be between 1 and 10")
        
        # Additional validation can be added here
        if len(request.contract_name) > 255:
            raise ValueError("contract_name cannot exceed 255 characters")
        
        if len(request.user_id) > 100:
            raise ValueError("user_id cannot exceed 100 characters")


# Singleton controller instance
_orchestrator_controller = None

def get_orchestrator_controller() -> OrchestratorController:
    """Get singleton orchestrator controller instance"""
    global _orchestrator_controller
    if _orchestrator_controller is None:
        _orchestrator_controller = OrchestratorController()
    return _orchestrator_controller