import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

class LangSmithConfig:
    """A stub for LangSmith configuration to avoid errors when it's not installed."""
    
    def __init__(self):
        logger.info("LangSmith is not installed. Using stub configuration.")
        self.client = None
        self.tracer = None
    
    def is_enabled(self) -> bool:
        return False
    
    def create_tracer_callback(self) -> None:
        return None
    
    def log_workflow_start(self, *args, **kwargs) -> None:
        pass
    
    def log_agent_execution(self, *args, **kwargs) -> None:
        pass

_langsmith_config = None

def get_langsmith_config() -> LangSmithConfig:
    """Get singleton LangSmith configuration instance."""
    global _langsmith_config
    if _langsmith_config is None:
        _langsmith_config = LangSmithConfig()
    return _langsmith_config

def trace_agent(agent_name: str):
    """A stub decorator that does nothing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def trace_workflow_step(step_name: str):
    """A stub decorator that does nothing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
