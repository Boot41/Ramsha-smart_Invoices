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
from agents.invoice_scheduler_agent import get_invoice_scheduler_agent, InvoiceSchedule
from services.gmail_mcp_service import get_gmail_mcp_service, EmailMessage
from services.cloud_scheduler_service import get_cloud_scheduler_service

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

# Initialize services
agent = get_invoice_scheduler_agent()
gmail_service = get_gmail_mcp_service()
scheduler_service = get_cloud_scheduler_service()

@router.get("/status")
async def get_agent_status() -> Dict[str, Any]:
    """
    Get status of all invoice scheduling services
    """
    try:
        logger.info("📊 Getting agent status...")
        
        # Get status from all services
        agent_status = agent.get_agent_status()
        scheduler_status = scheduler_service.get_scheduler_status()
        
        # Test Gmail connection
        gmail_test = await gmail_service.test_gmail_connection()
        
        status = {
            "invoice_scheduler_agent": agent_status,
            "cloud_scheduler": scheduler_status,
            "gmail_mcp": {
                "status": "connected" if gmail_test["success"] else "error",
                "details": gmail_test
            },
            "overall_status": "healthy",
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
        
        # Step 1: Retrieve schedules from Pinecone using RAG
        schedules_result = await agent.retrieve_schedules_by_date(target_date)
        
        if not schedules_result["success"]:
            logger.error(f"❌ Failed to retrieve schedules: {schedules_result['message']}")
            return
        
        schedules = schedules_result.get("schedules", [])
        logger.info(f"📋 Found {len(schedules)} schedules for {target_date}")
        
        # Step 2: Process each schedule
        for schedule in schedules:
            try:
                logger.info(f"📧 Processing invoice for {schedule.client_name}")
                
                # Generate email content using AI
                email_template = await agent.generate_invoice_email_content(schedule)
                
                # Create email message
                email_message = EmailMessage(
                    to=schedule.recipient_email,
                    subject=email_template.subject,
                    body_html=email_template.body_html,
                    body_text=email_template.body_text
                )
                
                # Send email via Gmail MCP
                send_result = await gmail_service.send_email(email_message)
                
                if send_result["success"]:
                    logger.info(f"✅ Email sent successfully to {schedule.client_name}")
                else:
                    logger.error(f"❌ Failed to send email to {schedule.client_name}: {send_result['message']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {schedule.client_name}: {str(e)}")
        
        logger.info(f"✅ Completed background processing for {target_date}")
        
    except Exception as e:
        logger.error(f"❌ Error in background processing: {str(e)}")

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
            schedule_obj = InvoiceSchedule(
                recipient_email=schedule.recipient_email,
                send_dates=schedule.send_dates,
                frequency=schedule.frequency,
                invoice_template=schedule.invoice_template,
                amount=schedule.amount,
                client_name=schedule.client_name,
                service_description=schedule.service_description,
                due_days=schedule.due_days,
                metadata=schedule.metadata
            )
            schedule_objects.append(schedule_obj)
        
        # Store in Pinecone
        result = await agent.ingest_invoice_schedule_data(schedule_objects)
        
        return result
        
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
        
        result = await agent.retrieve_schedules_by_query(query, top_k)
        
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
        
        result = await agent.retrieve_schedules_by_date(target_date)
        
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
        
        result = await agent.create_sample_invoice_schedules()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creating sample schedules: {str(e)}")
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