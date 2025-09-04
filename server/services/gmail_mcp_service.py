"""
Gmail MCP Server Integration Service

This service integrates with Gmail MCP server for sending emails.
Supports OAuth2 authentication and email sending functionality.
"""

import os
import json
import httpx
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

@dataclass
class EmailMessage:
    """Email message structure"""
    to: str
    subject: str
    body_html: str
    body_text: str = ""
    cc: List[str] = None
    bcc: List[str] = None
    attachments: List[Dict[str, Any]] = None

@dataclass
class GmailCredentials:
    """Gmail OAuth2 credentials"""
    client_id: str
    client_secret: str
    refresh_token: str
    access_token: str = None

class GmailMCPService:
    """
    Gmail MCP Server integration service for sending emails
    """
    
    def __init__(self, mcp_server_url: str = None):
        """
        Initialize Gmail MCP service
        
        Args:
            mcp_server_url: URL of the deployed Gmail MCP server
        """
        logger.info("🚀 Initializing Gmail MCP Service...")
        
        # MCP Server configuration
        self.mcp_server_url = mcp_server_url or os.getenv("GMAIL_MCP_SERVER_URL")
        if not self.mcp_server_url:
            logger.warning("⚠️ Gmail MCP server URL not configured")
        
        # OAuth2 credentials from environment
        self.credentials = GmailCredentials(
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),  # Will be obtained via OAuth flow
            access_token=os.getenv("GOOGLE_ACCESS_TOKEN")     # Will be refreshed automatically
        )
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info("✅ Gmail MCP Service initialized!")
    
    def _validate_configuration(self):
        """Validate service configuration"""
        missing_configs = []
        
        if not self.credentials.client_id:
            missing_configs.append("GOOGLE_CLIENT_ID")
        if not self.credentials.client_secret:
            missing_configs.append("GOOGLE_CLIENT_SECRET")
        
        if missing_configs:
            logger.warning(f"⚠️ Missing OAuth2 configurations: {', '.join(missing_configs)}")
        else:
            logger.info("✅ OAuth2 credentials configured")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh OAuth2 access token using refresh token
        
        Returns:
            Dictionary with token refresh result
        """
        try:
            if not self.credentials.refresh_token:
                return {
                    "success": False,
                    "message": "❌ No refresh token available",
                    "error": "missing_refresh_token"
                }
            
            logger.info("🔄 Refreshing OAuth2 access token...")
            
            token_data = {
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "refresh_token": self.credentials.refresh_token,
                "grant_type": "refresh_token"
            }
            
            response = await self.http_client.post(
                "https://oauth2.googleapis.com/token",
                data=token_data
            )
            
            if response.status_code == 200:
                token_info = response.json()
                self.credentials.access_token = token_info.get("access_token")
                
                logger.info("✅ Access token refreshed successfully")
                return {
                    "success": True,
                    "message": "✅ Access token refreshed",
                    "access_token": self.credentials.access_token,
                    "expires_in": token_info.get("expires_in", 3600)
                }
            else:
                error_msg = f"❌ Token refresh failed: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "status_code": response.status_code,
                    "response": response.text
                }
                
        except Exception as e:
            error_msg = f"❌ Error refreshing access token: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    async def send_email_via_mcp(self, email: EmailMessage) -> Dict[str, Any]:
        """
        Send email via Gmail MCP server
        
        Args:
            email: EmailMessage object with email details
            
        Returns:
            Dictionary with sending result
        """
        try:
            if not self.mcp_server_url:
                return {
                    "success": False,
                    "message": "❌ Gmail MCP server URL not configured",
                    "error": "missing_mcp_server_url"
                }
            
            logger.info(f"📤 Sending email to {email.to} via MCP server...")
            
            # Ensure we have a valid access token
            if not self.credentials.access_token:
                token_result = await self.refresh_access_token()
                if not token_result["success"]:
                    return token_result
            
            # Prepare email payload for MCP server
            email_payload = {
                "method": "send_email",
                "params": {
                    "to": email.to,
                    "subject": email.subject,
                    "body_html": email.body_html,
                    "body_text": email.body_text or email.body_html,
                    "cc": email.cc or [],
                    "bcc": email.bcc or [],
                    "attachments": email.attachments or []
                },
                "credentials": {
                    "access_token": self.credentials.access_token
                }
            }
            
            # Send to MCP server
            response = await self.http_client.post(
                f"{self.mcp_server_url}/gmail/send",
                json=email_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.credentials.access_token}"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Email sent successfully to {email.to}")
                return {
                    "success": True,
                    "message": f"✅ Email sent to {email.to}",
                    "recipient": email.to,
                    "subject": email.subject,
                    "mcp_response": result
                }
            else:
                error_msg = f"❌ MCP server error: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "recipient": email.to,
                    "status_code": response.status_code,
                    "response": response.text
                }
                
        except Exception as e:
            error_msg = f"❌ Error sending email via MCP: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "recipient": email.to,
                "error": str(e)
            }
    
    async def send_email_direct_gmail(self, email: EmailMessage) -> Dict[str, Any]:
        """
        Send email directly via Gmail API (fallback method)
        
        Args:
            email: EmailMessage object with email details
            
        Returns:
            Dictionary with sending result
        """
        try:
            logger.info(f"📤 Sending email directly via Gmail API to {email.to}...")
            
            # Ensure we have a valid access token
            if not self.credentials.access_token:
                token_result = await self.refresh_access_token()
                if not token_result["success"]:
                    return token_result
            
            # Create email message in Gmail API format
            import base64
            import email.mime.multipart
            import email.mime.text
            
            msg = email.mime.multipart.MIMEMultipart('alternative')
            msg['To'] = email.to
            msg['Subject'] = email.subject
            
            # Add text and HTML parts
            if email.body_text:
                text_part = email.mime.text.MIMEText(email.body_text, 'plain')
                msg.attach(text_part)
            
            if email.body_html:
                html_part = email.mime.text.MIMEText(email.body_html, 'html')
                msg.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            
            # Send via Gmail API
            gmail_payload = {
                "raw": raw_message
            }
            
            response = await self.http_client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                json=gmail_payload,
                headers={
                    "Authorization": f"Bearer {self.credentials.access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Email sent successfully via Gmail API to {email.to}")
                return {
                    "success": True,
                    "message": f"✅ Email sent to {email.to} via Gmail API",
                    "recipient": email.to,
                    "subject": email.subject,
                    "message_id": result.get("id"),
                    "method": "gmail_api_direct"
                }
            else:
                error_msg = f"❌ Gmail API error: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "recipient": email.to,
                    "status_code": response.status_code,
                    "response": response.text,
                    "method": "gmail_api_direct"
                }
                
        except Exception as e:
            error_msg = f"❌ Error sending email via Gmail API: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "recipient": email.to,
                "error": str(e),
                "method": "gmail_api_direct"
            }
    
    async def send_email(self, email: EmailMessage, use_mcp: bool = True) -> Dict[str, Any]:
        """
        Send email using preferred method (MCP server or direct Gmail API)
        
        Args:
            email: EmailMessage object with email details
            use_mcp: Whether to use MCP server (falls back to direct API if fails)
            
        Returns:
            Dictionary with sending result
        """
        logger.info(f"📧 Sending email to {email.to} - Subject: {email.subject}")
        
        if use_mcp and self.mcp_server_url:
            # Try MCP server first
            result = await self.send_email_via_mcp(email)
            if result["success"]:
                return result
            
            # Fall back to direct Gmail API
            logger.warning("MCP server failed, falling back to direct Gmail API...")
            return await self.send_email_direct_gmail(email)
        else:
            # Use direct Gmail API
            return await self.send_email_direct_gmail(email)
    
    async def send_batch_emails(self, emails: List[EmailMessage]) -> Dict[str, Any]:
        """
        Send multiple emails in batch
        
        Args:
            emails: List of EmailMessage objects
            
        Returns:
            Dictionary with batch sending results
        """
        logger.info(f"📤 Sending batch of {len(emails)} emails...")
        
        results = []
        successful_sends = 0
        failed_sends = 0
        
        for email in emails:
            try:
                result = await self.send_email(email)
                results.append(result)
                
                if result["success"]:
                    successful_sends += 1
                else:
                    failed_sends += 1
                    
            except Exception as e:
                error_result = {
                    "success": False,
                    "message": f"❌ Error sending to {email.to}: {str(e)}",
                    "recipient": email.to,
                    "error": str(e)
                }
                results.append(error_result)
                failed_sends += 1
        
        return {
            "success": failed_sends == 0,
            "message": f"📧 Batch email results: {successful_sends} sent, {failed_sends} failed",
            "total_emails": len(emails),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "results": results
        }
    
    async def test_gmail_connection(self) -> Dict[str, Any]:
        """
        Test Gmail connection and authentication
        
        Returns:
            Dictionary with test results
        """
        logger.info("🧪 Testing Gmail connection...")
        
        try:
            # Test token refresh
            token_result = await self.refresh_access_token()
            
            if not token_result["success"]:
                return {
                    "success": False,
                    "message": "❌ OAuth2 authentication failed",
                    "details": token_result
                }
            
            # Test Gmail API access
            response = await self.http_client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/profile",
                headers={
                    "Authorization": f"Bearer {self.credentials.access_token}"
                }
            )
            
            if response.status_code == 200:
                profile = response.json()
                return {
                    "success": True,
                    "message": "✅ Gmail connection successful",
                    "email_address": profile.get("emailAddress"),
                    "messages_total": profile.get("messagesTotal"),
                    "access_token_valid": True
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ Gmail API access failed: {response.status_code}",
                    "status_code": response.status_code,
                    "response": response.text
                }
                
        except Exception as e:
            error_msg = f"❌ Error testing Gmail connection: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    def get_oauth_authorization_url(self) -> Dict[str, Any]:
        """
        Generate OAuth2 authorization URL for Gmail access
        
        Returns:
            Dictionary with authorization URL and instructions
        """
        if not self.credentials.client_id:
            return {
                "success": False,
                "message": "❌ Google Client ID not configured"
            }
        
        import urllib.parse
        
        # OAuth2 parameters
        params = {
            "client_id": self.credentials.client_id,
            "redirect_uri": "http://localhost:8080/oauth2callback",  # Configure as needed
            "scope": "https://www.googleapis.com/auth/gmail.send",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
        
        return {
            "success": True,
            "message": "✅ OAuth2 authorization URL generated",
            "authorization_url": auth_url,
            "instructions": [
                "1. Visit the authorization URL",
                "2. Authorize the application",
                "3. Copy the authorization code from the callback",
                "4. Exchange the code for refresh token"
            ]
        }
    
    async def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            authorization_code: Code received from OAuth2 callback
            
        Returns:
            Dictionary with token exchange result
        """
        try:
            logger.info("🔄 Exchanging authorization code for tokens...")
            
            token_data = {
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "code": authorization_code,
                "grant_type": "authorization_code",
                "redirect_uri": "http://localhost:8080/oauth2callback"
            }
            
            response = await self.http_client.post(
                "https://oauth2.googleapis.com/token",
                data=token_data
            )
            
            if response.status_code == 200:
                tokens = response.json()
                
                # Update credentials
                self.credentials.access_token = tokens.get("access_token")
                self.credentials.refresh_token = tokens.get("refresh_token")
                
                logger.info("✅ Tokens obtained successfully")
                return {
                    "success": True,
                    "message": "✅ OAuth2 tokens obtained",
                    "access_token": self.credentials.access_token,
                    "refresh_token": self.credentials.refresh_token,
                    "expires_in": tokens.get("expires_in", 3600),
                    "note": "Save the refresh_token to environment variables"
                }
            else:
                error_msg = f"❌ Token exchange failed: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "status_code": response.status_code,
                    "response": response.text
                }
                
        except Exception as e:
            error_msg = f"❌ Error exchanging code for tokens: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            import asyncio
            asyncio.create_task(self.http_client.aclose())
        except:
            pass


