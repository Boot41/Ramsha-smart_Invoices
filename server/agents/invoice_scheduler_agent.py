"""
Invoice Scheduling Agent with RAG Capabilities

This agent handles:
1. Extracting invoice scheduling data from Pinecone vector DB via RAG
2. Sending emails on scheduled dates using Gmail MCP server  
3. Real-time scheduling automation
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Import existing services
from services.pinecone_service import get_pinecone_service
from services.llm_service import LLMService
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

@dataclass
class InvoiceSchedule:
    """Data structure for invoice scheduling information"""
    recipient_email: str
    send_dates: List[str]  # ISO format dates
    frequency: str  # daily, weekly, monthly, quarterly
    invoice_template: str
    amount: float
    client_name: str
    service_description: str
    due_days: int = 30
    metadata: Dict[str, Any] = None

@dataclass  
class EmailTemplate:
    """Email template structure for invoice sending"""
    subject: str
    body_html: str
    body_text: str
    attachments: List[str] = None

class InvoiceSchedulerAgent:
    """
    Agentic workflow for automated invoice scheduling and email sending
    """
    
    def __init__(self):
        """Initialize the Invoice Scheduler Agent"""
        logger.info("🚀 Initializing Invoice Scheduler Agent...")
        
        # Initialize services
        self.pinecone_service = get_pinecone_service()
        self.llm_service = LLMService()
        
        # Configure Gemini API
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Gmail MCP server configuration (will be set up later)
        self.gmail_mcp_url = None
        self.gmail_oauth_token = None
        
        logger.info("✅ Invoice Scheduler Agent initialized successfully!")
    
    async def ingest_invoice_schedule_data(self, schedules: List[InvoiceSchedule]) -> Dict[str, Any]:
        """
        Ingest invoice scheduling data into Pinecone vector database
        
        Args:
            schedules: List of InvoiceSchedule objects to store
            
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"📥 Ingesting {len(schedules)} invoice schedules to Pinecone...")
        
        try:
            texts = []
            metadata_list = []
            vector_ids = []
            
            for schedule in schedules:
                # Create comprehensive text for embedding
                schedule_text = self._create_schedule_text(schedule)
                texts.append(schedule_text)
                
                # Create metadata
                metadata = {
                    "type": "invoice_schedule",
                    "recipient_email": schedule.recipient_email,
                    "send_dates": json.dumps(schedule.send_dates),
                    "frequency": schedule.frequency,
                    "client_name": schedule.client_name,
                    "amount": schedule.amount,
                    "service_description": schedule.service_description,
                    "due_days": schedule.due_days,
                    "created_at": datetime.now().isoformat(),
                }
                if schedule.metadata:
                    metadata.update(schedule.metadata)
                
                metadata_list.append(metadata)
                
                # Generate unique vector ID
                vector_id = f"invoice_schedule_{schedule.client_name}_{datetime.now().timestamp()}"
                vector_ids.append(vector_id)
            
            # Store in Pinecone
            result = self.pinecone_service.store_embeddings_batch(
                texts=texts,
                metadata_list=metadata_list, 
                vector_ids=vector_ids
            )
            
            logger.info(f"✅ Successfully ingested {len(schedules)} invoice schedules")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error ingesting invoice schedules: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    def _create_schedule_text(self, schedule: InvoiceSchedule) -> str:
        """Create comprehensive text representation for embedding"""
        return f"""
        Invoice Schedule Information:
        Client: {schedule.client_name}
        Recipient Email: {schedule.recipient_email}
        Service: {schedule.service_description}
        Amount: ${schedule.amount}
        Frequency: {schedule.frequency}
        Send Dates: {', '.join(schedule.send_dates)}
        Due Days: {schedule.due_days}
        Invoice Template: {schedule.invoice_template}
        """
    
    async def retrieve_schedules_by_query(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Retrieve invoice schedules from Pinecone using RAG
        
        Args:
            query: Natural language query about schedules
            top_k: Number of results to return
            
        Returns:
            Dictionary with retrieved schedules
        """
        logger.info(f"🔍 Retrieving schedules for query: '{query}'")
        
        try:
            # Search Pinecone for similar schedules
            search_result = self.pinecone_service.search_similar(
                query_text=query,
                top_k=top_k,
                filter_metadata={"type": "invoice_schedule"}
            )
            
            if not search_result["success"]:
                return search_result
            
            # Parse and format results
            schedules = []
            for match in search_result["results"]:
                metadata = match["metadata"]
                
                schedule = InvoiceSchedule(
                    recipient_email=metadata.get("recipient_email", ""),
                    send_dates=json.loads(metadata.get("send_dates", "[]")),
                    frequency=metadata.get("frequency", ""),
                    invoice_template=metadata.get("invoice_template", ""),
                    amount=metadata.get("amount", 0.0),
                    client_name=metadata.get("client_name", ""),
                    service_description=metadata.get("service_description", ""),
                    due_days=metadata.get("due_days", 30),
                    metadata={"score": match["score"], "vector_id": match["id"]}
                )
                schedules.append(schedule)
            
            result = {
                "success": True,
                "message": f"✅ Retrieved {len(schedules)} schedules",
                "query": query,
                "schedules": schedules,
                "total_matches": len(schedules)
            }
            
            logger.info(f"✅ Retrieved {len(schedules)} schedules for query")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error retrieving schedules: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "query": query,
                "error": str(e)
            }
    
    async def retrieve_schedules_by_date(self, target_date: str) -> Dict[str, Any]:
        """
        Retrieve schedules due on a specific date
        
        Args:
            target_date: Date in ISO format (YYYY-MM-DD)
            
        Returns:
            Dictionary with schedules due on target date
        """
        logger.info(f"📅 Retrieving schedules for date: {target_date}")
        
        query = f"invoice schedules due on {target_date} send date {target_date}"
        return await self.retrieve_schedules_by_query(query)
    
    async def generate_invoice_email_content(self, schedule: InvoiceSchedule) -> EmailTemplate:
        """
        Generate personalized email content for invoice using Gemini AI
        
        Args:
            schedule: InvoiceSchedule object with client information
            
        Returns:
            EmailTemplate with generated content
        """
        logger.info(f"✉️ Generating email content for {schedule.client_name}")
        
        try:
            prompt = f"""
            Generate a professional invoice email for the following details:
            
            Client Name: {schedule.client_name}
            Service Description: {schedule.service_description}
            Amount: ${schedule.amount}
            Due Days: {schedule.due_days}
            
            Create:
            1. A professional email subject line
            2. HTML email body (professional invoice email template)
            3. Plain text version
            
            Make it polite, professional, and include all necessary invoice details.
            Include a clear call-to-action for payment.
            
            Format the response as JSON with keys: subject, body_html, body_text
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            # Parse the response
            try:
                # Clean the response text and extract JSON
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3]  # Remove ```json and ```
                
                email_data = json.loads(response_text)
                
                template = EmailTemplate(
                    subject=email_data.get("subject", f"Invoice for {schedule.client_name}"),
                    body_html=email_data.get("body_html", ""),
                    body_text=email_data.get("body_text", ""),
                    attachments=[]
                )
                
                logger.info(f"✅ Generated email content for {schedule.client_name}")
                return template
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse JSON response, using fallback template")
                return self._create_fallback_email_template(schedule)
                
        except Exception as e:
            logger.error(f"❌ Error generating email content: {str(e)}")
            return self._create_fallback_email_template(schedule)
    
    def _create_fallback_email_template(self, schedule: InvoiceSchedule) -> EmailTemplate:
        """Create fallback email template"""
        subject = f"Invoice - {schedule.service_description} - ${schedule.amount}"
        
        body_html = f"""
        <html>
        <body>
        <h2>Invoice</h2>
        <p>Dear {schedule.client_name},</p>
        <p>Please find your invoice details below:</p>
        <ul>
        <li>Service: {schedule.service_description}</li>
        <li>Amount: ${schedule.amount}</li>
        <li>Due: {schedule.due_days} days</li>
        </ul>
        <p>Thank you for your business!</p>
        </body>
        </html>
        """
        
        body_text = f"""
        Invoice
        
        Dear {schedule.client_name},
        
        Please find your invoice details below:
        - Service: {schedule.service_description}
        - Amount: ${schedule.amount}
        - Due: {schedule.due_days} days
        
        Thank you for your business!
        """
        
        return EmailTemplate(
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )
    
    async def process_scheduled_invoices(self, target_date: str = None) -> Dict[str, Any]:
        """
        Main processing function to handle scheduled invoices for a given date
        
        Args:
            target_date: Date to process (defaults to today)
            
        Returns:
            Dictionary with processing results
        """
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"🔄 Processing scheduled invoices for {target_date}")
        
        try:
            # Step 1: Retrieve schedules due today
            schedules_result = await self.retrieve_schedules_by_date(target_date)
            
            if not schedules_result["success"]:
                return schedules_result
            
            schedules = schedules_result.get("schedules", [])
            logger.info(f"📋 Found {len(schedules)} schedules for {target_date}")
            
            # Step 2: Process each schedule
            processing_results = []
            
            for schedule in schedules:
                logger.info(f"📧 Processing invoice for {schedule.client_name}")
                
                try:
                    # Generate email content
                    email_template = await self.generate_invoice_email_content(schedule)
                    
                    # For now, we'll log the email (Gmail MCP integration will be added)
                    result = {
                        "client_name": schedule.client_name,
                        "recipient_email": schedule.recipient_email,
                        "amount": schedule.amount,
                        "email_subject": email_template.subject,
                        "status": "prepared",  # Will be "sent" when Gmail MCP is integrated
                        "message": "Email content generated successfully"
                    }
                    
                    processing_results.append(result)
                    logger.info(f"✅ Processed invoice for {schedule.client_name}")
                    
                except Exception as e:
                    error_result = {
                        "client_name": schedule.client_name,
                        "recipient_email": schedule.recipient_email,
                        "status": "error",
                        "message": f"Error processing: {str(e)}"
                    }
                    processing_results.append(error_result)
                    logger.error(f"❌ Error processing {schedule.client_name}: {str(e)}")
            
            return {
                "success": True,
                "message": f"✅ Processed {len(schedules)} scheduled invoices",
                "date": target_date,
                "total_schedules": len(schedules),
                "results": processing_results
            }
            
        except Exception as e:
            error_msg = f"❌ Error processing scheduled invoices: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "date": target_date,
                "error": str(e)
            }
    
    async def create_sample_invoice_schedules(self) -> Dict[str, Any]:
        """
        Create sample invoice schedules for testing
        
        Returns:
            Dictionary with creation results
        """
        logger.info("📝 Creating sample invoice schedules...")
        
        # Sample schedules
        sample_schedules = [
            InvoiceSchedule(
                recipient_email="client1@example.com",
                send_dates=["2024-09-05", "2024-10-05", "2024-11-05"],
                frequency="monthly",
                invoice_template="modern",
                amount=2500.00,
                client_name="Acme Corporation",
                service_description="Web Development Services",
                due_days=30
            ),
            InvoiceSchedule(
                recipient_email="client2@example.com", 
                send_dates=["2024-09-07", "2024-09-14", "2024-09-21"],
                frequency="weekly",
                invoice_template="minimalist",
                amount=750.00,
                client_name="TechStart Inc",
                service_description="Digital Marketing Consultation",
                due_days=15
            ),
            InvoiceSchedule(
                recipient_email="client3@example.com",
                send_dates=["2024-09-15", "2024-12-15"],
                frequency="quarterly", 
                invoice_template="vintage",
                amount=5000.00,
                client_name="Enterprise Solutions LLC",
                service_description="Software Development & Maintenance",
                due_days=45
            )
        ]
        
        # Ingest to Pinecone
        result = await self.ingest_invoice_schedule_data(sample_schedules)
        
        logger.info("✅ Sample invoice schedules created")
        return result
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get current status of the Invoice Scheduler Agent
        
        Returns:
            Dictionary with agent status
        """
        try:
            # Get Pinecone stats
            pinecone_stats = self.pinecone_service.get_index_stats()
            
            status = {
                "agent_name": "Invoice Scheduler Agent",
                "status": "healthy",
                "services": {
                    "pinecone": "connected" if pinecone_stats["success"] else "error",
                    "gemini_ai": "connected" if self.gemini_api_key else "not_configured",
                    "gmail_mcp": "pending_setup"
                },
                "capabilities": [
                    "RAG-based schedule retrieval",
                    "AI-powered email generation", 
                    "Automated invoice processing",
                    "Real-time scheduling (pending Gmail MCP)"
                ],
                "pinecone_stats": pinecone_stats.get("stats", {}),
                "timestamp": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            return {
                "agent_name": "Invoice Scheduler Agent",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global agent instance
_invoice_scheduler_agent = None

def get_invoice_scheduler_agent() -> InvoiceSchedulerAgent:
    """Get singleton Invoice Scheduler Agent instance"""
    global _invoice_scheduler_agent
    if _invoice_scheduler_agent is None:
        _invoice_scheduler_agent = InvoiceSchedulerAgent()
    return _invoice_scheduler_agent


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Test the Invoice Scheduler Agent"""
        agent = get_invoice_scheduler_agent()
        
        # Create sample data
        print("Creating sample invoice schedules...")
        result = await agent.create_sample_invoice_schedules()
        print(f"Sample data result: {result}")
        
        # Test retrieval
        print("\nTesting schedule retrieval...")
        schedules = await agent.retrieve_schedules_by_query("monthly invoices for web development")
        print(f"Retrieved schedules: {schedules}")
        
        # Test processing 
        print("\nTesting invoice processing...")
        processing_result = await agent.process_scheduled_invoices("2024-09-05")
        print(f"Processing result: {processing_result}")
        
        # Check agent status
        print("\nAgent status:")
        status = agent.get_agent_status()
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())