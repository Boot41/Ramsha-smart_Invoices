"""
ADK Integration Service

This service provides integration between the existing FastAPI application 
and the new Google ADK workflow system.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from .orchestrator_adk_workflow import create_adk_workflow, InvoiceProcessingADKWorkflow
from schemas.workflow_schemas import WorkflowRequest, WorkflowResponse, WorkflowStatus, ProcessingStatus

logger = logging.getLogger(__name__)


class ADKIntegrationService:
    """
    Service for integrating Google ADK workflows with the existing FastAPI application
    """
    
    def __init__(self):
        self.adk_workflow: InvoiceProcessingADKWorkflow = create_adk_workflow()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def start_adk_workflow(
        self,
        request: WorkflowRequest
    ) -> WorkflowResponse:
        """
        Start a new ADK workflow for invoice processing
        
        Args:
            request: WorkflowRequest containing user data and contract file
            
        Returns:
            WorkflowResponse with workflow ID and initial status
        """
        
        self.logger.info(f"🚀 Starting ADK workflow - User: {request.user_id}, Contract: {request.contract_name}")
        
        try:
            # Execute ADK workflow
            workflow_result = await self.adk_workflow.execute_workflow(
                user_id=request.user_id,
                contract_file=request.contract_file,
                contract_name=request.contract_name,
                max_attempts=request.max_attempts,
                options=request.options
            )
            
            workflow_id = workflow_result["workflow_id"]
            
            # Store workflow state for monitoring
            self.active_workflows[workflow_id] = {
                "state": workflow_result,
                "created_at": datetime.now().isoformat(),
                "request": request.model_dump()
            }
            
            # Create response
            response = WorkflowResponse(
                workflow_id=workflow_id,
                status=ProcessingStatus.IN_PROGRESS,
                message="ADK workflow started successfully",
                processing_status=workflow_result.get("processing_status", "pending"),
                current_agent=workflow_result.get("current_agent", "workflow_start"),
                progress_percentage=10.0,
                created_at=workflow_result["started_at"],
                adk_enabled=True
            )
            
            self.logger.info(f"✅ ADK workflow started - ID: {workflow_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start ADK workflow: {str(e)}")
            raise e
    
    async def get_adk_workflow_status(self, workflow_id: str) -> WorkflowStatus:
        """
        Get the current status of an ADK workflow
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            WorkflowStatus with detailed information
        """
        
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            self.logger.warning(f"❌ Workflow {workflow_id} not found in active_workflows. Available: {list(self.active_workflows.keys())}")
            return WorkflowStatus(
                workflow_id=workflow_id,
                status=ProcessingStatus.FAILED,
                current_agent="none",
                progress_percentage=0.0,
                last_updated=datetime.now(),
                errors=[f"Workflow {workflow_id} not found"]
            )
        
        workflow_state = workflow_info["state"]
        
        # Use ADK workflow's status method
        status_info = self.adk_workflow.get_workflow_status(workflow_state)
        
        # Convert status string to ProcessingStatus enum
        status_value = status_info["status"]
        if isinstance(status_value, str):
            try:
                status_enum = ProcessingStatus(status_value)
            except ValueError:
                # Map common status values to valid ProcessingStatus
                status_mapping = {
                    "not_found": ProcessingStatus.FAILED,
                    "unknown": ProcessingStatus.IN_PROGRESS,
                    "paused": ProcessingStatus.NEEDS_HUMAN_INPUT,
                    "waiting": ProcessingStatus.IN_PROGRESS,
                    "error": ProcessingStatus.FAILED
                }
                status_enum = status_mapping.get(status_value.lower(), ProcessingStatus.IN_PROGRESS)
        else:
            status_enum = status_value
            
        return WorkflowStatus(
            workflow_id=workflow_id,
            status=status_enum,
            current_agent=status_info["current_agent"],
            progress_percentage=status_info["progress_percentage"],
            last_updated=datetime.fromisoformat(status_info["last_updated_at"]) if status_info.get("last_updated_at") else datetime.now(),
            errors=workflow_state.get("errors", [])
        )
    
    async def resume_adk_workflow(
        self,
        workflow_id: str,
        human_input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused ADK workflow
        
        Args:
            workflow_id: Workflow identifier
            human_input_data: Human input data for validation corrections
            
        Returns:
            Updated workflow state
        """
        
        self.logger.info(f"🔄 Resuming ADK workflow - ID: {workflow_id}")
        
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow_state = workflow_info["state"]
        
        # Resume using ADK workflow
        updated_state = await self.adk_workflow.resume_workflow(
            workflow_state=workflow_state,
            human_input_data=human_input_data
        )
        
        # Update stored state
        workflow_info["state"] = updated_state
        workflow_info["last_resumed_at"] = datetime.now().isoformat()
        
        self.logger.info(f"✅ ADK workflow resumed - ID: {workflow_id}")
        return updated_state
    
    def get_workflow_invoice_data(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the final generated invoice JSON data from completed ADK workflow
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Invoice data or error information
        """
        
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            return {
                "error": "Workflow not found",
                "workflow_id": workflow_id,
                "message": "ADK workflow may have been completed and cleaned up, or the ID is invalid"
            }
        
        workflow_state = workflow_info["state"]
        
        # Check if workflow has final invoice data
        final_invoice_json = workflow_state.get("final_invoice_json")
        correction_completed = workflow_state.get("correction_completed", False)
        
        if not final_invoice_json:
            return {
                "error": "Final invoice not yet generated",
                "workflow_id": workflow_id,
                "current_status": workflow_state.get("processing_status"),
                "current_agent": workflow_state.get("current_agent"),
                "correction_completed": correction_completed,
                "message": "ADK workflow may still be in progress or failed before invoice generation"
            }
        
        return {
            "workflow_id": workflow_id,
            "final_invoice_json": final_invoice_json,
            "correction_completed": correction_completed,
            "processing_status": workflow_state.get("processing_status"),
            "quality_score": workflow_state.get("quality_score", 0.0),
            "confidence_level": workflow_state.get("confidence_level", 0.0),
            "generated_at": workflow_state.get("last_updated_at"),
            "is_adk_workflow": True,
            "metadata": {
                "contract_name": workflow_state.get("contract_name"),
                "user_id": workflow_state.get("user_id"),
                "attempt_count": workflow_state.get("attempt_count", 0),
                "adk_events_count": len(workflow_state.get("adk_events", []))
            }
        }
    
    def list_adk_workflows(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List active ADK workflows
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of workflows
        """
        
        workflows = []
        
        for workflow_id, workflow_info in self.active_workflows.items():
            workflow_state = workflow_info["state"]
            
            # Filter by user if specified
            if user_id and workflow_state.get("user_id") != user_id:
                continue
            
            workflows.append({
                "workflow_id": workflow_id,
                "user_id": workflow_state.get("user_id"),
                "contract_name": workflow_state.get("contract_name"),
                "status": workflow_state.get("processing_status"),
                "current_agent": workflow_state.get("current_agent"),
                "workflow_completed": workflow_state.get("workflow_completed", False),
                "workflow_paused": workflow_state.get("workflow_paused", False),
                "created_at": workflow_info.get("created_at"),
                "last_updated_at": workflow_state.get("last_updated_at"),
                "is_adk_workflow": True
            })
        
        return {
            "workflows": workflows,
            "total_count": len(workflows),
            "adk_enabled": True
        }
    
    async def cancel_adk_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Cancel an ADK workflow
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Cancellation result
        """
        
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            return {
                "error": "Workflow not found",
                "workflow_id": workflow_id
            }
        
        # Update state to cancelled
        workflow_info["state"]["processing_status"] = "cancelled"
        workflow_info["state"]["workflow_completed"] = True
        workflow_info["state"]["cancelled_at"] = datetime.now().isoformat()
        
        self.logger.info(f"🛑 ADK workflow cancelled - ID: {workflow_id}")
        
        return {
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "ADK workflow cancelled successfully",
            "cancelled_at": workflow_info["state"]["cancelled_at"]
        }
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete workflow state for a given workflow ID
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Complete workflow state dictionary or None if not found
        """
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            return None
        
        return workflow_info["state"]
    
    async def resume_workflow_after_human_input(
        self,
        workflow_id: str, 
        human_input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume workflow execution after receiving human input corrections
        
        Args:
            workflow_id: Workflow identifier
            human_input_data: User corrections and field values
            
        Returns:
            Updated workflow state after processing human input
        """
        self.logger.info(f"🔄 Resuming ADK workflow after human input - ID: {workflow_id}")
        
        # Get current workflow state
        workflow_state = await self.get_workflow_state(workflow_id)
        if not workflow_state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Resume workflow using the ADK workflow system
        updated_state = await self.adk_workflow.resume_workflow(
            workflow_state=workflow_state,
            human_input_data=human_input_data
        )
        
        # Update stored workflow state
        self.active_workflows[workflow_id]["state"] = updated_state
        self.active_workflows[workflow_id]["last_resumed_at"] = datetime.now().isoformat()
        
        self.logger.info(f"✅ ADK workflow resumed after human input - ID: {workflow_id}")
        return updated_state


# Global ADK integration service instance
_adk_service: Optional[ADKIntegrationService] = None


def get_adk_integration_service() -> ADKIntegrationService:
    """
    Get the global ADK integration service instance
    
    Returns:
        ADKIntegrationService instance
    """
    global _adk_service
    if _adk_service is None:
        _adk_service = ADKIntegrationService()
    return _adk_service