"""
Internal HTTP client for agent-to-agent communication via HTTP endpoints
"""
import httpx
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class InternalHTTPClient:
    """HTTP client for internal API calls between agents and services"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        # Service token for internal auth - in production this should be from env
        self.service_headers = {
            "Authorization": "Bearer internal-service-token",
            "X-Internal-Service": "true",
            "Content-Type": "application/json"
        }
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url, 
            timeout=30.0,
            headers=self.service_headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        try:
            response = await self.client.get(f"/api/v1/orchestrator/workflow/{workflow_id}/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get workflow status for {workflow_id}: {e}")
            raise
    
    async def submit_human_input(self, workflow_id: str, field_values: Dict[str, Any], user_notes: str = "") -> Dict[str, Any]:
        """Submit human input for workflow validation"""
        try:
            payload = {
                "workflow_id": workflow_id,
                "field_values": field_values,
                "user_notes": user_notes
            }
            
            response = await self.client.post("/api/v1/human-input/submit", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to submit human input for {workflow_id}: {e}")
            raise
    
    async def submit_general_human_input(self, task_id: str, user_input: str) -> Dict[str, Any]:
        """Submit general human input for waiting workflows"""
        try:
            payload = {
                "task_id": task_id,
                "user_input": user_input
            }
            
            response = await self.client.post("/api/v1/human-input/input", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to submit general human input for {task_id}: {e}")
            raise
    
    async def get_human_input_request(self, workflow_id: str) -> Dict[str, Any]:
        """Get human input requirements for a workflow"""
        try:
            response = await self.client.get(f"/api/v1/human-input/request/{workflow_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get human input request for {workflow_id}: {e}")
            raise
    
    async def wait_for_human_input_with_timeout(self, workflow_id: str, timeout_seconds: int = 300) -> bool:
        """
        Wait for human input to be submitted via HTTP endpoint
        
        Returns True if human input was provided, False if timeout
        """
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout_seconds:
            try:
                status = await self.get_workflow_status(workflow_id)
                processing_status = status.get("processing_status", "")
                
                # Check if human input was provided (status changed from waiting)
                if processing_status not in ["needs_human_input", "WAITING_FOR_HUMAN_INPUT"]:
                    logger.info(f"✅ Human input received for workflow {workflow_id}")
                    return True
                    
                # Wait before checking again
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error checking workflow status: {e}")
                await asyncio.sleep(5)
        
        logger.warning(f"⏰ Timeout waiting for human input for workflow {workflow_id}")
        return False
    
    async def auto_resolve_simple_validation_issues(self, workflow_id: str) -> bool:
        """
        Attempt to auto-resolve simple validation issues using default values
        """
        try:
            # Get current human input request
            input_request = await self.get_human_input_request(workflow_id)
            
            fields = input_request.get("request", {}).get("fields", [])
            validation_results = input_request.get("validation_results", {})
            
            # Create auto-corrections for common issues
            auto_corrections = {}
            
            for field in fields:
                field_name = field.get("name")
                field_type = field.get("type", "string")
                current_value = field.get("value")
                
                if field_name and not current_value:
                    # Provide reasonable defaults for missing fields
                    if field_name.lower() in ["payment_due_days", "due_days"]:
                        auto_corrections[field_name] = 30
                    elif field_name.lower() in ["currency"]:
                        auto_corrections[field_name] = "USD"
                    elif field_name.lower() in ["payment_frequency", "frequency"]:
                        auto_corrections[field_name] = "monthly"
                    elif "amount" in field_name.lower() and field_type in ["number", "float"]:
                        auto_corrections[field_name] = 0.0
                    elif "date" in field_name.lower():
                        auto_corrections[field_name] = datetime.now().strftime("%Y-%m-%d")
                    elif field_type == "string":
                        auto_corrections[field_name] = f"Auto-generated {field_name}"
            
            if auto_corrections:
                logger.info(f"🤖 Auto-resolving {len(auto_corrections)} validation issues for workflow {workflow_id}")
                
                result = await self.submit_human_input(
                    workflow_id=workflow_id,
                    field_values=auto_corrections,
                    user_notes="Auto-resolved by system with default values"
                )
                
                return result.get("success", False)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to auto-resolve validation issues: {e}")
            return False

# Singleton instance
_http_client = None

def get_internal_http_client() -> InternalHTTPClient:
    """Get the internal HTTP client instance (returns context manager)"""
    return InternalHTTPClient()