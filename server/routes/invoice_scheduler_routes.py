"""
FastAPI routes for Invoice Scheduler Agent

Provides REST API endpoints for:
1. Processing scheduled invoices 
2. Managing invoice schedules
3. Gmail MCP integration
4. Cloud Scheduler management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Import our services
# from agents.invoice_scheduler_agent import get_invoice_scheduler_agent, InvoiceSchedule  # TODO: Update to ADK agents
from services.gmail_mcp_service import get_gmail_mcp_service, EmailMessage
from services.cloud_scheduler_service import get_cloud_scheduler_service
from adk_agents.schedule_retrieval_adk_agent import ScheduleRetrievalADKAgent
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoice-scheduler", tags=["Invoice Scheduler"])

# Pydantic models for request/response
class ScheduleProcessingRequest(BaseModel):
    """Request model for processing scheduled invoices"""
    target_date: Optional[str] = None
    job_name: Optional[str] = None
    triggered_by: Optional[str] = "api"
    timestamp: Optional[str] = None

class InvoiceScheduleRequest(BaseModel):
    """Request model for creating invoice schedules"""
    recipient_email: str
    send_dates: List[str]
    frequency: str
    invoice_template: str
    amount: float
    client_name: str
    service_description: str
    due_days: int = 30
    metadata: Optional[Dict[str, Any]] = None

class RecurringScheduleRequest(BaseModel):
    """Request model for recurring schedule setup"""
    client_name: str
    frequency: str  # daily, weekly, monthly, quarterly
    start_date: str
    hour: int = 9
    minute: int = 0

class EmailTestRequest(BaseModel):
    """Request model for testing email sending"""
    to: str
    subject: str
    body_html: str
    body_text: Optional[str] = None

class ScheduleExtractionRequest(BaseModel):
    """Request model for schedule extraction"""
    user_id: Optional[str] = None

# Initialize services and ADK agents
gmail_service = get_gmail_mcp_service()
scheduler_service = get_cloud_scheduler_service()

# ADK agents
schedule_retrieval_agent = ScheduleRetrievalADKAgent()


class _SimpleInvocationContext:
    """Lightweight shim for InvocationContext used by routes to call ADK agents directly.

    The real ADK InvocationContext has strict validation and additional fields. For route-triggered
    synchronous calls we provide a minimal compatible object that contains a state dict and a
    simple update method.
    """
    def __init__(self, state: dict):
        self.state = state

    def update(self, new_state: dict):
        # Simple merge
        self.state.update(new_state)


async def _run_adk_agent(agent, state: dict) -> dict:
    """Run an ADK agent's run implementation and collect the final state.

    Returns the updated state after the agent runs. This does not try to emulate the full
    InvocationContext API, only provides `.state` and `.update()` used by BaseADKAgent.
    """
    ctx = _SimpleInvocationContext(state)

    # Collect events but ignore streaming details for the HTTP route
    try:
        async for _event in agent.run(state, ctx):
            # Events are SimpleEvent objects; we don't need to surface them here
            pass
    except Exception as e:
        # Ensure the error info is present in returned state
        state.setdefault("errors", []).append({"agent": agent.name, "error": str(e)})
        state["processing_status"] = "failed"

    return state

@router.get("/status")
async def get_agent_status() -> Dict[str, Any]:
    """
    Get status of all invoice scheduling services
    """
    try:
        logger.info("📊 Getting agent status...")
        
        # Get status from all services
        # agent_status = agent.get_agent_status()  # TODO: Update to ADK agents
        scheduler_status = scheduler_service.get_scheduler_status()
        
        # Test Gmail connection
        gmail_test = await gmail_service.test_gmail_connection()

        # Quick health-run for the schedule retrieval agent using a minimal state
        health_state = {
            "workflow_id": "status-check",
            "user_id": "system",
            "processing_status": "pending",
            "current_agent": "schedule_retrieval",
        }
        try:
            await _run_adk_agent(schedule_retrieval_agent, health_state)
            agent_status = {"status": "ok", "last_run_state": health_state}
        except Exception as e:
            agent_status = {"status": "error", "error": str(e)}

        status = {
            "invoice_scheduler_agent": agent_status,
            "cloud_scheduler": scheduler_status,
            "gmail_mcp": {
                "status": "connected" if gmail_test["success"] else "error",
                "details": gmail_test
            },
            "overall_status": "partial",
            "timestamp": datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-scheduled-invoices")
async def process_scheduled_invoices(
    request: ScheduleProcessingRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Main endpoint for processing scheduled invoices
    This endpoint is called by Cloud Scheduler
    """
    try:
        target_date = request.target_date or datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"🔄 Processing scheduled invoices for {target_date}")
        
        # Process invoices in background
        background_tasks.add_task(
            _process_invoices_background,
            target_date,
            request.job_name,
            request.triggered_by
        )
        
        return {
            "success": True,
            "message": f"✅ Invoice processing started for {target_date}",
            "target_date": target_date,
            "job_name": request.job_name,
            "triggered_by": request.triggered_by,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing scheduled invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_invoices_background(target_date: str, job_name: str, triggered_by: str):
    """
    Background task for processing invoices
    """
    try:
        logger.info(f"🔄 Background processing invoices for {target_date}")
        
        # Step 1: Retrieve schedules from Pinecone using the ADK ScheduleRetrievalADKAgent
        state = {
            "workflow_id": f"scheduled-job-{job_name or 'manual'}-{int(datetime.now().timestamp())}",
            "user_id": "system",
            "processing_status": "pending",
            # Mark invoice generation as complete to allow schedule retrieval to proceed
            "invoice_generation_result": {"generation_successful": True},
        }

        try:
            updated_state = await _run_adk_agent(schedule_retrieval_agent, state)
        except Exception as e:
            logger.error(f"❌ ADK schedule retrieval failed: {str(e)}")
            return

        schedules_result = updated_state.get("schedule_retrieval_result", {})

        if not schedules_result or not schedules_result.get("scheduling_successful", False):
            logger.error(f"❌ No schedules or scheduling failed: {schedules_result}")
            return

        # Prefer scheduled_invoices (jobs created), fallback to retrieved_schedules
        schedules = schedules_result.get("scheduled_invoices") or schedules_result.get("retrieved_schedules") or []
        logger.info(f"📋 Found {len(schedules)} schedules for {target_date}")

        # Step 2: Process each schedule (send emails)
        for schedule in schedules:
            try:
                client_name = schedule.get("name") or schedule.get("metadata", {}).get("client_name") or "Client"
                recipient = schedule.get("metadata", {}).get("recipient_email") or schedule.get("recipient_email") or schedule.get("email")
                logger.info(f"📧 Processing invoice for {client_name} -> {recipient}")

                # Basic template when invoice-generation pipeline is not invoked here
                email_template = type("T", (), {})()
                email_template.subject = f"Invoice for {client_name}"
                email_template.body_html = f"<p>Dear {client_name},</p><p>Your invoice is scheduled according to {schedule.get('frequency', 'schedule')}.</p>"
                email_template.body_text = f"Dear {client_name}, Your invoice is scheduled."

                if not recipient:
                    logger.error(f"❌ No recipient found for schedule {schedule}")
                    continue

                email_message = EmailMessage(
                    to=recipient,
                    subject=email_template.subject,
                    body_html=email_template.body_html,
                    body_text=email_template.body_text
                )

                send_result = await gmail_service.send_email(email_message)

                if send_result.get("success"):
                    logger.info(f"✅ Email sent successfully to {client_name} ({recipient})")
                else:
                    logger.error(f"❌ Failed to send email to {client_name} ({recipient}): {send_result.get('message')}")

            except Exception as e:
                logger.error(f"❌ Error processing schedule for {schedule}: {str(e)}")

        logger.info(f"✅ Completed background processing for {target_date}")
        
    except Exception as e:
        logger.error(f"❌ Error in background processing: {str(e)}")


# ...existing code...
@router.get("/schedules/search")
async def search_invoice_schedules(query: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Search for invoice schedules using natural language query
    """
    try:
        logger.info(f"🔍 Searching schedules for query: {query}")
        
        # Attempt ADK-based retrieval
        state = {
            "workflow_id": f"nl-search-{int(datetime.now().timestamp())}",
            "user_id": "system",
            "processing_status": "pending",
            "nl_query": query,
            "top_k": top_k,
            # Provide minimal invoice_generation_result if ADK workflow expects it
            "invoice_generation_result": {"generation_successful": True},
        }

        try:
            updated_state = await _run_adk_agent(schedule_retrieval_agent, state)
            res = updated_state.get("schedule_retrieval_result", {})
            schedules = res.get("retrieved_schedules", []) or res.get("scheduled_invoices", [])
            result = {"success": True, "schedules": schedules, "raw": res}
        except Exception as e:
            logger.error(f"❌ ADK schedule search failed: {str(e)}")
            result = {
                "success": False,
                "message": "Invoice scheduler agent needs to be updated to ADK interface",
                "error": str(e)
            }
        
        # Convert schedules to dict for JSON serialization (schedules are dict-like)
        if result.get("success") and "schedules" in result:
            schedules_dict = []
            for schedule in result["schedules"]:
                schedules_dict.append({
                    "recipient_email": schedule.get("recipient_email") or schedule.get("email"),
                    "send_dates": schedule.get("send_dates") or schedule.get("dates") or [],
                    "frequency": schedule.get("frequency"),
                    "invoice_template": schedule.get("invoice_template"),
                    "amount": schedule.get("amount"),
                    "client_name": schedule.get("client_name") or schedule.get("name"),
                    "service_description": schedule.get("service_description"),
                    "due_days": schedule.get("due_days"),
                    "metadata": schedule.get("metadata", {})
                })
            result["schedules"] = schedules_dict
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error searching schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
# ...existing code...

@router.get("/schedules/date/{target_date}")
async def get_schedules_by_date(target_date: str) -> Dict[str, Any]:
    """
    Get invoice schedules for a specific date
    """
    try:
        logger.info(f"📅 Getting schedules for date: {target_date}")
        
        # Use ADK schedule retrieval with a minimal state indicating date filtering
        state = {
            "workflow_id": f"date-search-{target_date}-{int(datetime.now().timestamp())}",
            "user_id": "system",
            "processing_status": "pending",
            "target_date": target_date,
            "invoice_generation_result": {"generation_successful": True}
        }

        try:
            updated_state = await _run_adk_agent(schedule_retrieval_agent, state)
            res = updated_state.get("schedule_retrieval_result", {})
            schedules = res.get("retrieved_schedules", []) or res.get("scheduled_invoices", [])
            result = {"success": True, "schedules": schedules, "raw": res}
        except Exception as e:
            logger.error(f"❌ ADK schedule retrieval failed for date {target_date}: {str(e)}")
            result = {"success": False, "message": str(e)}
        
        # Convert schedules to dict for JSON serialization
        if result.get("success") and "schedules" in result:
            schedules_dict = []
            for schedule in result["schedules"]:
                schedules_dict.append({
                    "recipient_email": schedule.get("recipient_email") or schedule.get("email"),
                    "send_dates": schedule.get("send_dates") or schedule.get("dates") or [],
                    "frequency": schedule.get("frequency"),
                    "invoice_template": schedule.get("invoice_template"),
                    "amount": schedule.get("amount"),
                    "client_name": schedule.get("client_name") or schedule.get("name"),
                    "service_description": schedule.get("service_description"),
                    "due_days": schedule.get("due_days"),
                    "metadata": schedule.get("metadata", {})
                })
            result["schedules"] = schedules_dict
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting schedules by date: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
# ...existing code...

@router.post("/schedules/create-samples")
async def create_sample_schedules() -> Dict[str, Any]:
    """
    Create sample invoice schedules for testing
    """
    try:
        logger.info("📝 Creating sample invoice schedules...")
        
        # Try to trigger ADK sample creation workflow if available
        state = {
            "workflow_id": f"create-samples-{int(datetime.now().timestamp())}",
            "user_id": "system",
            "processing_status": "pending",
            "action": "create_sample_schedules"
        }
        try:
            updated_state = await _run_adk_agent(schedule_retrieval_agent, state)
            res = updated_state.get("sample_creation_result", {}) or updated_state.get("schedule_retrieval_result", {})
            if res:
                return {"success": True, "result": res}
            else:
                return {"success": False, "message": "ADK agent ran but returned no sample creation result", "raw": updated_state}
        except Exception as e:
            logger.error(f"❌ ADK sample creation failed: {str(e)}")
            return {
                "success": False,
                "message": "Invoice scheduler agent needs to be updated to ADK interface",
                "error": str(e)
            }
        
    except Exception as e:
        logger.error(f"❌ Error creating sample schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
# ...existing code...

# @router.post("/schedules/extract")
# async def extract_schedules_from_invoices(request: ScheduleExtractionRequest) -> Dict[str, Any]:
#     """
#     Extract schedule details from database invoices using RAG
#     """
#     try:
#         logger.info(f"📊 Extracting schedules from invoices for user: {request.user_id or 'all users'}")
        
#         state = {
#             "workflow_id": f"extract-schedules-{int(datetime.now().timestamp())}",
#             "user_id": request.user_id or "system",
#             "processing_status": "pending",
#             "action": "extract_schedules"
#         }
#         try:
#             updated_state = await _run_adk_agent(schedule_retrieval_agent, state)
#             res = updated_state.get("extraction_result") or updated_state.get("schedule_retrieval_result") or {}
#             if res:
#                 return {"success": True, "result": res}
#             else:
#                 return {"success": False, "message": "ADK agent ran but returned no extraction result", "raw": updated_state}
#         except Exception as e:
#             logger.error(f"❌ ADK extraction failed: {str(e)}")
#             return {
#                 "success": False,
#                 "message": "Invoice scheduler agent needs to be updated to ADK interface",
#                 "error": str(e)
#             }
        
#     except Exception as e:
#         logger.error(f"❌ Error extracting schedules from invoices: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules")
async def create_invoice_schedules(schedules: List[InvoiceScheduleRequest]) -> Dict[str, Any]:
    """
    Create and store invoice schedules in Pinecone
    """
    try:
        logger.info(f"📝 Creating {len(schedules)} invoice schedules...")
        
        # Convert to InvoiceSchedule objects
        schedule_objects = []
        for schedule in schedules:
            schedule_objects.append({
                "recipient_email": schedule.recipient_email,
                "send_dates": schedule.send_dates,
                "frequency": schedule.frequency,
                "invoice_template": schedule.invoice_template,
                "amount": schedule.amount,
                "client_name": schedule.client_name,
                "service_description": schedule.service_description,
                "due_days": schedule.due_days,
                "metadata": schedule.metadata or {}
            })
            # recipient_email=schedule.recipient_email,
            # send_dates=schedule.send_dates,
            # frequency=schedule.frequency,
            # invoice_template=schedule.invoice_template,
            # amount=schedule.amount,
            # client_name=schedule.client_name,
            # service_description=schedule.service_description,
            # due_days=schedule.due_days,
            # metadata=schedule.metadata
            # )
            # schedule_objects.append(schedule_obj)
        
        # Store in Pinecone
        # result = await agent.ingest_invoice_schedule_data(schedule_objects)  # TODO: Update to ADK agents

        # Note: actual ingestion into a vector store / ADK index is not implemented here.
        # Return converted schedules as acknowledgement.
        return {"success": True, "ingested": False, "schedules": schedule_objects}

    except Exception as e:
        logger.error(f"❌ Error creating schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/search")
async def search_invoice_schedules(query: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Search for invoice schedules using natural language query
    """
    try:
        logger.info(f"🔍 Searching schedules for query: {query}")
        
        # result = await agent.retrieve_schedules_by_query(query, top_k)  # TODO: Update to ADK agents
        result = {
            "success": False,
            "message": "Invoice scheduler agent needs to be updated to ADK interface"
        }
        
        # Convert schedules to dict for JSON serialization
        if result["success"] and "schedules" in result:
            schedules_dict = []
            for schedule in result["schedules"]:
                schedules_dict.append({
                    "recipient_email": schedule.recipient_email,
                    "send_dates": schedule.send_dates,
                    "frequency": schedule.frequency,
                    "invoice_template": schedule.invoice_template,
                    "amount": schedule.amount,
                    "client_name": schedule.client_name,
                    "service_description": schedule.service_description,
                    "due_days": schedule.due_days,
                    "metadata": schedule.metadata
                })
            result["schedules"] = schedules_dict
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error searching schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/date/{target_date}")
async def get_schedules_by_date(target_date: str) -> Dict[str, Any]:
    """
    Get invoice schedules for a specific date
    """
    try:
        logger.info(f"📅 Getting schedules for date: {target_date}")
        
        # Use ADK schedule retrieval with a minimal state indicating date filtering
        state = {
            "workflow_id": f"date-search-{target_date}",
            "user_id": "system",
            "processing_status": "pending",
            "invoice_generation_result": {"generation_successful": True}
        }

        try:
            updated_state = await _run_adk_agent(schedule_retrieval_agent, state)
            res = updated_state.get("schedule_retrieval_result", {})
            result = {"success": True, "schedules": res.get("retrieved_schedules", []), "raw": res}
        except Exception as e:
            result = {"success": False, "message": str(e)}
        
        # Convert schedules to dict for JSON serialization
        if result["success"] and "schedules" in result:
            schedules_dict = []
            for schedule in result["schedules"]:
                schedules_dict.append({
                    "recipient_email": schedule.recipient_email,
                    "send_dates": schedule.send_dates,
                    "frequency": schedule.frequency,
                    "invoice_template": schedule.invoice_template,
                    "amount": schedule.amount,
                    "client_name": schedule.client_name,
                    "service_description": schedule.service_description,
                    "due_days": schedule.due_days,
                    "metadata": schedule.metadata
                })
            result["schedules"] = schedules_dict
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting schedules by date: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules/create-samples")
async def create_sample_schedules() -> Dict[str, Any]:
    """
    Create sample invoice schedules for testing
    """
    try:
        logger.info("📝 Creating sample invoice schedules...")
        
        # result = await agent.create_sample_invoice_schedules()  # TODO: Update to ADK agents
        result = {
            "success": False,
            "message": "Invoice scheduler agent needs to be updated to ADK interface"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creating sample schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules/extract")
async def extract_schedules_from_invoices(request: ScheduleExtractionRequest) -> Dict[str, Any]:
    """
    Extract schedule details from database invoices using RAG
    
    This endpoint fetches invoices from the database, identifies their contract IDs,
    and uses RAG to retrieve basic schedule details including:
    - Number of times invoice should be sent
    - Frequency (monthly, quarterly, etc.)
    - Send dates
    """
    try:
        logger.info(f"📊 Extracting schedules from invoices for user: {request.user_id or 'all users'}")
        
        # result = await agent.fetch_invoices_and_extract_schedules(user_id=request.user_id)  # TODO: Update to ADK agents
        result = {
            "success": False,
            "message": "Invoice scheduler agent needs to be updated to ADK interface"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error extracting schedules from invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gmail/test-email")
async def test_email_sending(request: EmailTestRequest) -> Dict[str, Any]:
    """
    Test email sending via Gmail MCP
    """
    try:
        logger.info(f"📧 Testing email sending to {request.to}")
        
        email_message = EmailMessage(
            to=request.to,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text or request.body_html
        )
        
        result = await gmail_service.send_email(email_message)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error testing email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail/test-connection")
async def test_gmail_connection() -> Dict[str, Any]:
    """
    Test Gmail connection and authentication
    """
    try:
        logger.info("🧪 Testing Gmail connection...")
        
        result = await gmail_service.test_gmail_connection()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error testing Gmail connection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail/oauth-url")
async def get_oauth_url() -> Dict[str, Any]:
    """
    Get OAuth2 authorization URL for Gmail setup
    """
    try:
        result = gmail_service.get_oauth_authorization_url()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting OAuth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/recurring")
async def create_recurring_schedule(request: RecurringScheduleRequest) -> Dict[str, Any]:
    """
    Create recurring invoice schedule with Cloud Scheduler
    """
    try:
        logger.info(f"🔄 Creating recurring schedule for {request.client_name}")
        
        result = scheduler_service.create_recurring_invoice_schedule(
            client_name=request.client_name,
            frequency=request.frequency,
            start_date=request.start_date,
            hour=request.hour,
            minute=request.minute
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creating recurring schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduler/jobs")
async def list_scheduled_jobs(name_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    List all scheduled jobs
    """
    try:
        result = scheduler_service.list_scheduled_jobs(name_filter)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error listing scheduled jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/scheduler/jobs/{job_name}")
async def delete_scheduled_job(job_name: str) -> Dict[str, Any]:
    """
    Delete a scheduled job
    """
    try:
        result = scheduler_service.delete_scheduled_job(job_name)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error deleting scheduled job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/jobs/{job_name}/pause")
async def pause_scheduled_job(job_name: str) -> Dict[str, Any]:
    """
    Pause a scheduled job
    """
    try:
        result = scheduler_service.pause_scheduled_job(job_name)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error pausing scheduled job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/jobs/{job_name}/resume")
async def resume_scheduled_job(job_name: str) -> Dict[str, Any]:
    """
    Resume a paused scheduled job
    """
    try:
        result = scheduler_service.resume_scheduled_job(job_name)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error resuming scheduled job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/jobs/{job_name}/run")
async def run_job_now(job_name: str) -> Dict[str, Any]:
    """
    Trigger a scheduled job to run immediately
    """
    try:
        result = scheduler_service.run_job_now(job_name)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error running scheduled job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))