"""
Validation API endpoints for human-in-the-loop workflow
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel, Field
from services.orchestrator_service import get_orchestrator_service
from agents.correction_agent import CorrectionAgent
from agents.invoice_generator_agent import InvoiceGeneratorAgent
from agents.ui_invoice_generator_agent import UIInvoiceGeneratorAgent
from middleware.auth import get_current_user
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/validation", tags=["validation"])

# Define expected data structure models for clear documentation
class PartyData(BaseModel):
    """Expected party (client/service_provider) data structure"""
    name: str
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None

class PaymentTermsData(BaseModel):
    """Expected payment terms data structure"""
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    frequency: Optional[str] = None
    due_days: Optional[int] = 30
    late_fee: Optional[float] = None
    discount_terms: Optional[str] = None
    payment_method: Optional[str] = "bank_transfer"

class ExpectedCorrectedData(BaseModel):
    """Expected structure for corrected_data field"""
    client: Optional[PartyData] = None
    service_provider: Optional[PartyData] = None
    payment_terms: Optional[PaymentTermsData] = None
    contract_title: Optional[str] = None
    contract_type: Optional[str] = None
    notes: Optional[str] = None

class DataFormatResponse(BaseModel):
    """Response showing expected data format"""
    expected_format: Dict[str, Any]
    example: Dict[str, Any]
    notes: list

class ValidationRequirementsResponse(BaseModel):
    """Response containing validation requirements for human input"""
    workflow_id: str
    contract_name: str
    user_id: str
    validation_issues: list
    required_fields: list
    current_data: Dict[str, Any]
    instructions: str

class ResumeWorkflowRequest(BaseModel):
    """Request to resume workflow with corrected data"""
    workflow_id: str = Field(..., description="Workflow ID to resume")
    corrected_data: Dict[str, Any] = Field(..., description="Human-corrected validation data")
    user_notes: str = Field(default="", description="Optional notes from user")

class ResumeWorkflowResponse(BaseModel):
    """Response after resuming workflow"""
    success: bool
    message: str
    workflow_id: str
    status: str
    final_invoice_ready: bool = False
    ui_template_ready: bool = False

@router.get("/requirements/{workflow_id}", response_model=ValidationRequirementsResponse)
async def get_validation_requirements(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get validation requirements for a paused workflow
    
    Returns what data needs to be corrected by human input before the workflow can continue.
    Workflow must be in PAUSED_FOR_HUMAN_INPUT status.
    """
    try:
        logger.info(f"📋 Getting validation requirements for workflow {workflow_id}")
        
        orchestrator_service = get_orchestrator_service()
        
        # Get workflow from active workflows
        workflow_info = orchestrator_service.active_workflows.get(workflow_id)
        if not workflow_info:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found or has expired"
            )
        
        workflow_state = workflow_info["state"]
        
        # Check if workflow is paused for human input
        if workflow_state.get("processing_status") != "PAUSED_FOR_HUMAN_INPUT":
            raise HTTPException(
                status_code=400,
                detail=f"Workflow {workflow_id} is not paused for human input. Current status: {workflow_state.get('processing_status')}"
            )
        
        # Extract validation information
        human_input_request = workflow_state.get("human_input_request", {})
        validation_results = workflow_state.get("validation_results", {})
        
        # Get current extracted data for context - prioritize unified format
        current_data = {}
        if "unified_invoice_data" in workflow_state:
            current_data = workflow_state["unified_invoice_data"]
        elif "invoice_data" in workflow_state:
            invoice_data = workflow_state["invoice_data"]
            if isinstance(invoice_data, dict) and "invoice_response" in invoice_data:
                current_data = invoice_data["invoice_response"].get("invoice_data", {})
        
        return ValidationRequirementsResponse(
            workflow_id=workflow_id,
            contract_name=workflow_state.get("contract_name", "Unknown Contract"),
            user_id=workflow_state.get("user_id", "Unknown User"),
            validation_issues=validation_results.get("issues", []),
            required_fields=human_input_request.get("fields", []),
            current_data=current_data,
            instructions=human_input_request.get("instructions", "Please review and correct the extracted data.")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get validation requirements for workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation requirements: {str(e)}"
        )

