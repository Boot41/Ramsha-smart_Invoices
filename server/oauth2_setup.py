#!/usr/bin/env python3
"""
OAuth2 Setup Helper for Gmail Access

This script helps you complete the OAuth2 flow to get Gmail access tokens.
"""

import asyncio
import webbrowser
import urllib.parse as urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from services.gmail_mcp_service import get_gmail_mcp_service
import json

class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth2 callback"""
    
    def do_GET(self):
        """Handle GET request with authorization code"""
        # Parse the URL to get the authorization code
        parsed_url = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            # Got authorization code
            auth_code = query_params['code'][0]
            print(f"\n✅ Authorization code received: {auth_code[:20]}...")
            
            # Store the code globally so we can access it
            OAuth2CallbackHandler.auth_code = auth_code
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <html>
            <head><title>OAuth2 Success</title></head>
            <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can now close this browser tab and return to the terminal.</p>
                <script>setTimeout(function(){ window.close(); }, 3000);</script>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
            
        elif 'error' in query_params:
            # OAuth error
            error = query_params['error'][0]
            print(f"\n❌ OAuth2 error: {error}")
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <html>
            <head><title>OAuth2 Error</title></head>
            <body>
                <h1>❌ Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
        
        else:
            # Unknown request
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Invalid request")
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass

async def setup_gmail_oauth():
    """Complete Gmail OAuth2 setup process"""
    
    print("🔐 Gmail OAuth2 Setup")
    print("=" * 50)
    
    # Initialize Gmail service
    gmail_service = get_gmail_mcp_service()
    
    # Step 1: Get authorization URL
    print("📋 Step 1: Getting authorization URL...")
    auth_result = gmail_service.get_oauth_authorization_url()
    
    if not auth_result["success"]:
        print(f"❌ Failed to get authorization URL: {auth_result['message']}")
        return False
    
    auth_url = auth_result["authorization_url"]
    print(f"✅ Authorization URL generated")
    
    # Step 2: Start callback server
    print("\n📡 Step 2: Starting OAuth2 callback server...")
    callback_server = HTTPServer(('localhost', 8080), OAuth2CallbackHandler)
    print("✅ Callback server started on http://localhost:8080")
    
    # Step 3: Open browser
    print("\n🌐 Step 3: Opening browser for authorization...")
    print(f"If the browser doesn't open automatically, visit:")
    print(f"{auth_url}")
    
    try:
        webbrowser.open(auth_url)
        print("✅ Browser opened")
    except:
        print("⚠️ Could not open browser automatically")
    
    # Step 4: Wait for callback
    print("\n⏳ Step 4: Waiting for authorization...")
    print("Please complete the OAuth flow in your browser...")
    
    # Handle one request (the callback)
    OAuth2CallbackHandler.auth_code = None
    callback_server.handle_request()
    callback_server.server_close()
    
    if not hasattr(OAuth2CallbackHandler, 'auth_code') or OAuth2CallbackHandler.auth_code is None:
        print("❌ No authorization code received")
        return False
    
    auth_code = OAuth2CallbackHandler.auth_code
    
    # Step 5: Exchange code for tokens
    print("\n🔄 Step 5: Exchanging authorization code for tokens...")
    token_result = await gmail_service.exchange_code_for_tokens(auth_code)
    
    if not token_result["success"]:
        print(f"❌ Token exchange failed: {token_result['message']}")
        return False
    
    refresh_token = token_result["refresh_token"]
    access_token = token_result["access_token"]
    
    print("✅ Tokens obtained successfully!")
    print(f"   Access Token: {access_token[:20]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")
    
    # Step 6: Update .env file
    print("\n📝 Step 6: Updating .env file...")
    
    env_file = "/home/ramsha/Documents/smart-invoice-scheduler/server/.env"
    
    try:
        # Read current .env
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        # Add or update refresh token
        if "GOOGLE_REFRESH_TOKEN=" in env_content:
            # Update existing
            import re
            env_content = re.sub(
                r'GOOGLE_REFRESH_TOKEN=.*',
                f'GOOGLE_REFRESH_TOKEN="{refresh_token}"',
                env_content
            )
        else:
            # Add new line
            env_content += f'\nGOOGLE_REFRESH_TOKEN="{refresh_token}"\n'
        
        # Write back to .env
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Updated {env_file} with refresh token")
        
    except Exception as e:
        print(f"⚠️ Could not update .env file automatically: {e}")
        print(f"Please manually add this line to your .env file:")
        print(f'GOOGLE_REFRESH_TOKEN="{refresh_token}"')
    
    # Step 7: Test Gmail connection
    print("\n🧪 Step 7: Testing Gmail connection...")
    
    # Reinitialize service to pick up new token
    gmail_service = get_gmail_mcp_service()
    test_result = await gmail_service.test_gmail_connection()
    
    if test_result["success"]:
        print("✅ Gmail connection successful!")
        print(f"   Email Address: {test_result.get('email_address', 'N/A')}")
        print(f"   Messages Total: {test_result.get('messages_total', 'N/A')}")
    else:
        print(f"❌ Gmail connection test failed: {test_result['message']}")
        return False
    
    # Success summary
    print("\n🎉 OAuth2 Setup Complete!")
    print("=" * 50)
    print("✅ Authorization successful")
    print("✅ Tokens obtained and saved")
    print("✅ Gmail connection verified")
    print("\nYou can now send emails through the Invoice Scheduler!")
    
    return True

async def quick_test_email():
    """Send a quick test email to verify everything works"""
    
    print("\n📧 Quick Email Test")
    print("=" * 30)
    
    gmail_service = get_gmail_mcp_service()
    
    # Ask for test email
    test_email = input("Enter your email address to send a test: ").strip()
    
    if not test_email:
        print("No email provided, skipping test")
        return
    
    # Send test email
    from services.gmail_mcp_service import EmailMessage
    
    test_message = EmailMessage(
        to=test_email,
        subject="🎉 Invoice Scheduler OAuth2 Setup Complete!",
        body_html="""
        <h2>🎉 Success!</h2>
        <p>Your Invoice Scheduler Agent is now configured for Gmail access.</p>
        <ul>
            <li>✅ OAuth2 authentication working</li>
            <li>✅ Gmail API access granted</li>
            <li>✅ Email sending functional</li>
        </ul>
        <p>You can now use the Invoice Scheduler to send automated invoices!</p>
        <br>
        <p><em>Sent from Invoice Scheduler Agent 🤖</em></p>
        """,
        body_text="""
        Success!
        
        Your Invoice Scheduler Agent is now configured for Gmail access.
        
        - OAuth2 authentication working
        - Gmail API access granted  
        - Email sending functional
        
        You can now use the Invoice Scheduler to send automated invoices!
        
        Sent from Invoice Scheduler Agent 🤖
        """
    )
    
    print(f"📤 Sending test email to {test_email}...")
    
    send_result = await gmail_service.send_email(test_message)
    
    if send_result["success"]:
        print("✅ Test email sent successfully!")
        print("Check your inbox to confirm email delivery.")
    else:
        print(f"❌ Test email failed: {send_result['message']}")

if __name__ == "__main__":
    print("🚀 Starting Gmail OAuth2 Setup...")
    
    try:
        # Run OAuth2 setup
        success = asyncio.run(setup_gmail_oauth())
        
        if success:
            # Optional test email
            send_test = input("\nWould you like to send a test email? (y/n): ").strip().lower()
            if send_test in ['y', 'yes']:
                asyncio.run(quick_test_email())
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()