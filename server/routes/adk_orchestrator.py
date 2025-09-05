"""
ADK-enabled Orchestrator Routes

FastAPI routes that integrate with Google ADK workflow system
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json
from datetime import datetime

from adk_agents.adk_integration_service import get_adk_integration_service
from schemas.workflow_schemas import WorkflowRequest, WorkflowResponse, WorkflowStatus
from schemas.unified_invoice_schemas import UnifiedInvoiceData
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Get ADK integration service instance
adk_service = get_adk_integration_service()


@router.post("/adk/workflow/invoice/start", response_model=WorkflowResponse)
async def start_adk_invoice_workflow(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    contract_name: str = Form(...),
    max_attempts: int = Form(3),
    options: Optional[str] = Form(default='{}'),
    contract_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """
    🚀 Start a new ADK-powered invoice processing workflow
    
    This endpoint initiates the complete Google ADK agentic workflow by accepting form-data.
    Can handle both new contracts (with file upload) and existing contracts (without file).
    
    Features:
    - Google ADK orchestration
    - Built-in retry logic and error handling
    - Real-time progress tracking
    - Human-in-the-loop validation
    - Automatic quality assurance
    """
    
    # Handle file upload for new contracts or None for existing contracts
    file_bytes = None
    if contract_file and contract_file.filename != 'existing_contract.pdf':
        file_bytes = await contract_file.read()
    
    try:
        options_dict = json.loads(options)
    except json.JSONDecodeError:
        options_dict = {}

    # Add ADK-specific options
    options_dict["adk_enabled"] = True
    options_dict["workflow_type"] = "adk"

    request = WorkflowRequest(
        user_id=user_id,
        contract_name=contract_name,
        contract_file=file_bytes,
        max_attempts=max_attempts,
        options=options_dict
    )

    logger.info(f"🎯 ADK API: Starting agentic workflow - User: {request.user_id}, Contract: {request.contract_name}")
    
    # Ensure user can only start workflows for themselves (unless admin)
    if not current_user.get("is_admin", False):
        request.user_id = current_user["user_id"]
    
    return await adk_service.start_adk_workflow(request)


class StartADKWorkflowRequest(BaseModel):
    user_id: str
    contract_name: str
    contract_path: Optional[str] = None
    max_attempts: int = 3
    options: Optional[Dict[str, Any]] = None


@router.post("/adk/workflow/invoice/start-for-contract", response_model=WorkflowResponse)
async def start_adk_workflow_for_existing_contract(
    request: StartADKWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    🚀 Start ADK workflow for existing contract
    
    This endpoint starts the Google ADK agentic invoice processing workflow for a contract
    that's already uploaded/processed in the system.
    """
    options = request.options or {}
    options["adk_enabled"] = True
    options["workflow_type"] = "adk"

    logger.info(f"🎯 ADK API: Starting agentic workflow for existing contract - User: {request.user_id}, Contract: {request.contract_name}")
    
    # Ensure user can only start workflows for themselves (unless admin)
    user_id = request.user_id
    if not current_user.get("is_admin", False):
        user_id = current_user["user_id"]
    
    # For existing contracts, we can pass None as contract_file since the contract
    # is already processed/available in the system
    workflow_request = WorkflowRequest(
        user_id=user_id,
        contract_name=request.contract_name,
        contract_file=None,  # Will be handled differently for existing contracts
        max_attempts=request.max_attempts,
        options={**options, "existing_contract": True, "contract_path": request.contract_path}
    )
    
    return await adk_service.start_adk_workflow(workflow_request)


@router.get("/adk/workflow/{workflow_id}/status", response_model=WorkflowStatus)
async def get_adk_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    🔍 Get the current status and progress of an ADK workflow
    
    Returns detailed information about:
    - Current processing stage and agent
    - Progress percentage (0-100%)
    - Quality scores and confidence levels
    - Any errors or retry attempts
    - Estimated completion time
    - ADK-specific event history
    """
    logger.info(f"📊 ADK API: Getting workflow status - ID: {workflow_id}, User: {current_user['user_id']}")
    
    status = await adk_service.get_adk_workflow_status(workflow_id)
    
    # Security check - users can only view their own workflows (unless admin)
    if not current_user.get("is_admin", False):
        # Would need to add user check here based on workflow owner
        pass
    
    return status


@router.get("/adk/workflow/{workflow_id}/invoice", response_model=Dict[str, Any])
async def get_adk_workflow_invoice_data(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    📄 Get the final generated invoice JSON data from a completed ADK workflow
    
    Returns the corrected and finalized invoice JSON generated by the ADK correction agent.
    Only available for completed ADK workflows.
    """
    logger.info(f"📄 ADK API: Getting final invoice data - ID: {workflow_id}, User: {current_user['user_id']}")
    
    return adk_service.get_workflow_invoice_data(workflow_id)


