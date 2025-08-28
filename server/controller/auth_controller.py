from fastapi import Request
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from schemas.auth_schemas import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserLoginRequest, UserLoginResponse, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse,
    UpdateProfileRequest, UserProfileResponse, EmailVerificationRequest,
    VerificationResponse, AuthErrorResponse, AuthStatus
)
from services.user_service import get_user_service
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)


class AuthController:
    """Controller for handling authentication and user management operations"""
    
    def __init__(self):
        self.user_service = get_user_service()
        logger.info("✅ Auth Controller initialized")
    
    async def register_user(
        self, 
        registration: UserRegistrationRequest,
        request: Optional[Request] = None
    ) -> UserRegistrationResponse:
        """
        Handle user registration
        
        Args:
            registration: User registration data
            request: FastAPI request object for IP extraction
            
        Returns:
            UserRegistrationResponse with registration results
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            logger.info(f"📝 User registration request: {registration.email} from IP: {ip_address}")
            
            # Validate registration data
            validation_errors = self._validate_registration(registration)
            if validation_errors:
                return UserRegistrationResponse(
                    success=False,
                    message=f"Validation failed: {', '.join(validation_errors)}",
                    email=registration.email,
                    role=registration.role
                )
            
            # Register user through service
            success, message, user_data = await self.user_service.register_user(
                registration, ip_address
            )
            
            if success and user_data:
                logger.info(f"✅ User registration successful: {registration.email}")
                return UserRegistrationResponse(
                    success=True,
                    message=message,
                    user_id=user_data.get("user_id"),
                    email=registration.email,
                    role=registration.role,
                    verification_required=not user_data.get("email_verified", True),
                    verification_method="email" if not user_data.get("email_verified", True) else None,
                    access_token=user_data.get("access_token"),
                    token_type=user_data.get("token_type", "bearer"),
                    expires_in=user_data.get("expires_in"),
                    user=user_data.get("user"),
                    permissions=user_data.get("permissions")
                )
            else:
                logger.error(f"❌ User registration failed: {message}")
                return UserRegistrationResponse(
                    success=False,
                    message=message,
                    email=registration.email,
                    role=registration.role
                )
                
        except Exception as e:
            logger.error(f"❌ Registration controller error: {str(e)}")
            return UserRegistrationResponse(
                success=False,
                message=f"Registration failed: {str(e)}",
                email=registration.email,
                role=registration.role
            )
    
    async def login_user(
        self, 
        login_request: UserLoginRequest,
        request: Optional[Request] = None
    ) -> UserLoginResponse:
        """
        Handle user login
        
        Args:
            login_request: User login credentials
            request: FastAPI request object for IP and user agent extraction
            
        Returns:
            UserLoginResponse with login results
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            user_agent = self._get_user_agent(request) if request else None
            
            logger.info(f"🔐 Login request: {login_request.email} from IP: {ip_address}")
            
            # Authenticate user through service
            success, message, login_data = await self.user_service.login_user(
                login_request, ip_address, user_agent
            )
            
            if success and login_data:
                logger.info(f"✅ Login successful: {login_request.email}")
                return UserLoginResponse(
                    success=True,
                    message=message,
                    access_token=login_data.get("access_token"),
                    token_type=login_data.get("token_type", "bearer"),
                    expires_in=login_data.get("expires_in"),
                    user=login_data.get("user"),
                    permissions=login_data.get("permissions")
                )
            else:
                logger.error(f"❌ Login failed: {message}")
                return UserLoginResponse(
                    success=False,
                    message=message
                )
                
        except Exception as e:
            logger.error(f"❌ Login controller error: {str(e)}")
            return UserLoginResponse(
                success=False,
                message=f"Login failed: {str(e)}"
            )
    
    async def change_password(
        self, 
        change_request: ChangePasswordRequest,
        current_user: Dict[str, Any],
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Handle password change
        
        Args:
            change_request: Password change data
            current_user: Authenticated user information
            request: FastAPI request object
            
        Returns:
            Dictionary with change results
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            user_id = current_user.get("user_id")
            
            logger.info(f"🔒 Password change request: {current_user.get('email')} from IP: {ip_address}")
            
            # Change password through service
            success, message = await self.user_service.change_password(
                user_id, change_request, ip_address
            )
            
            if success:
                logger.info(f"✅ Password changed successfully: {current_user.get('email')}")
            else:
                logger.error(f"❌ Password change failed: {message}")
            
            return {
                "success": success,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"❌ Password change controller error: {str(e)}")
            return {
                "success": False,
                "message": f"Password change failed: {str(e)}"
            }
    
    async def forgot_password(
        self, 
        forgot_request: ForgotPasswordRequest,
        request: Optional[Request] = None
    ) -> PasswordResetResponse:
        """
        Handle forgot password request
        
        Args:
            forgot_request: Forgot password data
            request: FastAPI request object
            
        Returns:
            PasswordResetResponse with reset token info
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            
            logger.info(f"📧 Forgot password request: {forgot_request.email} from IP: {ip_address}")
            
            # Process forgot password through service
            success, message, reset_token = await self.user_service.forgot_password(
                forgot_request, ip_address
            )
            
            if success:
                logger.info(f"✅ Password reset initiated: {forgot_request.email}")
            
            return PasswordResetResponse(
                success=success,
                message=message,
                reset_token=reset_token  # In production, don't return token, send via email
            )
            
        except Exception as e:
            logger.error(f"❌ Forgot password controller error: {str(e)}")
            return PasswordResetResponse(
                success=False,
                message=f"Forgot password failed: {str(e)}"
            )
    
    async def reset_password(
        self, 
        reset_request: ResetPasswordRequest,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Handle password reset with token
        
        Args:
            reset_request: Password reset data
            request: FastAPI request object
            
        Returns:
            Dictionary with reset results
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            
            logger.info(f"🔑 Password reset request from IP: {ip_address}")
            
            # Reset password through service
            success, message = await self.user_service.reset_password(
                reset_request, ip_address
            )
            
            if success:
                logger.info(f"✅ Password reset successful")
            else:
                logger.error(f"❌ Password reset failed: {message}")
            
            return {
                "success": success,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"❌ Password reset controller error: {str(e)}")
            return {
                "success": False,
                "message": f"Password reset failed: {str(e)}"
            }
    
    async def get_user_profile(
        self, 
        current_user: Dict[str, Any]
    ) -> Optional[UserProfileResponse]:
        """
        Get user profile information
        
        Args:
            current_user: Authenticated user information
            
        Returns:
            UserProfileResponse or None if not found
        """
        try:
            user_id = current_user.get("user_id")
            
            logger.info(f"👤 Profile request: {current_user.get('email')}")
            
            # Get profile through service
            profile_data = await self.user_service.get_user_profile(user_id)
            
            if profile_data:
                return UserProfileResponse(**profile_data)
            else:
                logger.error(f"❌ Profile not found for user: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Get profile controller error: {str(e)}")
            return None
    
    async def update_user_profile(
        self, 
        update_request: UpdateProfileRequest,
        current_user: Dict[str, Any],
        request: Optional[Request] = None
    ) -> Tuple[bool, str, Optional[UserProfileResponse]]:
        """
        Update user profile
        
        Args:
            update_request: Profile update data
            current_user: Authenticated user information
            request: FastAPI request object
            
        Returns:
            Tuple of (success, message, updated_profile)
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            user_id = current_user.get("user_id")
            
            logger.info(f"📝 Profile update request: {current_user.get('email')} from IP: {ip_address}")
            
            # Update profile through service
            success, message, updated_profile_data = await self.user_service.update_user_profile(
                user_id, update_request, ip_address
            )
            
            updated_profile = None
            if success and updated_profile_data:
                updated_profile = UserProfileResponse(**updated_profile_data)
                logger.info(f"✅ Profile updated successfully: {current_user.get('email')}")
            else:
                logger.error(f"❌ Profile update failed: {message}")
            
            return success, message, updated_profile
            
        except Exception as e:
            logger.error(f"❌ Update profile controller error: {str(e)}")
            return False, f"Profile update failed: {str(e)}", None
    
    async def verify_email(
        self, 
        verification_request: EmailVerificationRequest
    ) -> VerificationResponse:
        """
        Handle email verification
        
        Args:
            verification_request: Email verification data
            
        Returns:
            VerificationResponse with verification results
        """
        try:
            logger.info(f"📧 Email verification request")
            
            # Verify email through service
            success, message = await self.user_service.verify_email(
                verification_request.token
            )
            
            if success:
                logger.info(f"✅ Email verification successful")
            else:
                logger.error(f"❌ Email verification failed: {message}")
            
            return VerificationResponse(
                success=success,
                message=message
            )
            
        except Exception as e:
            logger.error(f"❌ Email verification controller error: {str(e)}")
            return VerificationResponse(
                success=False,
                message=f"Email verification failed: {str(e)}"
            )
    
    async def logout_user(
        self, 
        current_user: Dict[str, Any],
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Handle user logout (token invalidation would be handled by auth middleware)
        
        Args:
            current_user: Authenticated user information
            request: FastAPI request object
            
        Returns:
            Dictionary with logout results
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            
            logger.info(f"👋 Logout request: {current_user.get('email')} from IP: {ip_address}")
            
            # In production, implement token blacklisting here
            # For now, just log the logout
            
            logger.info(f"✅ User logged out: {current_user.get('email')}")
            
            return {
                "success": True,
                "message": "Logged out successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Logout controller error: {str(e)}")
            return {
                "success": False,
                "message": f"Logout failed: {str(e)}"
            }
    
    def _validate_registration(self, registration: UserRegistrationRequest) -> list[str]:
        """Validate registration data"""
        errors = []
        
        # Password strength validation
        password = registration.password
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        # Email format validation (additional to Pydantic)
        email = registration.email.lower()
        if len(email) > 254:
            errors.append("Email address is too long")
        
        # Name validation
        if len(registration.name.strip()) < 2:
            errors.append("Name must be at least 2 characters long")
        
        return errors
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request"""
        try:
            # Check for forwarded IP first (for load balancers/proxies)
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            
            # Check for real IP
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip
            
            # Fall back to client host
            if request.client:
                return request.client.host
            
            return None
        except Exception:
            return None
    
    def _get_user_agent(self, request: Request) -> Optional[str]:
        """Extract user agent from request"""
        try:
            return request.headers.get("User-Agent")
        except Exception:
            return None
    
    def generate_error_response(
        self, 
        error_message: str, 
        error_code: str = "AUTH_ERROR"
    ) -> AuthErrorResponse:
        """Generate standardized error response"""
        return AuthErrorResponse(
            error=error_message,
            error_code=error_code,
            timestamp=datetime.now()
        )


# Global controller instance
_auth_controller = None

def get_auth_controller() -> AuthController:
    """Get singleton auth controller instance"""
    global _auth_controller
    if _auth_controller is None:
        _auth_controller = AuthController()
    return _auth_controller