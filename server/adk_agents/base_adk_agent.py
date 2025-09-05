"""
Base ADK Agent for Smart Invoice Scheduler

Converts the custom BaseAgent to Google ADK pattern
"""

from abc import abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
import logging
import time
from datetime import datetime

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from pydantic import PrivateAttr

# Using custom event class instead of Google ADK Event to avoid complex validation
class SimpleEvent:
    """Simple event class for workflow communication"""
    def __init__(self, author: str, content: str, data: Optional[Dict[str, Any]] = None):
        self.author = author
        self.content = content
        self.data = data or {}
        self.timestamp = datetime.now().isoformat()

from schemas.workflow_schemas import AgentType, ProcessingStatus

logger = logging.getLogger(__name__)


class BaseADKAgent(BaseAgent):
    """Base class for all ADK agents in the Smart Invoice Scheduler workflow"""
    agent_type: Optional[AgentType] = None
    max_retries: Optional[int] = None
    _logger: logging.Logger = PrivateAttr()
    
    def __init__(
        self, 
        name: str,
        agent_type: AgentType, 
        description: str,
        max_retries: int = 2,
        **kwargs
    ):
        super().__init__(name=name, description=description, **kwargs)
        self.agent_type = agent_type
        self.max_retries = max_retries
        self._logger = logging.getLogger(f"{__name__}.{agent_type.value}")

    @property
    def logger(self) -> logging.Logger:
        return self._logger
    
    async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """ADK-required async implementation with error handling and timing"""
        start_time = time.time()
        self.logger.info(f"🚀 Starting ADK {self.agent_type.value} execution")
        
        try:
            # Get current state from context
            state = context.state or {}
            
            # Update state to show current agent
            state["current_agent"] = self.agent_type.value
            state["last_updated_at"] = datetime.now().isoformat()
            
            # Execute the agent-specific logic
            async for event in self.process_adk(state, context):
                yield event
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log success and yield final event
            self.logger.info(f"✅ ADK {self.agent_type.value} completed in {execution_time:.2f}s")
            
            yield SimpleEvent(
                author=self.name,
                content=f"Agent {self.agent_type.value} completed successfully",
                data={
                    "execution_time": execution_time,
                    "status": "success",
                    "agent_type": self.agent_type.value
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ ADK {self.agent_type.value} failed after {execution_time:.2f}s: {str(e)}")
            
            # Add error to state
            state = context.state or {}
            error_info = {
                "agent": self.agent_type.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time
            }
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(error_info)
            
            # Update status
            state["processing_status"] = ProcessingStatus.FAILED
            
            # Update context state
            context.state.update(state)
            
            yield SimpleEvent(
                author=self.name,
                content=f"Agent {self.agent_type.value} failed: {str(e)}",
                data={
                    "execution_time": execution_time,
                    "status": "failed",
                    "error": str(e),
                    "agent_type": self.agent_type.value
                }
            )
    
    @abstractmethod
    async def process_adk(self, state: Dict[str, Any], context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """
        Abstract method to be implemented by each ADK agent
        
        Args:
            state: Current workflow state dictionary
            context: ADK InvocationContext with shared state and configuration
            
        Yields:
            SimpleEvent: ADK events representing processing steps and results
        """
        pass
    
    def create_success_event(
        self, 
        message: str,
        data: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0
    ) -> SimpleEvent:
        """Helper to create standardized success events"""
        return SimpleEvent(
            author=self.name,
            content=message,
            data={
                "status": "success",
                "agent_type": self.agent_type.value,
                "confidence": confidence,
                **(data or {})
            }
        )
    
    def create_error_event(
        self, 
        message: str,
        error: str,
        data: Optional[Dict[str, Any]] = None
    ) -> SimpleEvent:
        """Helper to create standardized error events"""
        return SimpleEvent(
            author=self.name,
            content=f"Error: {message}",
            data={
                "status": "error",
                "agent_type": self.agent_type.value,
                "error": error,
                **(data or {})
            }
        )
    
    def create_progress_event(
        self, 
        message: str,
        progress_percentage: float = 0.0,
        data: Optional[Dict[str, Any]] = None
    ) -> SimpleEvent:
        """Helper to create progress update events"""
        return SimpleEvent(
            author=self.name,
            content=message,
            data={
                "status": "in_progress",
                "agent_type": self.agent_type.value,
                "progress": progress_percentage,
                **(data or {})
            }
        )
    
    def update_state_metrics(self, state: Dict[str, Any], confidence: float, quality_score: float = None):
        """Update state with agent metrics"""
        state["confidence_level"] = confidence
        if quality_score is not None:
            state["quality_score"] = quality_score
        state["last_updated_at"] = datetime.now().isoformat()
    
    def update_invoice_data(self, state: Dict[str, Any], new_data: Dict[str, Any], source_agent: str = None):
        """
        Centralized method to update invoice data with proper versioning and history
        
        Args:
            state: Current workflow state
            new_data: New invoice data to store
            source_agent: Name of agent providing the data
        """
        # Archive current data to history
        if state.get("current_invoice_data"):
            history_entry = {
                "data": state["current_invoice_data"].copy(),
                "version": state.get("data_version", 0),
                "source_agent": state.get("authoritative_source"),
                "timestamp": state.get("last_updated_at"),
                "replaced_by": source_agent or self.name
            }
            state.setdefault("invoice_data_history", []).append(history_entry)
        
        # Update current data
        state["current_invoice_data"] = new_data.copy() if new_data else None
        state["authoritative_source"] = source_agent or self.name
        state["data_version"] = state.get("data_version", 0) + 1
        state["last_updated_at"] = datetime.now().isoformat()
        state["last_update_agent"] = source_agent or self.name
        
        # Also update legacy fields for backward compatibility
        if new_data:
            state["unified_invoice_data"] = new_data.copy()
            state["invoice_data"] = new_data.copy()
        
        self.logger.info(f"📝 Updated invoice data - Version: {state['data_version']}, Source: {source_agent or self.name}")
    
    def get_latest_invoice_data(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the most current, authoritative invoice data"""
        return state.get("current_invoice_data")
    
    def set_workflow_status(self, state: Dict[str, Any], status: str, paused: bool = False, 
                           human_input_required: bool = False, correction_pending: bool = False):
        """
        Centralized method to update workflow status and control flags
        
        Args:
            state: Current workflow state
            status: Processing status (should be a ProcessingStatus enum value)
            paused: Whether workflow is paused
            human_input_required: Whether human input is needed
            correction_pending: Whether correction is pending
        """
        state["processing_status"] = status
        state["workflow_paused"] = paused
        state["human_input_required"] = human_input_required
        state["correction_pending"] = correction_pending
        state["last_updated_at"] = datetime.now().isoformat()
        state["last_update_agent"] = self.name
        
        self.logger.info(f"🔄 Updated workflow status - Status: {status}, Paused: {paused}, Human Input: {human_input_required}")
    
    def should_skip_processing(self, state: Dict[str, Any]) -> tuple[bool, str]:
        """
        Check if agent should skip processing based on current workflow state
        
        Returns:
            (should_skip, reason) tuple
        """
        if state.get("workflow_paused", False):
            return True, "Workflow is paused"
        
        if state.get("human_input_required", False) and not state.get("human_input_resolved", False):
            return True, "Human input is required but not yet provided"
            
        processing_status = state.get("processing_status")
        if processing_status in [ProcessingStatus.FAILED, ProcessingStatus.NEEDS_HUMAN_INPUT]:
            return True, f"Workflow status requires attention: {processing_status}"
        
        return False, ""
    
    def validate_state_consistency(self, state: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that the workflow state is consistent and has required data
        
        Returns:
            (is_valid, issues) tuple
        """
        issues = []
        
        # Check for required workflow identifiers
        if not state.get("workflow_id"):
            issues.append("Missing workflow_id")
        if not state.get("user_id"):
            issues.append("Missing user_id")
        
        # Check data consistency
        current_data = state.get("current_invoice_data")
        authoritative_source = state.get("authoritative_source")
        
        if current_data and not authoritative_source:
            issues.append("Invoice data exists but no authoritative source specified")
        
        if authoritative_source and not current_data:
            issues.append("Authoritative source specified but no invoice data found")
        
        # Check version consistency
        data_version = state.get("data_version", 0)
        history_length = len(state.get("invoice_data_history", []))
        
        if data_version > 0 and data_version != history_length + 1:
            issues.append(f"Version mismatch: data_version={data_version}, expected={history_length + 1}")
        
        # Check workflow status consistency
        processing_status = state.get("processing_status")
        workflow_paused = state.get("workflow_paused", False)
        human_input_required = state.get("human_input_required", False)
        
        if human_input_required and processing_status != ProcessingStatus.NEEDS_HUMAN_INPUT:
            issues.append(f"Human input required but status is {processing_status}")
        
        if workflow_paused and processing_status not in [
            ProcessingStatus.NEEDS_HUMAN_INPUT, 
            ProcessingStatus.PAUSED_FOR_HUMAN_INPUT
        ]:
            issues.append(f"Workflow paused but status is {processing_status}")
        
        return len(issues) == 0, issues