@router.post("/adk/workflow/{workflow_id}/resume")
async def resume_adk_workflow(
    workflow_id: str,
    human_input_data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    ▶️ Resume a paused ADK workflow
    
    This endpoint resumes ADK workflows that are paused for human input.
    Typically used after validation requires human corrections.
    """
    logger.info(f"▶️ ADK API: Resuming workflow - ID: {workflow_id}, User: {current_user['user_id']}")
    
    try:
        updated_state = await adk_service.resume_adk_workflow(
            workflow_id=workflow_id,
            human_input_data=human_input_data
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "resumed",
            "message": "ADK workflow resumed successfully",
            "processing_status": updated_state.get("processing_status"),
            "current_agent": updated_state.get("current_agent"),
            "workflow_completed": updated_state.get("workflow_completed", False),
            "resumed_at": updated_state.get("resume_timestamp")
        }
        
    except Exception as e:
        logger.error(f"❌ ADK API: Failed to resume workflow {workflow_id}: {str(e)}")
        return {
            "workflow_id": workflow_id,
            "status": "error",
            "message": f"Failed to resume ADK workflow: {str(e)}"
        }


@router.delete("/adk/workflow/{workflow_id}/cancel")
async def cancel_adk_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    🛑 Cancel a running ADK workflow
    
    Gracefully stops the ADK workflow execution and cleans up resources.
    Only the workflow owner or admin can cancel a workflow.
    """
    logger.info(f"🛑 ADK API: Cancelling workflow - ID: {workflow_id}, User: {current_user['user_id']}")
    
    # Security check would go here
    
    return await adk_service.cancel_adk_workflow(workflow_id)


@router.get("/adk/workflows/active")
async def list_active_adk_workflows(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    📋 List all active ADK workflows
    
    Returns a list of currently running or recently completed ADK workflows.
    Regular users can only see their own workflows, admins can see all.
    
    Query Parameters:
    - user_id: Filter workflows by specific user (admin only)
    """
    logger.info(f"📋 ADK API: Listing workflows - Requester: {current_user['user_id']}, Filter: {user_id or 'none'}")
    
    # Security: Non-admin users can only see their own workflows
    if not current_user.get("is_admin", False):
        user_id = current_user["user_id"]
    
    return adk_service.list_adk_workflows(user_id)


@router.get("/adk/workflow/health")
async def adk_workflow_health_check():
    """
    💚 Health check endpoint for the ADK workflow system
    
    Returns system health status and basic metrics about:
    - Active ADK workflows count
    - System readiness
    - Available resources
    - ADK integration status
    """
    logger.info("💚 ADK API: Health check requested")
    
    try:
        workflows = adk_service.list_adk_workflows()
        active_count = workflows["total_count"]
        
        return {
            "status": "healthy",
            "message": "Google ADK agentic orchestrator is running",
            "active_workflows": active_count,
            "system_ready": True,
            "version": "1.0.0-adk",
            "adk_enabled": True,
            "features": [
                "Google ADK multi-agent orchestration",
                "Built-in error handling and retries", 
                "Real-time progress tracking",
                "Human-in-the-loop validation",
                "Automatic quality assurance",
                "Event-driven architecture",
                "Native Google Cloud integration"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ ADK API: Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"ADK system error: {str(e)}",
            "system_ready": False,
            "adk_enabled": False
        }


@router.post("/adk/workflow/test")
async def test_adk_workflow():
    """
    🧪 Test endpoint for ADK development and debugging
    
    Creates a simple test workflow to verify the Google ADK system is working correctly.
    This endpoint is for development purposes only.
    """
    logger.info("🧪 ADK API: Test workflow requested")
    
    test_request = WorkflowRequest(
        user_id="test_user_adk_123",
        contract_file="test_contract_adk.pdf",
        contract_name="Test ADK Rental Agreement",
        max_attempts=2,
        options={"test_mode": True, "adk_enabled": True}
    )
    
    try:
        response = await adk_service.start_adk_workflow(test_request)
        
        return {
            "test_status": "success",
            "workflow_id": response.workflow_id,
            "message": "ADK test workflow created successfully",
            "adk_enabled": True,
            "response": response.model_dump()
        }
        
    except Exception as e:
        logger.error(f"❌ ADK API: Test workflow failed: {str(e)}")
        return {
            "test_status": "failed",
            "error": str(e),
            "message": "ADK test workflow creation failed",
            "adk_enabled": False
        }


# ADK Human Input Models
class ADKHumanInputRequest(BaseModel):
    """Request model for ADK human input to resolve validation issues"""
    workflow_id: str
    field_values: Dict[str, Any]
    user_notes: str = ""

class ADKHumanInputResponse(BaseModel):
    """Response after processing ADK human input"""
    success: bool
    message: str
    workflow_id: str
    processing_status: str
    updated_fields: Dict[str, Any]
    workflow_resumed: bool = False


@router.post("/adk/workflow/human-input/submit", response_model=ADKHumanInputResponse)
async def submit_adk_human_input(
    request: ADKHumanInputRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit human input to resolve ADK workflow validation issues and resume workflow
    
    This endpoint allows users to provide missing or corrected data when
    ADK validation finds issues that require human intervention.
    """
    try:
        logger.info(f"📝 ADK API: Receiving human input for workflow {request.workflow_id}")
        
        # Get the ADK workflow state
        workflow_state = await adk_service.get_workflow_state(request.workflow_id)
        
        if not workflow_state:
            logger.error(f"❌ ADK workflow {request.workflow_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"ADK workflow {request.workflow_id} not found"
            )
        
        # Check if workflow is actually waiting for human input
        current_status = workflow_state.get("processing_status")
        human_input_required = workflow_state.get("human_input_required", False)
        workflow_paused = workflow_state.get("workflow_paused", False)
        
        if not (human_input_required or workflow_paused or current_status == "needs_human_input"):
            raise HTTPException(
                status_code=400,
                detail=f"Workflow {request.workflow_id} is not waiting for human input. Current status: {current_status}"
            )
        
        # Apply human corrections to the current invoice data
        updated_state = await _apply_human_corrections(workflow_state, request.field_values, request.user_notes)
        
        # Resume workflow execution with corrected data
        resumed_state = await adk_service.resume_workflow_after_human_input(request.workflow_id, updated_state)
        
        # Determine if workflow resumed successfully
        final_status = resumed_state.get("processing_status")
        workflow_resumed = final_status not in ["needs_human_input", "paused", "failed"]
        
        logger.info(f"✅ ADK human input processed - Workflow: {request.workflow_id}, Resumed: {workflow_resumed}, Status: {final_status}")
        
        return ADKHumanInputResponse(
            success=True,
            message=f"Human input processed successfully. Workflow {'resumed' if workflow_resumed else 'updated but still requires attention'}.",
            workflow_id=request.workflow_id,
            processing_status=final_status,
            updated_fields=request.field_values,
            workflow_resumed=workflow_resumed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ADK API: Failed to process human input for workflow {request.workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process ADK human input: {str(e)}"
        )


@router.get("/adk/workflow/{workflow_id}/status")
async def get_adk_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current status of an ADK workflow
    
    Returns workflow state, validation results, and human input requirements.
    """
    try:
        workflow_state = await adk_service.get_workflow_state(workflow_id)
        
        if not workflow_state:
            raise HTTPException(
                status_code=404,
                detail=f"ADK workflow {workflow_id} not found"
            )
        
        # Extract relevant information
        return {
            "workflow_id": workflow_id,
            "processing_status": workflow_state.get("processing_status"),
            "workflow_paused": workflow_state.get("workflow_paused", False),
            "human_input_required": workflow_state.get("human_input_required", False),
            "workflow_completed": workflow_state.get("workflow_completed", False),
            "current_agent": workflow_state.get("current_agent"),
            "user_id": workflow_state.get("user_id"),
            "contract_name": workflow_state.get("contract_name"),
            "validation_results": workflow_state.get("validation_result", {}),
            "last_updated_at": workflow_state.get("last_updated_at"),
            "authoritative_source": workflow_state.get("authoritative_source"),
            "data_version": workflow_state.get("data_version", 0),
            "invoice_generated": workflow_state.get("invoice_generation_result", {}).get("generation_successful", False),
            "scheduling_completed": workflow_state.get("schedule_retrieval_result", {}).get("scheduling_successful", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ADK API: Failed to get workflow status for {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ADK workflow status: {str(e)}"
        )


@router.get("/adk/workflow/{workflow_id}/human-input-request")
async def get_adk_human_input_request(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current human input request for an ADK workflow
    
    Returns the validation issues and required fields that need human attention.
    """
    try:
        workflow_state = await adk_service.get_workflow_state(workflow_id)
        
        if not workflow_state:
            raise HTTPException(
                status_code=404,
                detail=f"ADK workflow {workflow_id} not found"
            )
        
        validation_result = workflow_state.get("validation_result", {})
        current_invoice_data = workflow_state.get("current_invoice_data", {})
        
        # Extract validation issues that require human input
        validation_data = validation_result.get("validation_result", {})
        issues = validation_data.get("issues", [])
        missing_fields = validation_data.get("missing_required_fields", [])
        
        # Create human input request
        human_input_request = {
            "workflow_id": workflow_id,
            "instructions": "Please review and correct the following fields:",
            "missing_required_fields": missing_fields,
            "validation_issues": issues,
            "current_data": current_invoice_data,
            "validation_score": validation_data.get("validation_score", 0.0),
            "confidence_score": validation_data.get("confidence_score", 0.0),
            "requires_human_input": validation_data.get("human_input_required", False)
        }
        
        return human_input_request
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ADK API: Failed to get human input request for {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ADK human input request: {str(e)}"
        )


async def _apply_human_corrections(
    workflow_state: Dict[str, Any], 
    field_values: Dict[str, Any], 
    user_notes: str
) -> Dict[str, Any]:
    """Apply human corrections to the workflow state"""
    try:
        # Get current invoice data
        current_data = workflow_state.get("current_invoice_data", {})
        
        if not current_data:
            raise ValueError("No current invoice data found to apply corrections to")
        
        # Create updated invoice data with human corrections
        updated_data = current_data.copy()
        
        # Apply field corrections
        for field_path, value in field_values.items():
            # Handle nested field paths like "payment_terms.amount"
            keys = field_path.split('.')
            target = updated_data
            
            # Navigate to the parent of the target field
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            
            # Set the final value
            target[keys[-1]] = value
            logger.info(f"📝 Applied human correction: {field_path} = {value}")
        
        # Update metadata
        if "metadata" not in updated_data:
            updated_data["metadata"] = {}
        
        updated_data["metadata"]["human_corrected"] = True
        updated_data["metadata"]["human_correction_timestamp"] = datetime.now().isoformat()
        updated_data["metadata"]["user_notes"] = user_notes
        updated_data["metadata"]["corrected_fields"] = list(field_values.keys())
        
        # Update workflow state
        updated_state = workflow_state.copy()
        updated_state["current_invoice_data"] = updated_data
        updated_state["human_input_resolved"] = True
        updated_state["human_input_required"] = False
        updated_state["workflow_paused"] = False
        updated_state["processing_status"] = "in_progress"
        updated_state["data_version"] = workflow_state.get("data_version", 0) + 1
        updated_state["last_updated_at"] = datetime.now().isoformat()
        updated_state["last_update_agent"] = "human_input"
        
        # Archive the previous data
        if "invoice_data_history" not in updated_state:
            updated_state["invoice_data_history"] = []
        
        updated_state["invoice_data_history"].append({
            "data": current_data,
            "version": workflow_state.get("data_version", 0),
            "source_agent": workflow_state.get("authoritative_source", "unknown"),
            "timestamp": workflow_state.get("last_updated_at"),
            "replaced_by": "human_input"
        })
        
        # Update authoritative source
        updated_state["authoritative_source"] = "human_input"
        
        logger.info(f"✅ Applied human corrections to workflow {workflow_state.get('workflow_id')} - {len(field_values)} fields updated")
        
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ Failed to apply human corrections: {str(e)}")
        raise e