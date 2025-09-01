from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime
from schemas.workflow_schemas import WorkflowState, AgentResult, AgentType, ProcessingStatus

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the workflow"""
    
    def __init__(self, agent_type: AgentType, max_retries: int = 2):
        self.agent_type = agent_type
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{__name__}.{agent_type.value}")
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the agent with error handling and timing"""
        start_time = time.time()
        self.logger.info(f"🚀 Starting {self.agent_type.value} execution")
        
        try:
            # Update state to show current agent
            state["current_agent"] = self.agent_type.value
            state["last_updated_at"] = datetime.now().isoformat()
            
            # Execute the agent logic
            result = await self.process(state)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log success
            self.logger.info(f"✅ {self.agent_type.value} completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ {self.agent_type.value} failed after {execution_time:.2f}s: {str(e)}")
            
            # Add error to state
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
            state["processing_status"] = ProcessingStatus.FAILED.value
            
            return state
    
    @abstractmethod
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Abstract method to be implemented by each agent"""
        pass
    
    def create_result(self, 
                     status: ProcessingStatus, 
                     message: str,
                     data: Optional[Dict[str, Any]] = None,
                     confidence: float = 0.0,
                     errors: list = None,
                     suggestions: list = None) -> AgentResult:
        """Helper to create standardized agent results"""
        return AgentResult(
            agent_type=self.agent_type,
            status=status,
            message=message,
            data=data or {},
            confidence=confidence,
            errors=errors or [],
            suggestions=suggestions or [],
            execution_time=0.0
        )
    
    def update_state_metrics(self, state: WorkflowState, confidence: float, quality_score: float = None):
        """Update state with agent metrics"""
        state["confidence_level"] = confidence
        if quality_score is not None:
            state["quality_score"] = quality_score
        state["last_updated_at"] = datetime.now().isoformat()