# Global service instance
_gmail_mcp_service = None

def get_gmail_mcp_service(mcp_server_url: str = None) -> GmailMCPService:
    """Get singleton Gmail MCP service instance"""
    global _gmail_mcp_service
    if _gmail_mcp_service is None:
        _gmail_mcp_service = GmailMCPService(mcp_server_url)
    return _gmail_mcp_service


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Test the Gmail MCP Service"""
        service = get_gmail_mcp_service()
        
        # Test OAuth setup
        print("Getting OAuth authorization URL...")
        auth_result = service.get_oauth_authorization_url()
        print(f"Authorization: {auth_result}")
        
        # Test Gmail connection (requires valid tokens)
        print("\nTesting Gmail connection...")
        connection_result = await service.test_gmail_connection()
        print(f"Connection test: {connection_result}")
        
        # Test email sending (commented out to avoid sending test emails)
        # print("\nTesting email sending...")
        # test_email = EmailMessage(
        #     to="test@example.com",
        #     subject="Test Email from Invoice Scheduler",
        #     body_html="<h1>Test</h1><p>This is a test email.</p>",
        #     body_text="Test\n\nThis is a test email."
        # )
        # send_result = await service.send_email(test_email)
        # print(f"Send result: {send_result}")
        
        await service.close()
    
    asyncio.run(main())