@router.get("/format", response_model=DataFormatResponse)
async def get_expected_data_format():
    """
    Get the expected JSON format for corrected_data when resuming workflows
    
    Use this to understand exactly what structure to send in the corrected_data field
    when calling POST /api/v1/validation/resume
    """
    expected_format = {
        "client": {
            "name": "string (required)",
            "email": "string (optional)",
            "address": "string (optional)", 
            "phone": "string (optional)",
            "tax_id": "string (optional)"
        },
        "service_provider": {
            "name": "string (required)",
            "email": "string (optional)",
            "address": "string (optional)",
            "phone": "string (optional)", 
            "tax_id": "string (optional)"
        },
        "payment_terms": {
            "amount": "number (optional)",
            "currency": "string (optional, default: USD)",
            "frequency": "string (optional, e.g., monthly, quarterly)",
            "due_days": "number (optional, default: 30)",
            "late_fee": "number (optional)",
            "discount_terms": "string (optional)",
            "payment_method": "string (optional, default: bank_transfer)"
        },
        "contract_title": "string (optional)",
        "contract_type": "string (optional)",
        "notes": "string (optional)"
    }
    
    example = {
        "client": {
            "name": "test"
        },
        "service_provider": {
            "name": "user"
        },
        "payment_terms": {
            "amount": 1000,
            "currency": "INR",
            "frequency": "monthly"
        }
    }
    
    notes = [
        "Only include fields that you want to correct/update",
        "The correction agent will merge your corrections with existing data",
        "All fields are optional - only send what needs to be changed",
        "Nested objects (client, service_provider, payment_terms) will be merged deeply",
        "Currency codes should be standard 3-letter codes (USD, EUR, INR, etc.)",
        "Frequency values: monthly, quarterly, annually, weekly, one_time",
        "Amount can be sent as number or string - will be converted appropriately"
    ]
    
    return DataFormatResponse(
        expected_format=expected_format,
        example=example,
        notes=notes
    )

