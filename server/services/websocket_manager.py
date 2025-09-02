from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

class WorkflowWebSocketManager:
    """WebSocket manager for real-time workflow communication"""
    
    def __init__(self):
        # workflow_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # workflow_id -> future waiting for human input
        self.pending_human_inputs: Dict[str, asyncio.Future] = {}
        
        # workflow_id -> lock for thread safety
        self.workflow_locks: Dict[str, asyncio.Lock] = {}
        
        # connection_id -> workflow_id mapping for cleanup
        self.connection_workflows: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, workflow_id: str) -> str:
        """Connect a WebSocket to a workflow"""
        await websocket.accept()
        connection_id = str(uuid4())
        
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = set()
            
        self.active_connections[workflow_id].add(websocket)
        self.connection_workflows[connection_id] = workflow_id
        
        # Send connection confirmation
        await self._send_to_websocket(websocket, {
            'type': 'connection_established',
            'data': {
                'workflow_id': workflow_id,
                'connection_id': connection_id,
                'timestamp': datetime.now().isoformat()
            }
        })
        
        logger.info(f"📡 WebSocket connected to workflow {workflow_id}")
        return connection_id
        
    async def disconnect(self, websocket: WebSocket, connection_id: str):
        """Disconnect a WebSocket"""
        workflow_id = self.connection_workflows.get(connection_id)
        if workflow_id and workflow_id in self.active_connections:
            self.active_connections[workflow_id].discard(websocket)
            
            # Clean up empty workflow connections
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
                
                # Cancel pending human input if no connections left
                if workflow_id in self.pending_human_inputs:
                    future = self.pending_human_inputs[workflow_id]
                    if not future.done():
                        future.cancel()
                    del self.pending_human_inputs[workflow_id]
                    
        if connection_id in self.connection_workflows:
            del self.connection_workflows[connection_id]
            
        logger.info(f"📡 WebSocket disconnected from workflow {workflow_id}")
        
    async def broadcast_workflow_event(self, workflow_id: str, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connections for a workflow"""
        if workflow_id not in self.active_connections:
            logger.warning(f"No WebSocket connections for workflow {workflow_id}")
            return
            
        message = {
            'type': event_type,
            'workflow_id': workflow_id,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to all connections for this workflow
        connections_to_remove = set()
        for websocket in self.active_connections[workflow_id].copy():
            try:
                await self._send_to_websocket(websocket, message)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket: {e}")
                connections_to_remove.add(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            self.active_connections[workflow_id].discard(websocket)
            
        logger.info(f"📡 Broadcasted {event_type} to {len(self.active_connections[workflow_id])} connections for workflow {workflow_id}")
        
    async def request_human_input(self, workflow_id: str, requirements: Dict[str, Any], timeout: int = 300) -> Dict[str, Any]:
        """Request human input via WebSocket and wait for response"""
        logger.info(f"🙋 Requesting human input for workflow {workflow_id}")
        
        # Create future for human input response
        if workflow_id in self.pending_human_inputs:
            # Cancel existing request
            self.pending_human_inputs[workflow_id].cancel()
            
        future = asyncio.Future()
        self.pending_human_inputs[workflow_id] = future
        
        # Broadcast human input requirement
        await self.broadcast_workflow_event(workflow_id, 'human_input_required', {
            'requirements': requirements,
            'timeout': timeout,
            'request_id': str(uuid4())
        })
        
        try:
            # Wait for human input with timeout
            human_input_data = await asyncio.wait_for(future, timeout=timeout)
            logger.info(f"✅ Human input received for workflow {workflow_id}")
            
            # Broadcast acknowledgment
            await self.broadcast_workflow_event(workflow_id, 'human_input_received', {
                'message': 'Human input received, processing...'
            })
            
            return human_input_data
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Human input timeout for workflow {workflow_id}")
            raise Exception(f"Human input timeout after {timeout} seconds")
            
        except asyncio.CancelledError:
            logger.warning(f"🚫 Human input request cancelled for workflow {workflow_id}")
            raise Exception("Human input request cancelled")
            
        finally:
            # Clean up
            if workflow_id in self.pending_human_inputs:
                del self.pending_human_inputs[workflow_id]
                
    async def submit_human_input(self, workflow_id: str, input_data: Dict[str, Any]) -> bool:
        """Submit human input for a workflow"""
        if workflow_id not in self.pending_human_inputs:
            logger.warning(f"No pending human input request for workflow {workflow_id}")
            return False
            
        future = self.pending_human_inputs[workflow_id]
        if future.done():
            logger.warning(f"Human input already submitted for workflow {workflow_id}")
            return False
            
        # Set the result
        future.set_result(input_data)
        logger.info(f"📝 Human input submitted for workflow {workflow_id}")
        
        return True
        
    async def notify_workflow_status(self, workflow_id: str, status: str, message: str, data: Optional[Dict] = None):
        """Notify workflow status change"""
        await self.broadcast_workflow_event(workflow_id, 'workflow_status_update', {
            'status': status,
            'message': message,
            'data': data or {}
        })
        
    async def notify_agent_transition(self, workflow_id: str, from_agent: str, to_agent: str):
        """Notify agent transition"""
        await self.broadcast_workflow_event(workflow_id, 'agent_transition', {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'message': f'Transitioning from {from_agent} to {to_agent}'
        })
        
    async def notify_workflow_completed(self, workflow_id: str, final_state: Dict[str, Any]):
        """Notify workflow completion"""
        await self.broadcast_workflow_event(workflow_id, 'workflow_completed', {
            'message': 'Workflow completed successfully',
            'final_state': final_state
        })
        
    async def notify_workflow_failed(self, workflow_id: str, error: str, state: Dict[str, Any]):
        """Notify workflow failure"""
        await self.broadcast_workflow_event(workflow_id, 'workflow_failed', {
            'error': error,
            'message': f'Workflow failed: {error}',
            'final_state': state
        })
        
    async def _send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            # Remove the failed websocket from active connections
            await self._cleanup_websocket(websocket)
    
    async def _cleanup_websocket(self, websocket: WebSocket):
        """Remove a websocket from all active connections"""
        for workflow_id, connections in self.active_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                logger.info(f"📡 Removed failed WebSocket from workflow {workflow_id}")
                break
        
    def get_workflow_connections(self, workflow_id: str) -> int:
        """Get number of active connections for a workflow"""
        return len(self.active_connections.get(workflow_id, set()))
        
    def has_active_connections(self, workflow_id: str) -> bool:
        """Check if workflow has active WebSocket connections"""
        return workflow_id in self.active_connections and len(self.active_connections[workflow_id]) > 0


# Singleton instance
_websocket_manager = None

def get_websocket_manager() -> WorkflowWebSocketManager:
    """Get the singleton WebSocket manager"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WorkflowWebSocketManager()
    return _websocket_manager