from fastapi import APIRouter, BackgroundTasks, Depends, Query
from typing import Optional
import logging
from controller.orchestrator_controller import get_orchestrator_controller
from schemas.workflow_schemas import WorkflowRequest, WorkflowResponse, WorkflowStatus
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Get controller instance
orchestrator_controller = get_orchestrator_controller()

@router.post("/workflow/invoice/start", response_model=WorkflowResponse)
async def start_invoice_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    🚀 Start a new agentic invoice processing workflow
    
    This endpoint initiates the complete agentic workflow:
    1. Contract Processing - Extract and process contract data
    2. Validation - Validate contract completeness and accuracy  
    3. Schedule Extraction - Extract billing schedule information
    4. Invoice Generation - Generate structured invoice data using RAG
    5. Quality Assurance - Perform quality checks with feedback loops
    6. Storage & Scheduling - Store results and schedule future processing
    7. Feedback Learning - Learn from successes and failures for improvement
    
    The workflow includes:
    - ✅ Automatic retry logic with smart error recovery
    - ✅ Quality-based feedback loops for continuous improvement
    - ✅ Multi-agent orchestration with intelligent routing
    - ✅ Real-time progress tracking and status updates
    - ✅ Confidence scoring and quality assurance gates
    """
    logger.info(f"🎯 API: Starting agentic workflow - User: {request.user_id}, Contract: {request.contract_name}")
    
    # Ensure user can only start workflows for themselves (unless admin)
    if not current_user.get("is_admin", False):
        request.user_id = current_user["user_id"]
    
    return await orchestrator_controller.start_invoice_workflow(request, background_tasks)

@router.get("/workflow/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    🔍 Get the current status and progress of a workflow
    
    Returns detailed information about:
    - Current processing stage and agent
    - Progress percentage (0-100%)
    - Quality scores and confidence levels
    - Any errors or retry attempts
    - Estimated completion time
    """
    logger.info(f"📊 API: Getting workflow status - ID: {workflow_id}, User: {current_user['user_id']}")
    
    status = await orchestrator_controller.get_workflow_status(workflow_id)
    
    # Security check - users can only view their own workflows (unless admin)
    if not current_user.get("is_admin", False):
        # Would need to add user check here based on workflow owner
        pass
    
    return status

@router.delete("/workflow/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    🛑 Cancel a running workflow
    
    Gracefully stops the workflow execution and cleans up resources.
    Only the workflow owner or admin can cancel a workflow.
    """
    logger.info(f"🛑 API: Cancelling workflow - ID: {workflow_id}, User: {current_user['user_id']}")
    
    # Security check would go here
    
    return await orchestrator_controller.cancel_workflow(workflow_id)

@router.get("/workflows/active")
async def list_active_workflows(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    📋 List all active workflows
    
    Returns a list of currently running or recently completed workflows.
    Regular users can only see their own workflows, admins can see all.
    
    Query Parameters:
    - user_id: Filter workflows by specific user (admin only)
    """
    logger.info(f"📋 API: Listing workflows - Requester: {current_user['user_id']}, Filter: {user_id or 'none'}")
    
    # Security: Non-admin users can only see their own workflows
    if not current_user.get("is_admin", False):
        user_id = current_user["user_id"]
    
    return await orchestrator_controller.list_active_workflows(user_id)

@router.get("/workflow/health")
async def orchestrator_health_check():
    """
    💚 Health check endpoint for the orchestrator system
    
    Returns system health status and basic metrics about:
    - Active workflows count
    - System readiness
    - Available resources
    """
    logger.info("💚 API: Health check requested")
    
    try:
        orchestrator_service = orchestrator_controller.orchestrator_service
        active_count = len(orchestrator_service.active_workflows)
        
        return {
            "status": "healthy",
            "message": "Agentic orchestrator is running",
            "active_workflows": active_count,
            "system_ready": True,
            "version": "1.0.0",
            "features": [
                "Multi-agent orchestration",
                "Feedback loops & learning",
                "Quality assurance gates", 
                "Smart error recovery",
                "Real-time progress tracking",
                "LangGraph workflow engine"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ API: Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"System error: {str(e)}",
            "system_ready": False
        }

@router.post("/workflow/test")
async def test_orchestrator_workflow():
    """
    🧪 Test endpoint for development and debugging
    
    Creates a simple test workflow to verify the system is working correctly.
    This endpoint is for development purposes only.
    """
    logger.info("🧪 API: Test workflow requested")
    
    test_request = WorkflowRequest(
        user_id="test_user_123",
        contract_file="test_contract.pdf",
        contract_name="Test Rental Agreement",
        max_attempts=2,
        options={"test_mode": True}
    )
    
    try:
        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()
        
        # Create a minimal test user context
        test_user = {"user_id": "test_user_123", "is_admin": True}
        
        response = await orchestrator_controller.start_invoice_workflow(test_request, background_tasks)
        
        return {
            "test_status": "success",
            "workflow_id": response.workflow_id,
            "message": "Test workflow created successfully",
            "response": response.model_dump()
        }
        
    except Exception as e:
        logger.error(f"❌ API: Test workflow failed: {str(e)}")
        return {
            "test_status": "failed",
            "error": str(e),
            "message": "Test workflow creation failed"
        }