@router.post("/resume", response_model=ResumeWorkflowResponse)
async def resume_workflow_with_corrections(
    request: ResumeWorkflowRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Resume workflow from correction agent with human-validated data
    
    This endpoint:
    1. Takes human-corrected validation data
    2. Resumes workflow from correction agent
    3. Continues through invoice generation and UI generation
    4. Returns final status
    """
    try:
        logger.info(f"🔄 Resuming workflow {request.workflow_id} with human corrections")
        
        orchestrator_service = get_orchestrator_service()
        
        # Get workflow from active workflows
        workflow_info = orchestrator_service.active_workflows.get(request.workflow_id)
        if not workflow_info:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {request.workflow_id} not found or has expired"
            )
        
        workflow_state = workflow_info["state"]
        
        # Check if workflow is paused for human input
        if workflow_state.get("processing_status") != "PAUSED_FOR_HUMAN_INPUT":
            raise HTTPException(
                status_code=400,
                detail=f"Workflow {request.workflow_id} is not paused for human input. Current status: {workflow_state.get('processing_status')}"
            )
        
        # Update state with human corrections
        logger.info(f"📝 Applying human corrections: {list(request.corrected_data.keys())}")
        logger.info(f"🔍 Full corrected data: {request.corrected_data}")
        
        # Apply corrections to unified format first, then maintain legacy format
        from schemas.unified_invoice_schemas import UnifiedInvoiceData
        
        # Apply corrections to unified data if available
        if "unified_invoice_data" in workflow_state:
            try:
                unified_data = UnifiedInvoiceData(**workflow_state["unified_invoice_data"])
                corrected_unified = unified_data.apply_manual_corrections(request.corrected_data)
                workflow_state["unified_invoice_data"] = corrected_unified.model_dump()
                logger.info(f"✅ Applied corrections to unified invoice data")
            except Exception as e:
                logger.error(f"❌ Failed to apply corrections to unified data: {e}")
        
        # Maintain legacy format for backward compatibility
        if "invoice_data" in workflow_state:
            invoice_data = workflow_state["invoice_data"]
            logger.info(f"📊 Original invoice_data structure: {list(invoice_data.keys()) if isinstance(invoice_data, dict) else type(invoice_data)}")
            
            if isinstance(invoice_data, dict) and "invoice_response" in invoice_data:
                # Update the invoice data with corrections
                current_invoice_data = invoice_data["invoice_response"].get("invoice_data", {})
                logger.info(f"📋 Before update - current invoice data keys: {list(current_invoice_data.keys()) if isinstance(current_invoice_data, dict) else type(current_invoice_data)}")
                
                # Apply human corrections to the current invoice data
                current_invoice_data.update(request.corrected_data)
                logger.info(f"✅ After update - current invoice data keys: {list(current_invoice_data.keys()) if isinstance(current_invoice_data, dict) else type(current_invoice_data)}")
                
                # Update the nested structure
                invoice_data["invoice_response"]["invoice_data"] = current_invoice_data
                
                # Mark as human-corrected with metadata
                current_invoice_data["human_corrected"] = True
                current_invoice_data["human_corrections_applied_at"] = datetime.now().isoformat()
                current_invoice_data["user_notes"] = request.user_notes
                
                # Also update the root level to ensure consistency
                workflow_state["invoice_data"] = invoice_data
                
                # Store a clean copy for the correction agent to use
                workflow_state["human_corrected_data"] = {
                    "invoice_data": current_invoice_data,
                    "human_corrected": True,
                    "corrections_applied_at": datetime.now().isoformat(),
                    "user_notes": request.user_notes,
                    "corrected_fields": list(request.corrected_data.keys())
                }
                
                logger.info(f"📋 Stored human corrected data with {len(request.corrected_data)} corrections")
        
        # Update workflow state for resumption
        workflow_state["awaiting_human_input"] = False
        workflow_state["workflow_paused"] = False
        workflow_state["processing_status"] = "IN_PROGRESS"
        workflow_state["current_agent"] = "correction"
        workflow_state["human_input_completed"] = True
        workflow_state["human_input_resolved"] = True  # Add this flag for correction agent
        workflow_state["last_updated_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ Workflow state updated with human_input flags: completed={workflow_state.get('human_input_completed')}, resolved={workflow_state.get('human_input_resolved')}")
        
        # Remove pause-related flags
        workflow_state.pop("pause_reason", None)
        
        logger.info(f"✅ State updated, starting correction agent for workflow {request.workflow_id}")
        
        # Execute remaining workflow steps: correction -> invoice generation -> UI generation
        try:
            # Step 1: Correction Agent
            correction_agent = CorrectionAgent()
            workflow_state = await correction_agent.process(workflow_state)
            logger.info(f"✅ Correction agent completed for workflow {request.workflow_id}")
            
            # Step 2: Invoice Generation Agent
            invoice_agent = InvoiceGeneratorAgent()
            workflow_state = await invoice_agent.process(workflow_state)
            logger.info(f"✅ Invoice generation completed for workflow {request.workflow_id}")
            
            # Step 3: UI Invoice Generator Agent
            ui_agent = UIInvoiceGeneratorAgent()
            workflow_state = await ui_agent.process(workflow_state)
            logger.info(f"✅ UI generation completed for workflow {request.workflow_id}")
            
            # Mark workflow as completed
            workflow_state["processing_status"] = "COMPLETED"
            workflow_state["workflow_completed"] = True
            workflow_state["completed_at"] = datetime.now().isoformat()
            
            # Update stored state
            orchestrator_service.active_workflows[request.workflow_id]["state"] = workflow_state
            orchestrator_service.active_workflows[request.workflow_id]["completed_at"] = datetime.now()
            
            return ResumeWorkflowResponse(
                success=True,
                message="Workflow resumed and completed successfully",
                workflow_id=request.workflow_id,
                status="COMPLETED",
                final_invoice_ready=bool(workflow_state.get("final_invoice_json")),
                ui_template_ready=bool(workflow_state.get("ui_invoice_template"))
            )
            
        except Exception as agent_error:
            logger.error(f"❌ Error in workflow agents: {str(agent_error)}")
            
            # Update state with error
            workflow_state["processing_status"] = "FAILED"
            workflow_state["error"] = str(agent_error)
            workflow_state["failed_at"] = datetime.now().isoformat()
            
            # Update stored state
            orchestrator_service.active_workflows[request.workflow_id]["state"] = workflow_state
            
            return ResumeWorkflowResponse(
                success=False,
                message=f"Workflow resumed but failed during processing: {str(agent_error)}",
                workflow_id=request.workflow_id,
                status="FAILED",
                final_invoice_ready=False,
                ui_template_ready=False
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resume workflow {request.workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume workflow: {str(e)}"
        )

@router.get("/status/{workflow_id}")
async def get_workflow_validation_status(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed validation status for a workflow
    """
    try:
        orchestrator_service = get_orchestrator_service()
        
        workflow_info = orchestrator_service.active_workflows.get(workflow_id)
        if not workflow_info:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        
        workflow_state = workflow_info["state"]
        
        return {
            "workflow_id": workflow_id,
            "processing_status": workflow_state.get("processing_status"),
            "current_agent": workflow_state.get("current_agent"),
            "awaiting_human_input": workflow_state.get("awaiting_human_input", False),
            "workflow_paused": workflow_state.get("workflow_paused", False),
            "pause_reason": workflow_state.get("pause_reason"),
            "validation_results": workflow_state.get("validation_results", {}),
            "human_input_completed": workflow_state.get("human_input_completed", False),
            "workflow_completed": workflow_state.get("workflow_completed", False),
            "last_updated": workflow_state.get("last_updated_at"),
            "contract_name": workflow_state.get("contract_name"),
            "user_id": workflow_state.get("user_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get validation status for workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation status: {str(e)}"
        )