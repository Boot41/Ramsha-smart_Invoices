from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone
import logging
import secrets
import uuid

from models.user import UserModel
from models.document import DocumentModel
from schemas.auth_schemas import (
    UserRegistrationRequest, UserLoginRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest, UpdateProfileRequest,
    AuthStatus, SecurityEvent, SecurityEventType
)
from schemas.user_schemas import UserRole
from middleware.auth import TokenHelper
from services.gcp_storage_service import get_gcp_storage_service

logger = logging.getLogger(__name__)

class UserService:
    """Service layer for user management and authentication operations"""
    
    def __init__(self):
        self.storage_service = get_gcp_storage_service()
        # In-memory storage for demo (replace with actual database)
        self.users: Dict[str, UserModel] = {}
        self.users_by_email: Dict[str, str] = {}  # email -> user_id mapping
        self.security_events: List[SecurityEvent] = []
        
        logger.info("✅ User Service initialized")
    
    # User Registration
    async def register_user(
        self, 
        registration: UserRegistrationRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register a new user
        
        Args:
            registration: User registration data
            ip_address: Client IP address for security logging
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            logger.info(f"🔐 User registration attempt: {registration.email}")
            
            # Check if user already exists
            if registration.email.lower() in self.users_by_email:
                self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    email=registration.email,
                    ip_address=ip_address,
                    metadata={"reason": "email_already_exists"}
                )
                return False, "User with this email already exists", None
            
            # Validate tenant email for rent payers
            if registration.role == UserRole.RENT_PAYER:
                if not registration.tenant_email or registration.tenant_email.lower() not in self.users_by_email:
                    return False, "Invalid or non-existent tenant email", None
                
                # Check if tenant exists and is actually a tenant
                tenant_id = self.users_by_email[registration.tenant_email.lower()]
                tenant = self.users.get(tenant_id)
                if not tenant or tenant.role != UserRole.TENANT:
                    return False, "Associated tenant not found", None
            
            # Create new user
            user = UserModel(
                email=registration.email,
                name=registration.name,
                phone=registration.phone,
                role=registration.role,
                status=AuthStatus.ACTIVE,  # or PENDING_VERIFICATION if email verification required
                tenant_email=registration.tenant_email,
                email_verified=False,  # Set to True for demo, False for production
                metadata={"registration_ip": ip_address}
            )
            
            # Set password
            user.set_password(registration.password)
            
            # Generate email verification token
            verification_token = user.generate_email_verification_token()
            
            # Store user
            self.users[user.id] = user
            self.users_by_email[user.email.lower()] = user.id
            
            # Note: User data will be stored in PostgreSQL database
            # No need to create user folders in GCP Storage bucket
            
            # Log security event
            self._log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                metadata={"action": "user_registration", "role": user.role.value}
            )
            
            logger.info(f"✅ User registered successfully: {user.email} ({user.role.value})")
            
            # Generate JWT token for immediate login
            from datetime import timedelta
            access_token = TokenHelper.create_user_token(
                email=user.email,
                role=user.role.value,
                user_id=user.id,
                name=user.name
            )
            
            # Return user data with token (for immediate login after registration)
            user_data = {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "status": user.status.value,
                "email_verified": user.email_verified,
                "verification_token": verification_token if not user.email_verified else None,
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 3600,  # 1 hour in seconds
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role.value,
                    "status": user.status.value,
                    "email_verified": user.email_verified,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                "permissions": user.get_permissions()
            }
            
            return True, "User registered successfully", user_data
            
        except Exception as e:
            logger.error(f"❌ User registration failed: {str(e)}")
            return False, f"Registration failed: {str(e)}", None
    
    # User Login
    async def login_user(
        self, 
        login_request: UserLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate user login
        
        Args:
            login_request: Login credentials
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (success, message, login_data)
        """
        try:
            logger.info(f"🔐 Login attempt: {login_request.email}")
            
            # Find user
            user_id = self.users_by_email.get(login_request.email.lower())
            if not user_id:
                self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    email=login_request.email,
                    ip_address=ip_address,
                    metadata={"reason": "user_not_found"}
                )
                return False, "Invalid email or password", None
            
            user = self.users[user_id]
            
            # Check if user can login
            can_login, reason = user.can_login()
            if not can_login:
                self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=user.id,
                    email=user.email,
                    ip_address=ip_address,
                    metadata={"reason": reason}
                )
                return False, reason, None
            
            # Verify password
            if not user.verify_password(login_request.password):
                user.record_login_attempt(False, ip_address)
                self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=user.id,
                    email=user.email,
                    ip_address=ip_address,
                    metadata={"reason": "invalid_password"}
                )
                return False, "Invalid email or password", None
            
            # Successful login
            user.record_login_attempt(True, ip_address)
            
            # Generate JWT token
            token_expires = timedelta(hours=24 if login_request.remember_me else 1)
            access_token = TokenHelper.create_user_token(
                email=user.email,
                role=user.role.value,
                user_id=user.id,
                name=user.name
            )
            
            # Log security event
            self._log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"remember_me": login_request.remember_me}
            )
            
            logger.info(f"✅ User logged in successfully: {user.email}")
            
            # Return login data
            login_data = {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": int(token_expires.total_seconds()),
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role.value,
                    "status": user.status.value,
                    "email_verified": user.email_verified,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "permissions": user.get_permissions()
            }
            
            return True, "Login successful", login_data
            
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            return False, f"Login failed: {str(e)}", None
    
    # Password Management
    async def change_password(
        self, 
        user_id: str, 
        change_request: ChangePasswordRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Change user password
        
        Args:
            user_id: User identifier
            change_request: Password change data
            ip_address: Client IP address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"🔐 Password change request: {user_id}")
            
            user = self.users.get(user_id)
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not user.verify_password(change_request.current_password):
                self._log_security_event(
                    SecurityEventType.SUSPICIOUS_ACTIVITY,
                    user_id=user.id,
                    email=user.email,
                    ip_address=ip_address,
                    metadata={"action": "invalid_current_password_change"}
                )
                return False, "Current password is incorrect"
            
            # Set new password
            user.set_password(change_request.new_password)
            
            # Log security event
            self._log_security_event(
                SecurityEventType.PASSWORD_CHANGE,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address
            )
            
            logger.info(f"✅ Password changed successfully: {user.email}")
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"❌ Password change failed: {str(e)}")
            return False, f"Password change failed: {str(e)}"
    
    async def forgot_password(
        self, 
        forgot_request: ForgotPasswordRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Initiate password reset process
        
        Args:
            forgot_request: Forgot password request
            ip_address: Client IP address
            
        Returns:
            Tuple of (success, message, reset_token)
        """
        try:
            logger.info(f"🔐 Password reset request: {forgot_request.email}")
            
            user_id = self.users_by_email.get(forgot_request.email.lower())
            if not user_id:
                # Don't reveal if email exists
                return True, "Password reset email sent if account exists", None
            
            user = self.users[user_id]
            
            # Generate reset token
            reset_token = user.generate_password_reset_token()
            
            # Log security event
            self._log_security_event(
                SecurityEventType.PASSWORD_RESET,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                metadata={"action": "reset_token_generated"}
            )
            
            logger.info(f"✅ Password reset token generated: {user.email}")
            
            # In production, send email with reset token
            # For demo, return the token
            return True, "Password reset email sent", reset_token
            
        except Exception as e:
            logger.error(f"❌ Password reset failed: {str(e)}")
            return False, f"Password reset failed: {str(e)}", None
    
    async def reset_password(
        self, 
        reset_request: ResetPasswordRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Reset password with token
        
        Args:
            reset_request: Password reset data
            ip_address: Client IP address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"🔐 Password reset with token")
            
            # Find user with this reset token
            user = None
            for u in self.users.values():
                if u.password_reset_token == reset_request.token:
                    user = u
                    break
            
            if not user:
                return False, "Invalid or expired reset token"
            
            # Reset password
            if user.reset_password_with_token(reset_request.token, reset_request.new_password):
                # Log security event
                self._log_security_event(
                    SecurityEventType.PASSWORD_RESET,
                    user_id=user.id,
                    email=user.email,
                    ip_address=ip_address,
                    metadata={"action": "password_reset_completed"}
                )
                
                logger.info(f"✅ Password reset completed: {user.email}")
                return True, "Password reset successfully"
            else:
                return False, "Invalid or expired reset token"
            
        except Exception as e:
            logger.error(f"❌ Password reset failed: {str(e)}")
            return False, f"Password reset failed: {str(e)}"
    
    # Profile Management
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        try:
            user = self.users.get(user_id)
            if not user:
                return None
            
            # Get address information if available
            # TODO: Implement address retrieval from database
            
            profile = {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "role": user.role.value,
                "status": user.status.value,
                "tenant_email": user.tenant_email,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "address": None  # TODO: Populate from database
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Failed to get user profile: {str(e)}")
            return None
    
    async def update_user_profile(
        self, 
        user_id: str, 
        update_request: UpdateProfileRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update user profile
        
        Args:
            user_id: User identifier
            update_request: Profile update data
            ip_address: Client IP address
            
        Returns:
            Tuple of (success, message, updated_profile)
        """
        try:
            logger.info(f"👤 Profile update request: {user_id}")
            
            user = self.users.get(user_id)
            if not user:
                return False, "User not found", None
            
            # Update profile fields
            user.update_profile(
                name=update_request.name,
                phone=update_request.phone
            )
            
            # TODO: Handle address update
            
            # Log security event
            self._log_security_event(
                SecurityEventType.PROFILE_UPDATE,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                metadata={"fields_updated": [k for k, v in update_request.dict().items() if v is not None]}
            )
            
            # Get updated profile
            updated_profile = await self.get_user_profile(user_id)
            
            logger.info(f"✅ Profile updated successfully: {user.email}")
            return True, "Profile updated successfully", updated_profile
            
        except Exception as e:
            logger.error(f"❌ Profile update failed: {str(e)}")
            return False, f"Profile update failed: {str(e)}", None
    
    # Email Verification
    async def verify_email(self, token: str) -> Tuple[bool, str]:
        """Verify email with token"""
        try:
            # Find user with this verification token
            user = None
            for u in self.users.values():
                if u.email_verification_token == token:
                    user = u
                    break
            
            if not user:
                return False, "Invalid or expired verification token"
            
            if user.verify_email_token(token):
                logger.info(f"✅ Email verified successfully: {user.email}")
                return True, "Email verified successfully"
            else:
                return False, "Invalid or expired verification token"
                
        except Exception as e:
            logger.error(f"❌ Email verification failed: {str(e)}")
            return False, f"Email verification failed: {str(e)}"
    
    # Utility Methods
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        user_id = self.users_by_email.get(email.lower())
        return self.users.get(user_id) if user_id else None
    
    
    def _log_security_event(
        self, 
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log security event"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        self.security_events.append(event)
        
        # Log to application logger
        logger.info(f"🔒 Security Event: {event_type.value} - User: {email or user_id} - IP: {ip_address}")
    
    # Admin/Management Methods
    async def list_users(
        self, 
        role: Optional[UserRole] = None,
        status: Optional[AuthStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List users with filtering and pagination"""
        try:
            all_users = list(self.users.values())
            
            # Apply filters
            filtered_users = []
            for user in all_users:
                if role and user.role != role:
                    continue
                if status and user.status != status:
                    continue
                filtered_users.append(user)
            
            # Apply pagination
            total = len(filtered_users)
            paginated_users = filtered_users[offset:offset + limit]
            
            # Convert to response format
            user_list = []
            for user in paginated_users:
                profile = await self.get_user_profile(user.id)
                if profile:
                    user_list.append(profile)
            
            return user_list, total
            
        except Exception as e:
            logger.error(f"❌ Failed to list users: {str(e)}")
            return [], 0


# Global service instance
_user_service = None

def get_user_service() -> UserService:
    """Get singleton user service instance"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service