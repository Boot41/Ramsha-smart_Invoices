"""
Smart Invoice Scheduler - Google ADK Workflow Orchestration

This file contains the main ADK workflow that orchestrates all agents for invoice processing.
It replaces the legacy orchestrator and provides a modern ADK-based approach.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid

# Removed SequentialAgent, LlmAgent, ParallelAgent imports - using simpler approach
# Removed InvocationContext import - using simpler approach
# Using SimpleEvent from base_adk_agent instead of Google ADK Event

from .contract_processing_adk_agent import ContractProcessingADKAgent
from .validation_adk_agent import ValidationADKAgent
from .correction_adk_agent import CorrectionADKAgent
from .invoice_generator_adk_agent import InvoiceGeneratorADKAgent
from .ui_generation_adk_agent import UIGenerationADKAgent
# from .schedule_retrieval_adk_agent import ScheduleRetrievalADKAgent  # Temporarily commented due to missing dependency
from schemas.workflow_schemas import ProcessingStatus

logger = logging.getLogger(__name__)


class InvoiceProcessingADKWorkflow:
    """
    Main ADK workflow for Smart Invoice Processing
    
    This workflow orchestrates the complete invoice generation pipeline:
    1. Contract Processing (PDF/text extraction, embeddings, RAG)
    2. Validation (business rules, human-in-the-loop)
    3. Correction (final JSON generation, business rules)
    4. Invoice Generation (database storage, record creation)
    5. UI Generation (HTML/CSS invoice templates, viewing URLs)
    6. Schedule Retrieval (automated scheduling and notifications)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all ADK agents
        self.contract_processing_agent = ContractProcessingADKAgent()
        self.validation_agent = ValidationADKAgent()
        self.correction_agent = CorrectionADKAgent()
        self.invoice_generator_agent = InvoiceGeneratorADKAgent()
        self.ui_generation_agent = UIGenerationADKAgent()
        # self.schedule_retrieval_agent = ScheduleRetrievalADKAgent()  # Temporarily commented due to missing dependency
        
        # Create the main ADK workflow
        self.workflow = self._create_adk_workflow()
    
    def _create_adk_workflow(self):
        """
        Create the main ADK workflow agents list for sequential execution
        
        Returns a list of agents that will be executed sequentially.
        """
        
        # Return the agents in execution order
        return [
            self.contract_processing_agent,
            self.validation_agent,
            self.correction_agent,
            self.invoice_generator_agent,
            self.ui_generation_agent
            # self.schedule_retrieval_agent  # Temporarily commented due to missing dependency
        ]
    
    async def execute_workflow(
        self,
        user_id: str,
        contract_file: Any,
        contract_name: str,
        max_attempts: int = 3,
        options: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete ADK workflow for invoice processing
        
        Args:
            user_id: User identifier
            contract_file: Contract file bytes or text content
            contract_name: Name of the contract
            max_attempts: Maximum retry attempts
            options: Additional processing options
            workflow_id: Optional workflow ID (generated if not provided)
            
        Returns:
            Final workflow state with results
        """
        
        # Initialize workflow state
        w_id = workflow_id if workflow_id else str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        initial_state = {
            # Core workflow identifiers
            "workflow_id": w_id,
            "user_id": user_id,
            "contract_file": contract_file,
            "contract_name": contract_name,
            
            # Centralized data management
            "invoice_data_history": [],  # Track all versions of invoice data
            "current_invoice_data": None,  # Always the latest valid/corrected version
            "authoritative_source": None,  # Which agent owns the current data
            "data_version": 0,  # Increment with each data update
            
            # Agent-specific results (for debugging and analysis)
            "contract_processing_result": None,
            "validation_result": None,
            "correction_result": None,
            
            # Legacy compatibility (maintain existing keys for backward compatibility)
            "contract_data": None,
            "validation_results": None,
            "invoice_data": None,
            "unified_invoice_data": None,
            "final_invoice_json": None,
            
            # Workflow control
            "processing_status": ProcessingStatus.PENDING.value,
            "workflow_paused": False,
            "human_input_required": False,
            "correction_pending": False,
            
            # Metadata
            "attempt_count": 0,
            "max_attempts": max_attempts,
            "errors": [],
            "current_agent": "workflow_start",
            "started_at": now,
            "last_updated_at": now,
            "last_update_agent": None,
            "workflow_completed": False,
            "adk_workflow": True,
            "options": options or {}
        }
        
        self.logger.info(f"🚀 Starting ADK workflow execution - ID: {w_id}, User: {user_id}, Contract: {contract_name}")
        
        try:
            # Create a simple context object with state
            class SimpleContext:
                def __init__(self, state):
                    self.state = state
            
            context = SimpleContext(initial_state)
            
            # Execute agents sequentially using the workflow list
            final_events = []
            validation_bypass = initial_state.get("options", {}).get("bypass_validation", True)
            
            for i, agent in enumerate(self.workflow):
                agent_name = agent.__class__.__name__
                current_status = context.state.get('processing_status')
                
                # Check if we should skip this agent due to validation failure
                if (agent_name == "ValidationADKAgent" and 
                    current_status in [ProcessingStatus.FAILED.value, ProcessingStatus.NEEDS_HUMAN_INPUT.value] and
                    not validation_bypass):
                    self.logger.info(f"⏭️ Skipping {agent_name} due to previous failure and bypass disabled")
                    continue
                
                # For UI and scheduling agents, allow them to run even if validation failed (if bypass enabled)
                if (agent_name in ["UIGenerationADKAgent", "ScheduleRetrievalADKAgent"] and 
                    current_status in [ProcessingStatus.FAILED.value, ProcessingStatus.NEEDS_HUMAN_INPUT.value] and 
                    validation_bypass):
                    self.logger.info(f"⚠️ Running {agent_name} with validation bypass enabled")
                    context.state["validation_bypassed"] = True
                
                async for event in agent._run_async_impl(context):
                    final_events.append(event)
                    self.logger.info(f"📋 ADK Event: {event.author} - {event.content}")
                
                # Update state from event data if provided
                if hasattr(event, 'data') and event.data:
                    event_data = event.data
                    if isinstance(event_data, dict):
                        # Update specific workflow tracking fields
                        if 'status' in event_data:
                            context.state['processing_status'] = event_data['status']
                        if 'agent_type' in event_data:
                            context.state['current_agent'] = event_data['agent_type']
                        if 'workflow_completed' in event_data:
                            context.state['workflow_completed'] = event_data['workflow_completed']
                
                # Check if workflow should pause for human input (only if bypass is disabled)
                current_status = context.state.get('processing_status')
                if (current_status in [ProcessingStatus.NEEDS_HUMAN_INPUT.value, ProcessingStatus.FAILED.value] and 
                    not validation_bypass and 
                    agent_name == "ValidationADKAgent"):
                    self.logger.info(f"⏸️ Workflow paused after {agent_name} for human input")
                    break
            
            # Get final state from context
            final_state = context.state
            final_state["last_updated_at"] = datetime.now().isoformat()
            final_state["adk_events"] = [
                {
                    "author": event.author,
                    "content": event.content,
                    "data": event.data if hasattr(event, 'data') else None,
                    "timestamp": datetime.now().isoformat()
                }
                for event in final_events
            ]
            
            # Determine final status based on current state
            current_status = final_state.get("processing_status")
            workflow_paused = final_state.get("workflow_paused", False)
            human_input_required = final_state.get("human_input_required", False)
            
            if human_input_required or workflow_paused or current_status in [
                ProcessingStatus.NEEDS_HUMAN_INPUT.value, 
                ProcessingStatus.PAUSED_FOR_HUMAN_INPUT.value,
                ProcessingStatus.PAUSED_FOR_VALIDATION.value
            ]:
                # Workflow is paused for human input
                final_state["processing_status"] = ProcessingStatus.NEEDS_HUMAN_INPUT.value
                final_state["workflow_paused"] = True
                final_state["workflow_completed"] = False
                self.logger.info(f"⏸️ ADK workflow paused for human input - ID: {w_id}")
                
            elif final_state.get("schedule_retrieval_result", {}).get("scheduling_successful", False):
                # Complete workflow - all agents including scheduling completed
                final_state["processing_status"] = ProcessingStatus.SUCCESS.value
                final_state["workflow_completed"] = True
                final_state["workflow_paused"] = False
                self.logger.info(f"✅ ADK workflow completed successfully - ID: {w_id}")
                
            elif final_state.get("invoice_generation_result", {}).get("generation_successful", False):
                # Invoice generation completed but scheduling may not be needed
                final_state["processing_status"] = ProcessingStatus.SUCCESS.value
                final_state["workflow_completed"] = True
                final_state["workflow_paused"] = False
                self.logger.info(f"✅ ADK workflow completed with invoice generation - ID: {w_id}")
                
            elif current_status == ProcessingStatus.FAILED.value:
                # Workflow failed
                final_state["workflow_completed"] = True
                final_state["workflow_failed"] = True
                self.logger.info(f"❌ ADK workflow failed - ID: {w_id}")
                
            else:
                # Default to in progress if not clearly completed or paused
                final_state["processing_status"] = ProcessingStatus.IN_PROGRESS.value
                final_state["workflow_completed"] = False
                self.logger.info(f"🔄 ADK workflow in progress - ID: {w_id}, Status: {current_status}")
            
            final_workflow_status = final_state.get("processing_status")
            self.logger.info(f"📊 ADK workflow final status - ID: {w_id}, Status: {final_workflow_status}, Paused: {final_state.get('workflow_paused')}, Human Input Required: {final_state.get('human_input_required')}")
            
            return final_state
            
        except Exception as e:
            self.logger.error(f"❌ ADK workflow failed - ID: {w_id}: {str(e)}")
            
            # Return error state
            error_state = initial_state.copy()
            error_state.update({
                "processing_status": ProcessingStatus.FAILED.value,
                "workflow_completed": True,
                "workflow_failed": True,
                "last_updated_at": datetime.now().isoformat(),
                "errors": [
                    {
                        "agent": "adk_workflow",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            })
            
            return error_state
    
    async def resume_workflow(
        self,
        workflow_state: Dict[str, Any],
        human_input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused ADK workflow, typically after human input
        
        Args:
            workflow_state: Current workflow state
            human_input_data: Human input data for corrections
            
        Returns:
            Updated workflow state
        """
        workflow_id = workflow_state.get("workflow_id")
        self.logger.info(f"🔄 Resuming ADK workflow - ID: {workflow_id}")
        
        try:
            # Create context from existing state
            class SimpleContext:
                def __init__(self, state):
                    self.state = state
            
            context = SimpleContext(workflow_state)
            
            # If human input was provided, process it through validation agent
            if human_input_data:
                self.logger.info("📝 Processing human input data")
                
                # Process human input through validation agent
                async for event in self.validation_agent.handle_human_input_response(
                    workflow_state, context, human_input_data
                ):
                    self.logger.info(f"📋 Human Input Event: {event.author} - {event.content}")
                
                # Update state from context
                workflow_state = context.state
            
            # Check if we need to continue the workflow
            processing_status = workflow_state.get("processing_status")
            validation_bypass = workflow_state.get("options", {}).get("bypass_validation", True)
            
            # Allow continuation even if validation failed (bypass enabled by default)
            if ((processing_status == ProcessingStatus.SUCCESS.value or 
                 (validation_bypass and processing_status in [ProcessingStatus.FAILED.value, ProcessingStatus.NEEDS_HUMAN_INPUT.value])) and 
                not workflow_state.get("correction_completed")):
                
                if validation_bypass and processing_status != ProcessingStatus.SUCCESS.value:
                    self.logger.info("⚠️ Validation bypass enabled - continuing workflow despite validation issues")
                    workflow_state["validation_bypassed"] = True
                    workflow_state["bypass_reason"] = f"Continuing with status: {processing_status}"
                
                # Continue with correction agent
                self.logger.info("➡️ Continuing workflow with correction agent")
                async for event in self.correction_agent.process_adk(workflow_state, context):
                    self.logger.info(f"📋 Correction Event: {event.author} - {event.content}")
                
                # Update final state
                workflow_state = context.state
                
                # Continue with UI generation agent even if validation failed
                if validation_bypass or workflow_state.get("processing_status") == ProcessingStatus.SUCCESS.value:
                    self.logger.info("🎨 Continuing with UI generation agent")
                    async for event in self.ui_generation_agent.process_adk(workflow_state, context):
                        self.logger.info(f"📋 UI Generation Event: {event.author} - {event.content}")
                    
                    # Update final state
                    workflow_state = context.state
            
            workflow_state["last_updated_at"] = datetime.now().isoformat()
            workflow_state["workflow_resumed"] = True
            workflow_state["resume_timestamp"] = datetime.now().isoformat()
            
            self.logger.info(f"✅ ADK workflow resumed successfully - ID: {workflow_id}")
            return workflow_state
            
        except Exception as e:
            self.logger.error(f"❌ Failed to resume ADK workflow - ID: {workflow_id}: {str(e)}")
            
            # Add error to state
            if "errors" not in workflow_state:
                workflow_state["errors"] = []
            workflow_state["errors"].append({
                "agent": "adk_workflow_resume",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            workflow_state["processing_status"] = ProcessingStatus.FAILED.value
            workflow_state["last_updated_at"] = datetime.now().isoformat()
            
            return workflow_state
    
    def get_workflow_status(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed workflow status information
        
        Args:
            workflow_state: Current workflow state
            
        Returns:
            Detailed status information
        """
        workflow_id = workflow_state.get("workflow_id")
        current_agent = workflow_state.get("current_agent", "unknown")
        processing_status = workflow_state.get("processing_status", "unknown")
        
        # Calculate progress percentage based on completed steps
        progress_steps = [
            ("contract_data", "Contract processing completed"),
            ("validation_results", "Validation completed"),
            ("final_invoice_json", "Correction completed"),
            ("invoice_created", "Invoice generation completed"),
            ("ui_generated", "UI generation completed"),
            ("schedule_retrieval_result", "Schedule retrieval completed")
        ]
        
        completed_steps = 0
        current_step_info = "Starting workflow..."
        
        for step_key, step_description in progress_steps:
            if workflow_state.get(step_key):
                completed_steps += 1
                current_step_info = step_description
            else:
                break
        
        progress_percentage = (completed_steps / len(progress_steps)) * 100
        
        # Handle special cases
        if processing_status == "PAUSED_FOR_HUMAN_INPUT":
            current_step_info = "Waiting for human input validation"
        elif workflow_state.get("workflow_completed"):
            progress_percentage = 100
            current_step_info = "Workflow completed successfully"
        elif processing_status == ProcessingStatus.FAILED.value:
            current_step_info = "Workflow failed"
        
        return {
            "workflow_id": workflow_id,
            "status": processing_status,
            "current_agent": current_agent,
            "current_step": current_step_info,
            "progress_percentage": progress_percentage,
            "is_adk_workflow": True,
            "workflow_completed": workflow_state.get("workflow_completed", False),
            "workflow_paused": workflow_state.get("workflow_paused", False),
            "human_input_required": workflow_state.get("awaiting_human_input", False),
            "confidence_level": workflow_state.get("confidence_level", 0.0),
            "quality_score": workflow_state.get("quality_score", 0.0),
            "attempt_count": workflow_state.get("attempt_count", 0),
            "max_attempts": workflow_state.get("max_attempts", 3),
            "error_count": len(workflow_state.get("errors", [])),
            "started_at": workflow_state.get("started_at"),
            "last_updated_at": workflow_state.get("last_updated_at"),
            "estimated_completion": self._estimate_completion_time(workflow_state)
        }
    
    def _estimate_completion_time(self, workflow_state: Dict[str, Any]) -> Optional[str]:
        """Estimate completion time based on current progress"""
        if workflow_state.get("workflow_completed"):
            return "Completed"
        
        if workflow_state.get("processing_status") == "PAUSED_FOR_HUMAN_INPUT":
            return "Waiting for human input"
        
        # Simple estimation based on average processing time
        started_at = workflow_state.get("started_at")
        if started_at:
            try:
                start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
                
                # Estimate 5-10 minutes for complete workflow
                if elapsed_minutes < 5:
                    return "~3-5 minutes remaining"
                elif elapsed_minutes < 10:
                    return "~1-3 minutes remaining"
                else:
                    return "Processing (may require human input)"
            except:
                pass
        
        return "Estimating..."


def create_adk_workflow() -> InvoiceProcessingADKWorkflow:
    """
    Factory function to create a new ADK workflow instance
    
    Returns:
        Configured InvoiceProcessingADKWorkflow instance
    """
    return InvoiceProcessingADKWorkflow()