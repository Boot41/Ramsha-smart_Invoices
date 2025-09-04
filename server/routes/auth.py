from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import Dict, Any
from schemas.auth_schemas import (
    UserRegistrationRequest, UserRegistrationResponse, UserLoginRequest, UserLoginResponse,
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse,
    UpdateProfileRequest, UserProfileResponse, EmailVerificationRequest, VerificationResponse
)
from controller.auth_controller import get_auth_controller
from middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    registration: UserRegistrationRequest,
    request: Request
) -> UserRegistrationResponse:
    """Register a new user"""
    auth_controller = get_auth_controller()
    return await auth_controller.register_user(registration, request)

@router.post("/login", response_model=UserLoginResponse)
async def login(
    login_request: UserLoginRequest,
    request: Request
) -> UserLoginResponse:
    """Login user and return access token"""
    auth_controller = get_auth_controller()
    return await auth_controller.login_user(login_request, request)

@router.post("/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Logout current user"""
    auth_controller = get_auth_controller()
    return await auth_controller.logout_user(current_user, request)

@router.post("/change-password")
async def change_password(
    change_request: ChangePasswordRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Change password for authenticated user"""
    auth_controller = get_auth_controller()
    return await auth_controller.change_password(change_request, current_user, request)

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    forgot_request: ForgotPasswordRequest,
    request: Request
) -> PasswordResetResponse:
    """Request password reset"""
    auth_controller = get_auth_controller()
    return await auth_controller.forgot_password(forgot_request, request)

@router.post("/reset-password")
async def reset_password(
    reset_request: ResetPasswordRequest,
    request: Request
) -> Dict[str, Any]:
    """Reset password with token"""
    auth_controller = get_auth_controller()
    return await auth_controller.reset_password(reset_request, request)

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserProfileResponse:
    """Get current user profile"""
    auth_controller = get_auth_controller()
    profile = await auth_controller.get_user_profile(current_user)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile

@router.put("/profile")
async def update_profile(
    update_request: UpdateProfileRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update current user profile"""
    auth_controller = get_auth_controller()
    success, message, updated_profile = await auth_controller.update_user_profile(
        update_request, current_user, request
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message,
        "profile": updated_profile
    }

@router.post("/verify-email", response_model=VerificationResponse)
async def verify_email(
    verification_request: EmailVerificationRequest
) -> VerificationResponse:
    """Verify email address"""
    auth_controller = get_auth_controller()
    return await auth_controller.verify_email(verification_request)

@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current authenticated user information"""
    return {
        "user": current_user,
        "authenticated": True,
        "permissions": current_user.get("permissions", {})
    }

@router.get("/google-drive")
async def google_drive_auth(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Initiate Google Drive OAuth flow"""
    import json
    import os
    import logging
    from urllib.parse import urlencode
    import secrets
    
    logger = logging.getLogger(__name__)
    
    try:
        # Path to OAuth credentials
        oauth_keys_path = '/home/ramsha/Documents/smart-invoice-scheduler/mcp/gdrive_mcp/gdrive-mcp-server/credentials/gcp-oauth.keys.json'
        
        if not os.path.exists(oauth_keys_path):
            raise HTTPException(
                status_code=500,
                detail="OAuth credentials not found. Please configure Google Drive API credentials."
            )
        
        # Read OAuth keys
        with open(oauth_keys_path) as f:
            oauth_keys = json.load(f)
        
        # Get client credentials
        if 'installed' in oauth_keys:
            client_id = oauth_keys['installed']['client_id']
            redirect_uri = oauth_keys['installed']['redirect_uris'][0]
        elif 'web' in oauth_keys:
            client_id = oauth_keys['web']['client_id']
            redirect_uri = oauth_keys['web']['redirect_uris'][0]
        else:
            raise ValueError('Could not find client credentials in OAuth keys')
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Store state in session or cache (for now, we'll skip this validation)
        
        # Google OAuth parameters
        auth_params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/drive.readonly',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        
        # Build Google OAuth URL
        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"
        
        logger.info(f"🔗 Generated Google OAuth URL: {auth_url}")
        
        # Return HTML page that redirects to Google OAuth
        from fastapi.responses import HTMLResponse
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirecting to Google Drive Authentication...</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .container {{ max-width: 500px; margin: 0 auto; }}
                .btn {{ background: #4285f4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px; }}
                .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Google Drive Authentication</h1>
                <p>You will be redirected to Google to authenticate your Google Drive access...</p>
                <div class="spinner"></div>
                <p><a href="{auth_url}" class="btn">Click here if not redirected automatically</a></p>
                <p><small>After authentication, you'll be able to sync your contracts from Google Drive.</small></p>
            </div>
            <script>
                // Auto-redirect after 2 seconds
                setTimeout(function() {{
                    window.location.href = "{auth_url}";
                }}, 2000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Error initiating Google OAuth: {str(e)}")
        
        # Return error page
        from fastapi.responses import HTMLResponse
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .container {{ max-width: 500px; margin: 0 auto; }}
                .error {{ color: #d32f2f; }}
                .btn {{ background: #2196f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">❌ Authentication Error</h1>
                <p>Failed to initiate Google Drive authentication: {str(e)}</p>
                <a href="/contracts" class="btn">← Back to Contracts</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=error_html, status_code=500)

@router.get("/google-drive/callback")
async def google_drive_callback(
    request: Request,
    code: str = None,
    error: str = None,
    state: str = None
):
    """Handle Google Drive OAuth callback"""
    import json
    import os
    import logging
    import requests
    import time
    from fastapi.responses import HTMLResponse
    
    logger = logging.getLogger(__name__)
    
    if error:
        logger.error(f"❌ OAuth error: {error}")
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Failed</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .container {{ max-width: 500px; margin: 0 auto; }}
                .error {{ color: #d32f2f; }}
                .btn {{ background: #2196f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">❌ Authentication Failed</h1>
                <p>Google Drive authentication failed: {error}</p>
                <a href="/contracts" class="btn">← Back to Contracts</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=400)
    
    if not code:
        logger.error("❌ No authorization code received")
        return HTMLResponse(content="No authorization code received", status_code=400)
    
    try:
        # Path to OAuth credentials
        oauth_keys_path = '/home/ramsha/Documents/smart-invoice-scheduler/mcp/gdrive_mcp/gdrive-mcp-server/credentials/gcp-oauth.keys.json'
        credentials_path = '/home/ramsha/Documents/smart-invoice-scheduler/mcp/gdrive_mcp/gdrive-mcp-server/credentials/.gdrive-server-credentials.json'
        
        # Read OAuth keys
        with open(oauth_keys_path) as f:
            oauth_keys = json.load(f)
        
        # Get client credentials
        if 'installed' in oauth_keys:
            client_id = oauth_keys['installed']['client_id']
            client_secret = oauth_keys['installed']['client_secret']
            redirect_uri = oauth_keys['installed']['redirect_uris'][0]
        elif 'web' in oauth_keys:
            client_id = oauth_keys['web']['client_id']
            client_secret = oauth_keys['web']['client_secret']
            redirect_uri = oauth_keys['web']['redirect_uris'][0]
        else:
            raise ValueError('Could not find client credentials in OAuth keys')
        
        # Exchange authorization code for tokens
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        logger.info("🔄 Exchanging authorization code for tokens...")
        
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        
        if response.status_code == 200:
            tokens = response.json()
            
            # Create credentials object
            credentials = {
                'access_token': tokens['access_token'],
                'refresh_token': tokens.get('refresh_token'),
                'expiry_date': int((time.time() + tokens['expires_in']) * 1000),
                'client_id': client_id,
                'client_secret': client_secret,
                'type': 'authorized_user'
            }
            
            # Save credentials
            os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
            with open(credentials_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            logger.info("✅ Google Drive authentication successful!")
            
            success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Successful</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .container { max-width: 500px; margin: 0 auto; }
                    .success { color: #388e3c; }
                    .btn { background: #4caf50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">✅ Authentication Successful!</h1>
                    <p>Google Drive has been successfully authenticated. You can now sync your contracts!</p>
                    <a href="/contracts" class="btn">← Back to Contracts</a>
                </div>
                <script>
                    // Auto-redirect after 3 seconds
                    setTimeout(function() {
                        window.location.href = "/contracts";
                    }, 3000);
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=success_html)
            
        else:
            logger.error(f"❌ Token exchange failed: {response.status_code} - {response.text}")
            raise Exception(f"Token exchange failed: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ OAuth callback error: {str(e)}")
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .container {{ max-width: 500px; margin: 0 auto; }}
                .error {{ color: #d32f2f; }}
                .btn {{ background: #2196f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">❌ Authentication Error</h1>
                <p>Failed to complete Google Drive authentication: {str(e)}</p>
                <a href="/contracts" class="btn">← Back to Contracts</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=error_html, status_code=500)
