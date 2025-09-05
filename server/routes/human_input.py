from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel, Field
from services.orchestrator_service import get_orchestrator_service
from controller.orchestrator_controller import get_orchestrator_controller
# from agents.validation_agent import ValidationAgent  # TODO: Update to ADK agents
import logging
from datetime import datetime

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
        
        # Debug: Log current active workflows
        active_workflow_ids = list(orchestrator_service.active_workflows.keys())
        logger.info(f"🔍 Current active workflows: {active_workflow_ids}")
        logger.info(f"🎯 Looking for workflow: {request.workflow_id}")
        
        # Get workflow from active workflows
        workflow_info = orchestrator_service.active_workflows.get(request.workflow_id)
        if not workflow_info:
            logger.error(f"❌ Workflow {request.workflow_id} not found in active workflows. Available: {active_workflow_ids}")
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {request.workflow_id} not found or has expired. Available workflows: {len(active_workflow_ids)}"
            )
        
        # Update last accessed time to prevent cleanup
        workflow_info["last_accessed"] = datetime.now()
        
        workflow_state = workflow_info["state"]
        
        # Check if workflow is actually waiting for human input
        current_status = workflow_state.get("processing_status")
        if current_status not in ["needs_human_input", "WAITING_FOR_HUMAN_INPUT"]:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow {request.workflow_id} is not waiting for human input. Current status: {current_status}"
            )
        
        # Validate that we have the required human input request data
        if not workflow_state.get("human_input_request"):
            raise HTTPException(
                status_code=400,
                detail="No human input request found in workflow state"
            )
        
        # Process human input using validation agent
        # validation_agent = ValidationAgent()  # TODO: Update to ADK agents
        raise NotImplementedError("ValidationAgent needs to be updated to use ADK interface")
        
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
        elif processing_status in ["needs_human_input", "WAITING_FOR_HUMAN_INPUT"]:
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

@router.get("/debug/active-workflows")
async def debug_active_workflows():
    """
    Debug endpoint to list all currently active workflows
    """
    try:
        orchestrator_service = get_orchestrator_service()
        
        active_workflows = {}
        for workflow_id, workflow_info in orchestrator_service.active_workflows.items():
            state = workflow_info.get("state", {})
            active_workflows[workflow_id] = {
                "processing_status": state.get("processing_status"),
                "current_agent": state.get("current_agent"),
                "awaiting_human_input": state.get("awaiting_human_input"),
                "user_id": state.get("user_id"),
                "contract_name": state.get("contract_name"),
                "last_updated": state.get("last_updated_at")
            }
        
        return {
            "total_active_workflows": len(active_workflows),
            "workflows": active_workflows,
            "running_workflows": list(orchestrator_service.running_workflows.keys())
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get active workflows: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active workflows: {str(e)}"
        )

@router.post("/debug/create-test-workflow")
async def create_test_workflow_for_human_input():
    """
    Create a test workflow that requires human input for debugging
    """
    try:
        from services.orchestrator_service import get_orchestrator_service
        from schemas.workflow_schemas import WorkflowRequest
        from datetime import datetime
        import uuid
        
        orchestrator_service = get_orchestrator_service()
        workflow_id = str(uuid.uuid4())
        
        # Create a test workflow state that needs human input
        test_state = {
            "workflow_id": workflow_id,
            "user_id": "test_user",
            "contract_name": "Test Contract for Human Input",
            "processing_status": "needs_human_input",
            "awaiting_human_input": True,
            "current_agent": "validation",
            "last_updated_at": datetime.now().isoformat(),
            "human_input_request": {
                "instructions": "Please review and correct the test data",
                "fields": [
                    {
                        "name": "client_name",
                        "label": "Client Name",
                        "type": "string",
                        "value": "Test Client",
                        "required": True
                    },
                    {
                        "name": "payment_amount",
                        "label": "Payment Amount",
                        "type": "number",
                        "value": None,
                        "required": True
                    }
                ],
                "context": {"test": True}
            },
            "validation_results": {
                "is_valid": False,
                "human_input_required": True,
                "issues": [
                    {"field": "payment_amount", "message": "Missing payment amount", "requires_human_input": True}
                ]
            }
        }
        
        # Store in active workflows
        orchestrator_service.active_workflows[workflow_id] = {
            "state": test_state,
            "started_at": datetime.now(),
            "last_accessed": datetime.now(),
            "protected": True,
            "request": {"test_workflow": True}
        }
        
        logger.info(f"🧪 Created test workflow {workflow_id} for human input testing")
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Test workflow created and ready for human input",
            "instructions": "Use POST /api/v1/human-input/submit with this workflow_id",
            "sample_payload": {
                "workflow_id": workflow_id,
                "field_values": {
                    "client_name": "Corrected Client Name",
                    "payment_amount": 1500.00
                },
                "user_notes": "Test human input"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create test workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create test workflow: {str(e)}"
        )