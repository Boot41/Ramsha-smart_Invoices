from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel, Field
from services.orchestrator_service import get_orchestrator_service
from controller.orchestrator_controller import get_orchestrator_controller
from agents.validation_agent import ValidationAgent
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/human-input", tags=["human-input"])

class HumanInputRequest(BaseModel):
    """Request model for human input to resolve validation issues"""
    workflow_id: str = Field(..., description="Workflow ID that needs human input")
    field_values: Dict[str, Any] = Field(..., description="Field values provided by human")
    user_notes: str = Field(default="", description="Optional notes from user")

class HumanInputResponse(BaseModel):
    """Response after processing human input"""
    success: bool
    message: str
    workflow_id: str
    validation_status: str
    updated_fields: Dict[str, Any]
    remaining_issues: int = 0

class GeneralHumanInputRequest(BaseModel):
    """Request model for general human input to waiting workflows"""
    task_id: str = Field(..., description="Task/Workflow ID that is waiting for input")
    user_input: str = Field(..., description="User input text")

class GeneralHumanInputResponse(BaseModel):
    """Response after processing general human input"""
    success: bool
    message: str
    task_id: str
    status: str

@router.post("/input", response_model=GeneralHumanInputResponse)
async def submit_general_human_input(request: GeneralHumanInputRequest):
    """
    Submit general human input to resume a waiting workflow
    
    This endpoint allows users to provide input when a workflow is paused
    waiting for human interaction using the new asyncio.Event-based system.
    """
    try:
        logger.info(f"📥 Receiving general human input for task {request.task_id}")
        
        # Get orchestrator controller
        orchestrator_controller = get_orchestrator_controller()
        
        # Process the human input
        result = await orchestrator_controller.process_human_input(
            request.task_id, 
            request.user_input
        )
        
        return GeneralHumanInputResponse(
            success=True,
            message=result["message"],
            task_id=result["task_id"],
            status=result["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process general human input for task {request.task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process human input: {str(e)}"
        )

@router.post("/submit", response_model=HumanInputResponse)
async def submit_human_input(request: HumanInputRequest):
    """
    Submit human input to resolve validation issues and continue workflow
    
    This endpoint allows users to provide missing or corrected data when
    validation finds issues that require human intervention.
    """
    try:
        logger.info(f"📝 Receiving human input for workflow {request.workflow_id}")
        
        # Get orchestrator service to access workflow state
        orchestrator_service = get_orchestrator_service()
        
        # Get workflow from active workflows
        workflow_info = orchestrator_service.active_workflows.get(request.workflow_id)
        if not workflow_info:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {request.workflow_id} not found or has expired"
            )
        
        workflow_state = workflow_info["state"]
        
        # Check if workflow is actually waiting for human input
        if workflow_state.get("processing_status") != "needs_human_input":
            raise HTTPException(
                status_code=400,
                detail=f"Workflow {request.workflow_id} is not waiting for human input. Current status: {workflow_state.get('processing_status')}"
            )
        
        # Validate that we have the required human input request data
        if not workflow_state.get("human_input_request"):
            raise HTTPException(
                status_code=400,
                detail="No human input request found in workflow state"
            )
        
        # Process human input using validation agent
        validation_agent = ValidationAgent()
        
        # Add user notes to the input data if provided
        field_values_with_notes = request.field_values.copy()
        if request.user_notes:
            field_values_with_notes["_user_notes"] = request.user_notes
        
        # Process the human input
        updated_state = validation_agent.handle_human_input_response(
            state=workflow_state,
            human_input_data=field_values_with_notes
        )
        
        # Update the stored workflow state
        orchestrator_service.active_workflows[request.workflow_id]["state"] = updated_state
        
        # Determine current validation status
        validation_results = updated_state.get("validation_results", {})
        processing_status = updated_state.get("processing_status", "unknown")
        
        if processing_status == "success":
            validation_status = "resolved"
            message = "✅ Human input successfully resolved all validation issues. Workflow will continue."
        elif processing_status == "needs_human_input":
            validation_status = "partial_resolution" 
            remaining_issues = len([issue for issue in validation_results.get("issues", []) if issue.get("requires_human_input")])
            message = f"⚠️ Some validation issues remain. {remaining_issues} issues still require attention."
        else:
            validation_status = "error"
            message = f"❌ Error processing human input: {processing_status}"
        
        # If workflow can continue, restart it
        if processing_status == "success":
            try:
                # Continue workflow execution
                final_state = await orchestrator_service._execute_workflow(request.workflow_id, updated_state)
                orchestrator_service.active_workflows[request.workflow_id]["state"] = final_state
                logger.info(f"✅ Workflow {request.workflow_id} resumed successfully")
            except Exception as e:
                logger.error(f"❌ Failed to resume workflow {request.workflow_id}: {str(e)}")
                # Don't raise exception here, human input was still processed successfully
        
        return HumanInputResponse(
            success=True,
            message=message,
            workflow_id=request.workflow_id,
            validation_status=validation_status,
            updated_fields=field_values_with_notes,
            remaining_issues=len([issue for issue in validation_results.get("issues", []) if issue.get("requires_human_input", False)])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process human input for workflow {request.workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process human input: {str(e)}"
        )

@router.get("/request/{workflow_id}")
async def get_human_input_request(workflow_id: str):
    """
    Get the current human input request for a workflow
    
    Returns the validation issues and required fields that need human attention.
    """
    try:
        orchestrator_service = get_orchestrator_service()
        
        workflow_info = orchestrator_service.active_workflows.get(workflow_id)
        if not workflow_info:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        
        workflow_state = workflow_info["state"]
        human_input_request = workflow_state.get("human_input_request")
        
        if not human_input_request:
            raise HTTPException(
                status_code=404,
                detail=f"No human input request found for workflow {workflow_id}"
            )
        
        return {
            "workflow_id": workflow_id,
            "request": human_input_request,
            "validation_results": workflow_state.get("validation_results"),
            "contract_name": workflow_state.get("contract_name"),
            "user_id": workflow_state.get("user_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get human input request for workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get human input request: {str(e)}"
        )

@router.get("/status/{workflow_id}")
async def get_validation_status(workflow_id: str):
    """
    Get the current validation status for a workflow
    
    Returns validation results, issues, and human input requirements.
    """
    try:
        orchestrator_service = get_orchestrator_service()
        
        workflow_info = orchestrator_service.active_workflows.get(workflow_id)
        if not workflow_info:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        
        workflow_state = workflow_info["state"]
        validation_results = workflow_state.get("validation_results", {})
        
        return {
            "workflow_id": workflow_id,
            "processing_status": workflow_state.get("processing_status"),
            "validation_results": validation_results,
            "human_input_required": validation_results.get("human_input_required", False),
            "validation_score": validation_results.get("validation_score", 0.0),
            "confidence_score": validation_results.get("confidence_score", 0.0),
            "issues_summary": {
                "total_issues": validation_results.get("issues_count", 0),
                "missing_required_fields": validation_results.get("missing_required_fields_count", 0),
                "validation_timestamp": validation_results.get("validation_timestamp")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get validation status for workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation status: {str(e)}"
        )