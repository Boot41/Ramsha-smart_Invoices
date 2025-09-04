"""
Google Cloud Scheduler Service for Real-Time Invoice Scheduling

This service integrates with Google Cloud Scheduler to trigger 
invoice email sending at specified dates and times.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import scheduler
from google.cloud.scheduler import Job, HttpTarget, OidcToken
import google.auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class CloudSchedulerService:
    """
    Google Cloud Scheduler service for automating invoice email scheduling
    """
    
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """
        Initialize Cloud Scheduler service
        
        Args:
            project_id: GCP Project ID
            location: GCP region for scheduler jobs
        """
        logger.info("🚀 Initializing Cloud Scheduler Service...")
        
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.location = location
        
        if not self.project_id:
            raise ValueError("PROJECT_ID environment variable is required")
        
        # Initialize Cloud Scheduler client
        self.client = scheduler.CloudSchedulerClient()
        
        # Parent path for scheduler jobs
        self.parent = f"projects/{self.project_id}/locations/{self.location}"
        
        # Service endpoints
        self.invoice_processor_url = os.getenv("INVOICE_PROCESSOR_URL", 
                                             "https://your-service-url/process-scheduled-invoices")
        
        logger.info(f"✅ Cloud Scheduler initialized for project: {self.project_id}")
    
    def create_invoice_schedule_job(
        self, 
        job_name: str,
        schedule: str,
        target_date: str,
        description: str = None
    ) -> Dict[str, Any]:
        """
        Create a Cloud Scheduler job for invoice processing
        
        Args:
            job_name: Unique name for the scheduler job
            schedule: Cron expression for scheduling (e.g., "0 9 * * 1" for 9 AM every Monday)
            target_date: Date for invoice processing (YYYY-MM-DD format)
            description: Optional job description
            
        Returns:
            Dictionary with job creation result
        """
        try:
            logger.info(f"📅 Creating scheduler job: {job_name}")
            
            # Full job path
            job_path = f"{self.parent}/jobs/{job_name}"
            
            # Request payload for invoice processing
            request_payload = {
                "target_date": target_date,
                "job_name": job_name,
                "triggered_by": "cloud_scheduler",
                "timestamp": datetime.now().isoformat()
            }
            
            # HTTP target configuration
            http_target = HttpTarget(
                uri=self.invoice_processor_url,
                http_method=HttpTarget.HttpMethod.POST,
                headers={
                    "Content-Type": "application/json"
                },
                body=json.dumps(request_payload).encode("utf-8")
            )
            
            # Add OIDC authentication if needed
            try:
                # Get default credentials for OIDC token
                credentials, _ = google.auth.default()
                service_account_email = credentials.service_account_email
                
                http_target.oidc_token = OidcToken(
                    service_account_email=service_account_email
                )
                logger.info(f"🔐 Added OIDC authentication with {service_account_email}")
            except Exception as auth_error:
                logger.warning(f"⚠️ Could not set up OIDC auth: {str(auth_error)}")
            
            # Create the job
            job = Job(
                name=job_path,
                description=description or f"Invoice processing job for {target_date}",
                schedule=schedule,
                time_zone="UTC",
                http_target=http_target
            )
            
            # Create job in Cloud Scheduler
            response = self.client.create_job(
                parent=self.parent,
                job=job
            )
            
            result = {
                "success": True,
                "message": f"✅ Scheduler job created: {job_name}",
                "job_name": response.name,
                "schedule": schedule,
                "target_date": target_date,
                "next_run_time": None  # Would need to calculate based on cron
            }
            
            logger.info(f"✅ Created scheduler job: {job_name}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error creating scheduler job: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "job_name": job_name,
                "error": str(e)
            }
    
    def create_recurring_invoice_schedule(
        self, 
        client_name: str,
        frequency: str,
        start_date: str,
        hour: int = 9,
        minute: int = 0
    ) -> Dict[str, Any]:
        """
        Create recurring invoice schedule based on frequency
        
        Args:
            client_name: Name of the client for job naming
            frequency: Frequency (daily, weekly, monthly, quarterly)
            start_date: Start date (YYYY-MM-DD)
            hour: Hour to send (0-23, default 9 AM)
            minute: Minute to send (0-59, default 0)
            
        Returns:
            Dictionary with schedule creation result
        """
        try:
            logger.info(f"🔄 Creating recurring schedule for {client_name} - {frequency}")
            
            # Generate cron expression based on frequency
            cron_schedule = self._generate_cron_schedule(frequency, hour, minute, start_date)
            
            if not cron_schedule:
                return {
                    "success": False,
                    "message": f"❌ Unsupported frequency: {frequency}",
                    "client_name": client_name
                }
            
            # Create unique job name
            job_name = f"invoice-{client_name.lower().replace(' ', '-')}-{frequency}"
            
            # Create the scheduler job
            return self.create_invoice_schedule_job(
                job_name=job_name,
                schedule=cron_schedule,
                target_date=start_date,
                description=f"Recurring {frequency} invoice for {client_name}"
            )
            
        except Exception as e:
            error_msg = f"❌ Error creating recurring schedule: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "client_name": client_name,
                "error": str(e)
            }
    
    def _generate_cron_schedule(self, frequency: str, hour: int, minute: int, start_date: str) -> Optional[str]:
        """
        Generate cron expression based on frequency
        
        Args:
            frequency: Frequency string
            hour: Hour (0-23)
            minute: Minute (0-59)
            start_date: Start date for monthly/quarterly calculations
            
        Returns:
            Cron expression string or None if unsupported
        """
        try:
            start_dt = datetime.fromisoformat(start_date)
            
            if frequency == "daily":
                # Every day at specified time
                return f"{minute} {hour} * * *"
            
            elif frequency == "weekly":
                # Every week on the same day as start_date
                day_of_week = start_dt.weekday()  # Monday is 0, Sunday is 6
                # Convert to cron format (Sunday is 0, Saturday is 6)
                cron_day = 0 if day_of_week == 6 else day_of_week + 1
                return f"{minute} {hour} * * {cron_day}"
            
            elif frequency == "monthly":
                # Every month on the same day
                day_of_month = start_dt.day
                return f"{minute} {hour} {day_of_month} * *"
            
            elif frequency == "quarterly":
                # Every 3 months on the same day
                day_of_month = start_dt.day
                month = start_dt.month
                # Create cron for specific months (every 3 months)
                months = []
                for i in range(4):  # 4 quarters
                    quarter_month = ((month - 1 + i * 3) % 12) + 1
                    months.append(str(quarter_month))
                return f"{minute} {hour} {day_of_month} {','.join(months)} *"
            
            else:
                logger.warning(f"⚠️ Unsupported frequency: {frequency}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating cron schedule: {str(e)}")
            return None
    
    def list_scheduled_jobs(self, name_filter: str = None) -> Dict[str, Any]:
        """
        List all scheduled jobs, optionally filtered by name
        
        Args:
            name_filter: Optional filter for job names
            
        Returns:
            Dictionary with job list
        """
        try:
            logger.info("📋 Listing scheduled jobs...")
            
            # List jobs
            jobs = self.client.list_jobs(parent=self.parent)
            
            job_list = []
            for job in jobs:
                if name_filter and name_filter not in job.name:
                    continue
                
                job_info = {
                    "name": job.name.split('/')[-1],  # Extract job name
                    "full_name": job.name,
                    "schedule": job.schedule,
                    "description": job.description,
                    "state": job.state.name if job.state else "UNKNOWN",
                    "time_zone": job.time_zone,
                    "last_attempt_time": job.last_attempt_time.isoformat() if job.last_attempt_time else None,
                    "next_attempt_time": job.schedule_time.isoformat() if job.schedule_time else None
                }
                job_list.append(job_info)
            
            result = {
                "success": True,
                "message": f"✅ Found {len(job_list)} scheduled jobs",
                "total_jobs": len(job_list),
                "jobs": job_list
            }
            
            logger.info(f"✅ Listed {len(job_list)} scheduled jobs")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error listing scheduled jobs: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    def delete_scheduled_job(self, job_name: str) -> Dict[str, Any]:
        """
        Delete a scheduled job
        
        Args:
            job_name: Name of the job to delete
            
        Returns:
            Dictionary with deletion result
        """
        try:
            logger.info(f"🗑️ Deleting scheduled job: {job_name}")
            
            job_path = f"{self.parent}/jobs/{job_name}"
            
            self.client.delete_job(name=job_path)
            
            result = {
                "success": True,
                "message": f"✅ Deleted scheduled job: {job_name}",
                "job_name": job_name
            }
            
            logger.info(f"✅ Deleted scheduled job: {job_name}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error deleting scheduled job: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "job_name": job_name,
                "error": str(e)
            }
    
    def pause_scheduled_job(self, job_name: str) -> Dict[str, Any]:
        """
        Pause a scheduled job
        
        Args:
            job_name: Name of the job to pause
            
        Returns:
            Dictionary with pause result
        """
        try:
            logger.info(f"⏸️ Pausing scheduled job: {job_name}")
            
            job_path = f"{self.parent}/jobs/{job_name}"
            
            self.client.pause_job(name=job_path)
            
            result = {
                "success": True,
                "message": f"✅ Paused scheduled job: {job_name}",
                "job_name": job_name
            }
            
            logger.info(f"✅ Paused scheduled job: {job_name}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error pausing scheduled job: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "job_name": job_name,
                "error": str(e)
            }
    
    def resume_scheduled_job(self, job_name: str) -> Dict[str, Any]:
        """
        Resume a paused scheduled job
        
        Args:
            job_name: Name of the job to resume
            
        Returns:
            Dictionary with resume result
        """
        try:
            logger.info(f"▶️ Resuming scheduled job: {job_name}")
            
            job_path = f"{self.parent}/jobs/{job_name}"
            
            self.client.resume_job(name=job_path)
            
            result = {
                "success": True,
                "message": f"✅ Resumed scheduled job: {job_name}",
                "job_name": job_name
            }
            
            logger.info(f"✅ Resumed scheduled job: {job_name}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error resuming scheduled job: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "job_name": job_name,
                "error": str(e)
            }
    
    def run_job_now(self, job_name: str) -> Dict[str, Any]:
        """
        Trigger a scheduled job to run immediately
        
        Args:
            job_name: Name of the job to run
            
        Returns:
            Dictionary with run result
        """
        try:
            logger.info(f"🚀 Running scheduled job now: {job_name}")
            
            job_path = f"{self.parent}/jobs/{job_name}"
            
            self.client.run_job(name=job_path)
            
            result = {
                "success": True,
                "message": f"✅ Triggered job to run now: {job_name}",
                "job_name": job_name
            }
            
            logger.info(f"✅ Triggered job to run: {job_name}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error running scheduled job: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "job_name": job_name,
                "error": str(e)
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get Cloud Scheduler service status
        
        Returns:
            Dictionary with service status
        """
        try:
            # List jobs to test connectivity
            jobs_result = self.list_scheduled_jobs()
            
            status = {
                "service": "Cloud Scheduler",
                "status": "healthy" if jobs_result["success"] else "error",
                "project_id": self.project_id,
                "location": self.location,
                "total_jobs": jobs_result.get("total_jobs", 0),
                "invoice_processor_url": self.invoice_processor_url,
                "timestamp": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            return {
                "service": "Cloud Scheduler",
                "status": "error",
                "project_id": self.project_id,
                "location": self.location,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global service instance
_cloud_scheduler_service = None

def get_cloud_scheduler_service(project_id: str = None, location: str = "us-central1") -> CloudSchedulerService:
    """Get singleton Cloud Scheduler service instance"""
    global _cloud_scheduler_service
    if _cloud_scheduler_service is None:
        _cloud_scheduler_service = CloudSchedulerService(project_id, location)
    return _cloud_scheduler_service


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    
    def main():
        """Test the Cloud Scheduler Service"""
        service = get_cloud_scheduler_service()
        
        # Test service status
        print("Getting scheduler status...")
        status = service.get_scheduler_status()
        print(f"Status: {json.dumps(status, indent=2)}")
        
        # Test creating a sample job (commented to avoid creating actual jobs)
        # print("\nCreating sample job...")
        # job_result = service.create_recurring_invoice_schedule(
        #     client_name="Test Client",
        #     frequency="weekly",
        #     start_date="2024-09-15",
        #     hour=10,
        #     minute=0
        # )
        # print(f"Job creation result: {job_result}")
        
        # Test listing jobs
        print("\nListing scheduled jobs...")
        jobs_result = service.list_scheduled_jobs()
        print(f"Jobs: {json.dumps(jobs_result, indent=2)}")
    
    main()