import os
import logging
from typing import Optional, Dict, Any
from langsmith import Client, traceable
from langchain.callbacks import LangChainTracer
from langchain.callbacks.base import BaseCallbackHandler
from datetime import datetime

logger = logging.getLogger(__name__)

class LangSmithConfig:
    """LangSmith configuration and utilities for workflow monitoring"""
    
    def __init__(self):
        self.client = None
        self.tracer = None
        self.project_name = "smart-invoice-orchestrator"
        self._setup_langsmith()
    
    def _setup_langsmith(self):
        """Initialize LangSmith client and tracer"""
        try:
            # Set environment variables if not already set
            if not os.getenv("LANGCHAIN_TRACING_V2"):
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
            
            if not os.getenv("LANGCHAIN_PROJECT"):
                os.environ["LANGCHAIN_PROJECT"] = self.project_name
            
            # Initialize client
            self.client = Client()
            
            # Initialize tracer with project name
            self.tracer = LangChainTracer(project_name=self.project_name)
            
            logger.info(f"✅ LangSmith configured for project: {self.project_name}")
            
        except Exception as e:
            logger.warning(f"⚠️ LangSmith setup failed: {str(e)}. Continuing without tracing.")
            self.client = None
            self.tracer = None
    
    def is_enabled(self) -> bool:
        """Check if LangSmith is properly configured"""
        return self.client is not None and self.tracer is not None
    
    def create_tracer_callback(self) -> Optional[BaseCallbackHandler]:
        """Get LangChain tracer callback for workflow execution"""
        return self.tracer if self.is_enabled() else None
    
    def log_workflow_start(self, workflow_id: str, user_id: str, contract_name: str) -> None:
        """Log workflow start event to LangSmith"""
        if not self.is_enabled():
            return
        
        try:
            self.client.create_run(
                name="workflow_start",
                run_type="chain",
                inputs={
                    "workflow_id": workflow_id,
                    "user_id": user_id,
                    "contract_name": contract_name,
                    "timestamp": datetime.now().isoformat()
                },
                project_name=self.project_name
            )
        except Exception as e:
            logger.warning(f"Failed to log workflow start: {str(e)}")
    
    def log_agent_execution(self, agent_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any], 
                           execution_time: float = 0.0, error: str = None) -> None:
        """Log individual agent execution to LangSmith"""
        if not self.is_enabled():
            return
        
        try:
            run_data = {
                "name": f"agent_{agent_name}",
                "run_type": "tool",
                "inputs": inputs,
                "outputs": outputs,
                "project_name": self.project_name
            }
            
            if error:
                run_data["error"] = error
            
            if execution_time > 0:
                run_data["execution_time"] = execution_time
            
            self.client.create_run(**run_data)
            
        except Exception as e:
            logger.warning(f"Failed to log agent execution: {str(e)}")


# Global LangSmith configuration instance
_langsmith_config = None

def get_langsmith_config() -> LangSmithConfig:
    """Get singleton LangSmith configuration instance"""
    global _langsmith_config
    if _langsmith_config is None:
        _langsmith_config = LangSmithConfig()
    return _langsmith_config


# Decorators for easy tracing
def trace_agent(agent_name: str):
    """Decorator to trace agent execution"""
    def decorator(func):
        if get_langsmith_config().is_enabled():
            return traceable(
                name=f"agent_{agent_name}",
                project_name="smart-invoice-orchestrator"
            )(func)
        return func
    return decorator


def trace_workflow_step(step_name: str):
    """Decorator to trace workflow steps"""
    def decorator(func):
        if get_langsmith_config().is_enabled():
            return traceable(
                name=f"workflow_{step_name}",
                project_name="smart-invoice-orchestrator"
            )(func)
        return func
    return decorator