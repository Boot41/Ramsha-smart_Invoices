from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any
import logging
import json
import asyncio
from datetime import datetime
from services.websocket_manager import get_websocket_manager
from services.orchestrator_service import get_orchestrator_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test")
async def websocket_test():
    """Test endpoint to verify WebSocket routes are working"""
    return {
        "message": "WebSocket routes are working!",
        "endpoints": [
            "GET /api/v1/ws/test - This test endpoint",
            "WebSocket /api/v1/ws/workflow/{workflow_id}/realtime - Main WebSocket endpoint",
            "GET /api/v1/ws/workflow/{workflow_id}/connections - Connection count"
        ]
    }

@router.websocket("/workflow/{workflow_id}/realtime")
async def workflow_websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time workflow communication
    
    Provides real-time updates for:
    - Workflow status changes
    - Agent transitions
    - Human input requirements
    - Validation results
    - Workflow completion/failure
    """
    websocket_manager = get_websocket_manager()
    connection_id = None
    
    try:
        # Connect WebSocket to workflow
        connection_id = await websocket_manager.connect(websocket, workflow_id)
        logger.info(f"📡 WebSocket connected - Workflow: {workflow_id}, Connection: {connection_id}")
        
        # Send initial workflow status if available
        orchestrator_service = get_orchestrator_service()
        workflow_info = orchestrator_service.active_workflows.get(workflow_id)
        
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
        logger.info(f"📡 WebSocket disconnected - Workflow: {workflow_id}")
        
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

async def handle_websocket_message(workflow_id: str, message: Dict[str, Any], websocket_manager):
    """Handle incoming WebSocket messages from clients"""
    
    message_type = message.get('type')
    data = message.get('data', {})
    
    try:
        if message_type == 'human_input_submission':
            # Handle human input submission
            logger.info(f"📝 Processing human input submission for workflow {workflow_id}")
            
            field_values = data.get('field_values', {})
            user_notes = data.get('user_notes', '')
            
            # Submit human input to the workflow
            success = await websocket_manager.submit_human_input(workflow_id, {
                'field_values': field_values,
                'user_notes': user_notes,
                'submission_timestamp': datetime.now().isoformat(),
                'source': 'websocket'
            })
            
            if success:
                await websocket_manager.broadcast_workflow_event(workflow_id, 'human_input_acknowledged', {
                    'message': 'Human input received and processing...',
                    'fields_updated': list(field_values.keys())
                })
            else:
                await websocket_manager.broadcast_workflow_event(workflow_id, 'error', {
                    'message': 'No pending human input request for this workflow'
                })
                
        elif message_type == 'ping':
            # Handle ping for connection health
            await websocket_manager.broadcast_workflow_event(workflow_id, 'pong', {
                'timestamp': datetime.now().isoformat()
            })
            
        elif message_type == 'get_status':
            # Handle status request
            orchestrator_service = get_orchestrator_service()
            workflow_info = orchestrator_service.active_workflows.get(workflow_id)
            
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

@router.get("/workflow/{workflow_id}/connections")
async def get_workflow_connections(workflow_id: str):
    """Get number of active WebSocket connections for a workflow"""
    websocket_manager = get_websocket_manager()
    connection_count = websocket_manager.get_workflow_connections(workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "active_connections": connection_count,
        "has_connections": websocket_manager.has_active_connections(workflow_id)
    }