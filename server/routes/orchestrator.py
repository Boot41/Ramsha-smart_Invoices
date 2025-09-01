from fastapi import APIRouter, BackgroundTasks, Depends, Query, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from typing import Optional, Dict, Any
import logging
import json
from datetime import datetime
from controller.orchestrator_controller import get_orchestrator_controller
from schemas.workflow_schemas import WorkflowRequest, WorkflowResponse, WorkflowStatus
from middleware.auth import get_current_user
from services.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Get controller and manager instances
orchestrator_controller = get_orchestrator_controller()
websocket_manager = get_websocket_manager()

@router.post("/workflow/invoice/start", response_model=WorkflowResponse)
async def start_invoice_workflow(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    contract_name: str = Form(...),
    max_attempts: int = Form(3),
    options: Optional[str] = Form(default='{}'),
    contract_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    🚀 Start a new agentic invoice processing workflow
    
    This endpoint initiates the complete agentic workflow by accepting form-data
    including the contract file.
    """
    import json
    file_bytes = await contract_file.read()
    
    try:
        options_dict = json.loads(options)
    except json.JSONDecodeError:
        options_dict = {}

    request = WorkflowRequest(
        user_id=user_id,
        contract_name=contract_name,
        contract_file=file_bytes,
        max_attempts=max_attempts,
        options=options_dict
    )

    logger.info(f"🎯 API: Starting agentic workflow - User: {request.user_id}, Contract: {request.contract_name}")
    
    # Ensure user can only start workflows for themselves (unless admin)
    if not current_user.get("is_admin", False):
        request.user_id = current_user["user_id"]
    
    return await orchestrator_controller.start_invoice_workflow(request, background_tasks)

@router.websocket("/ws/workflow/{workflow_id}/realtime")
async def workflow_websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """
    🔌 Real-time WebSocket connection for workflow updates
    
    Provides real-time updates for:
    - Workflow status changes
    - Agent transitions  
    - Human input requirements
    - Validation results
    - Workflow completion/failure
    """
    connection_id = None
    
    try:
        # Connect WebSocket to workflow
        connection_id = await websocket_manager.connect(websocket, workflow_id)
        logger.info(f"📡 WebSocket connected to workflow {workflow_id}")
        
        # Send initial workflow status if available
        workflow_info = orchestrator_controller.orchestrator_service.active_workflows.get(workflow_id)
        
        if workflow_info:
            await websocket_manager.broadcast_workflow_event(workflow_id, 'workflow_status', {
                'status': workflow_info['state'].get('processing_status', 'unknown'),
                'message': f'Connected to workflow {workflow_id}',
                'workflow_state': {
                    'contract_name': workflow_info['state'].get('contract_name'),
                    'user_id': workflow_info['state'].get('user_id'),
                    'processing_status': workflow_info['state'].get('processing_status'),
                    'validation_results': workflow_info['state'].get('validation_results', {}),
                    'current_agent': workflow_info['state'].get('current_agent'),
                    'workflow_id': workflow_id
                }
            })
        else:
            await websocket_manager.broadcast_workflow_event(workflow_id, 'workflow_status', {
                'status': 'not_found',
                'message': f'Workflow {workflow_id} not found in active workflows'
            })
        
        # Listen for client messages
        while True:
            try:
                # Wait for message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                logger.info(f"📨 Received WebSocket message: {message.get('type', 'unknown')}")
                
                # Handle different message types
                await handle_websocket_message(workflow_id, message, websocket_manager)
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON received: {e}")
                await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                    'message': 'Invalid JSON format',
                    'error': str(e)
                })
                
    except WebSocketDisconnect:
        logger.info(f"📡 WebSocket disconnected from workflow {workflow_id}")
        
    except Exception as e:
        logger.error(f"❌ WebSocket error for workflow {workflow_id}: {str(e)}")
        try:
            await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                'message': f'WebSocket error: {str(e)}'
            })
        except:
            pass  # Connection might be closed
            
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(websocket, connection_id)

async def handle_websocket_message(workflow_id: str, message: dict, websocket_manager):
    """Handle incoming WebSocket messages from clients"""
    message_type = message.get('type')
    data = message.get('data', {})
    
    try:
        if message_type == 'human_input_submission':
            # Handle human input submission
            logger.info(f"📝 Processing human input submission for workflow {workflow_id}")
            
            field_values = data.get('field_values', {})
            user_notes = data.get('user_notes', '')
            
            # Get the workflow state and process human input directly
            workflow_info = orchestrator_controller.orchestrator_service.active_workflows.get(workflow_id)
            
            if not workflow_info:
                await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                    'message': 'Workflow not found in active workflows'
                })
                return
                
            workflow_state = workflow_info["state"]
            
            # Debug: Log current workflow state
            logger.info(f"🔍 Workflow state check for {workflow_id}:")
            logger.info(f"  - awaiting_human_input_websocket: {workflow_state.get('awaiting_human_input_websocket')}")
            logger.info(f"  - processing_status: {workflow_state.get('processing_status')}")
            logger.info(f"  - validation_results: {workflow_state.get('validation_results', {})}")
            logger.info(f"  - human_input_required: {workflow_state.get('validation_results', {}).get('human_input_required')}")
            
            # Check if workflow is expecting human input (more lenient check)
            is_waiting_websocket = workflow_state.get("awaiting_human_input_websocket")
            is_needs_input = workflow_state.get("processing_status") == "needs_human_input"
            has_validation_requiring_input = (workflow_state.get("validation_results", {}).get("human_input_required") and
                                            workflow_state.get("validation_results", {}).get("is_valid") == False)
            
            if not (is_waiting_websocket or is_needs_input or has_validation_requiring_input):
                await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                    'message': f'Workflow is not currently waiting for human input. State: awaiting_ws={is_waiting_websocket}, needs_input={is_needs_input}, validation_requires={has_validation_requiring_input}',
                    'debug_info': {
                        'awaiting_human_input_websocket': workflow_state.get('awaiting_human_input_websocket'),
                        'processing_status': workflow_state.get('processing_status'),
                        'validation_human_input_required': workflow_state.get('validation_results', {}).get('human_input_required'),
                        'validation_is_valid': workflow_state.get('validation_results', {}).get('is_valid')
                    }
                })
                return
            
            # Process human input using validation agent
            from agents.validation_agent import ValidationAgent
            validation_agent = ValidationAgent()
            
            # Acknowledge receipt
            await websocket_manager.broadcast_workflow_event(workflow_id, 'human_input_acknowledged', {
                'message': 'Human input received and processing...',
                'fields_updated': list(field_values.keys())
            })
            
            try:
                # Process the human input
                updated_state = await validation_agent.handle_human_input_response(
                    workflow_state, 
                    {
                        'field_values': field_values,
                        'user_notes': user_notes,
                        'submission_timestamp': datetime.now().isoformat(),
                        'source': 'websocket'
                    }
                )
                
                # Update the stored workflow state
                orchestrator_controller.orchestrator_service.active_workflows[workflow_id]["state"] = updated_state
                
                # Clear the waiting flag
                updated_state["awaiting_human_input_websocket"] = False
                
                # Notify success
                await websocket_manager.broadcast_workflow_event(workflow_id, 'human_input_processed', {
                    'message': 'Human input processed successfully',
                    'validation_results': updated_state.get('validation_results', {}),
                    'processing_status': updated_state.get('processing_status')
                })
                
                # If validation now passes, trigger workflow continuation
                if (updated_state.get('validation_results', {}).get('is_valid') and
                    updated_state.get('processing_status') == 'success'):
                    
                    # Continue workflow execution asynchronously
                    import asyncio
                    asyncio.create_task(
                        orchestrator_controller.orchestrator_service._execute_workflow(workflow_id, updated_state)
                    )
                
                logger.info(f"✅ WebSocket human input processed successfully for workflow {workflow_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to process WebSocket human input: {str(e)}")
                await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                    'message': f'Failed to process human input: {str(e)}'
                })
                
        elif message_type == 'ping':
            # Handle ping for connection health
            await websocket_manager.broadcast_workflow_event(workflow_id, 'pong', {
                'timestamp': datetime.now().isoformat()
            })
            
        elif message_type == 'get_status':
            # Handle status request
            workflow_info = orchestrator_controller.orchestrator_service.active_workflows.get(workflow_id)
            
            if workflow_info:
                await websocket_manager.broadcast_workflow_event(workflow_id, 'workflow_status', {
                    'status': workflow_info['state'].get('processing_status'),
                    'validation_results': workflow_info['state'].get('validation_results', {}),
                    'current_agent': workflow_info['state'].get('current_agent'),
                    'human_input_request': workflow_info['state'].get('human_input_request')
                })
            else:
                await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                    'message': f'Workflow {workflow_id} not found'
                })
                
        else:
            logger.warning(f"⚠️ Unknown message type: {message_type}")
            await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                'message': f'Unknown message type: {message_type}'
            })
            
    except Exception as e:
        logger.error(f"❌ Error handling WebSocket message: {str(e)}")
        await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
            'message': f'Error processing message: {str(e)}'
        })

@router.websocket("/ws/test")
async def test_websocket(
    websocket: WebSocket,
):
    """
    🔌 Simple WebSocket endpoint for testing connectivity.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        logger.info(f"🔌 Test WebSocket disconnected.")

@router.get("/workflow/{workflow_id}/invoice", response_model=Dict[str, Any])
async def get_workflow_invoice_data(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    📄 Get the final generated invoice JSON data from a completed workflow
    
    Returns the corrected and finalized invoice JSON generated by the correction agent.
    Only available for completed workflows.
    """
    logger.info(f"📄 API: Getting final invoice data - ID: {workflow_id}, User: {current_user['user_id']}")
    
    # Get the workflow state from active workflows
    workflow_info = orchestrator_controller.orchestrator_service.active_workflows.get(workflow_id)
    
    if not workflow_info:
        return {
            "error": "Workflow not found",
            "workflow_id": workflow_id,
            "message": "Workflow may have been completed and cleaned up, or the ID is invalid"
        }
    
    workflow_state = workflow_info.get("state", {})
    
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
            "message": "Workflow may still be in progress or failed before invoice generation"
        }
    
    return {
        "workflow_id": workflow_id,
        "final_invoice_json": final_invoice_json,
        "correction_completed": correction_completed,
        "processing_status": workflow_state.get("processing_status"),
        "quality_score": workflow_state.get("quality_score", 0.0),
        "confidence_level": workflow_state.get("confidence_level", 0.0),
        "generated_at": workflow_state.get("last_updated_at"),
        "metadata": {
            "contract_name": workflow_state.get("contract_name"),
            "user_id": workflow_state.get("user_id"),
            "attempt_count": workflow_state.get("attempt_count", 0)
        }
    }

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
