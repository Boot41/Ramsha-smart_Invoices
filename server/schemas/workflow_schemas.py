from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_RETRY = "needs_retry"
    NEEDS_HUMAN_INPUT = "needs_human_input"
    COMPLETED = "completed"

class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    CONTRACT_PROCESSING = "contract_processing"
    VALIDATION = "validation"
    CORRECTION = "correction"
    SCHEDULE_EXTRACTION = "schedule_extraction"
    INVOICE_GENERATION = "invoice_generation"
    QUALITY_ASSURANCE = "quality_assurance"
    STORAGE_SCHEDULING = "storage_scheduling"
    FEEDBACK_LEARNING = "feedback_learning"
    ERROR_RECOVERY = "error_recovery"

class WorkflowState(TypedDict):
    """LangGraph state for the agentic workflow"""
    # Core Data
    contract_file: bytes
    user_id: str
    contract_name: str
    contract_data: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    invoice_data: Optional[Dict[str, Any]]
    schedule_data: Optional[Dict[str, Any]]
    final_invoice: Optional[Dict[str, Any]]
    
    # Agentic Control
    attempt_count: int
    max_attempts: int
    errors: List[Dict[str, Any]]
    feedback_history: List[Dict[str, Any]]
    quality_score: float
    confidence_level: float
    
    # Status Tracking
    processing_status: str
    current_agent: str
    retry_reasons: List[str]
    
    # Learning & Improvement
    learned_patterns: Dict[str, Any]
    improvement_suggestions: List[str]
    success_metrics: Dict[str, Any]
    
    # Timestamps
    started_at: str
    last_updated_at: str
    workflow_id: str

class WorkflowRequest(BaseModel):
    """Request to start the invoice workflow"""
    user_id: str = Field(..., description="User ID")
    contract_file: bytes = Field(..., description="Contract file content as bytes")
    contract_name: str = Field(..., description="Name of the contract")
    max_attempts: int = Field(default=3, description="Maximum retry attempts")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options")

class WorkflowResponse(BaseModel):
    """Response from workflow execution"""
    workflow_id: str
    status: ProcessingStatus
    message: str
    result: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    quality_score: float = 0.0
    confidence_level: float = 0.0
    attempt_count: int = 0
    processing_time_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)

class AgentResult(BaseModel):
    """Result from individual agent execution"""
    agent_type: AgentType
    status: ProcessingStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    errors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    execution_time: float = 0.0

class WorkflowStatus(BaseModel):
    """Status check response"""
    workflow_id: str
    status: ProcessingStatus
    current_agent: str
    progress_percentage: float
    last_updated: datetime
    errors: List[str] = Field(default_factory=list)