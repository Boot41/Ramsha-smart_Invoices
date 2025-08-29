from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone
import logging
import secrets
import uuid

from models.database_models import User, UserRole, UserStatus
from schemas.auth_schemas import (
    UserRegistrationRequest, UserLoginRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest, UpdateProfileRequest,
    AuthStatus, SecurityEventType
)
from schemas.address_schemas import AddressCreate
from services.database_service import get_database_service
from middleware.auth import TokenHelper

logger = logging.getLogger(__name__)


class UserServiceDB:
    """Database-backed user service for authentication and user management"""
    
    def __init__(self):
        self.db_service = get_database_service()
        logger.info("✅ Database User Service initialized")
    
    # User Registration
    async def register_user(
        self, 
        registration: UserRegistrationRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register a new user with database persistence
        """
        try:
            logger.info(f"🔐 User registration attempt: {registration.email}")
            
            # Validate tenant email for rent payers
            if registration.role.value == "rent_payer":
                if not registration.tenant_email:
                    return False, "Tenant email is required for rent payers", None
                
                # Check if tenant exists
                tenant = await self.db_service.get_user_by_email(registration.tenant_email)
                if not tenant or tenant.role != UserRole.TENANT:
                    return False, "Invalid or non-existent tenant email", None
            
            # Create user in database
            success, message, user = await self.db_service.create_user(
                registration, 
                registration.address if hasattr(registration, 'address') and registration.address else None
            )
            
            if not success or not user:
                # Log security event
                await self.db_service.log_security_event(
                    event_type=SecurityEventType.LOGIN_FAILURE.value,
                    email=registration.email,
                    ip_address=ip_address,
                    metadata={"reason": "registration_failed", "message": message}
                )
                return False, message, None
            
            # Log successful registration
            await self.db_service.log_security_event(
                event_type=SecurityEventType.LOGIN_SUCCESS.value,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                metadata={"action": "user_registration", "role": user.role.value}
            )
            
            logger.info(f"✅ User registered successfully: {user.email} ({user.role.value})")
            
            # Generate JWT token for immediate login
            access_token = TokenHelper.create_user_token(
                email=user.email,
                role=user.role.value,
                user_id=user.id,
                name=user.name
            )
            
            # Return user data with token
            user_data = {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "status": user.status.value,
                "email_verified": user.email_verified,
                "verification_token": user.email_verification_token if not user.email_verified else None,
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
        Authenticate user login with database persistence
        """
        try:
            logger.info(f"🔐 Login attempt: {login_request.email}")
            
            # Find user in database
            user = await self.db_service.get_user_by_email(login_request.email)
            if not user:
                await self.db_service.log_security_event(
                    event_type=SecurityEventType.LOGIN_FAILURE.value,
                    email=login_request.email,
                    ip_address=ip_address,
                    metadata={"reason": "user_not_found"}
                )
                return False, "Invalid email or password", None
            
            # Check if user can login
            can_login, reason = user.can_login()
            if not can_login:
                await self.db_service.log_security_event(
                    event_type=SecurityEventType.LOGIN_FAILURE.value,
                    user_id=user.id,
                    email=user.email,
                    ip_address=ip_address,
                    metadata={"reason": reason}
                )
                return False, reason, None
            
            # Verify password
            if not user.verify_password(login_request.password):
                # Record failed login attempt
                await self.db_service.record_login_attempt(user.id, False, ip_address)
                
                await self.db_service.log_security_event(
                    event_type=SecurityEventType.LOGIN_FAILURE.value,
                    user_id=user.id,
                    email=user.email,
                    ip_address=ip_address,
                    metadata={"reason": "invalid_password"}
                )
                return False, "Invalid email or password", None
            
            # Successful login - record in database
            await self.db_service.record_login_attempt(user.id, True, ip_address)
            
            # Generate JWT token
            token_expires = timedelta(hours=24 if login_request.remember_me else 1)
            access_token = TokenHelper.create_user_token(
                email=user.email,
                role=user.role.value,
                user_id=user.id,
                name=user.name
            )
            
            # Log security event
            await self.db_service.log_security_event(
                event_type=SecurityEventType.LOGIN_SUCCESS.value,
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
        Change user password with database persistence
        """
        try:
            logger.info(f"🔐 Password change request: {user_id}")
            
            user = await self.db_service.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not user.verify_password(change_request.current_password):
                await self.db_service.log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY.value,
                    user_id=user.id,
                    email=user.email,
                    ip_address=ip_address,
                    metadata={"action": "invalid_current_password_change"}
                )
                return False, "Current password is incorrect"
            
            # Update password in database
            success, message = await self.db_service.update_user_password(user_id, change_request.new_password)
            if not success:
                return False, message
            
            # Log security event
            await self.db_service.log_security_event(
                event_type=SecurityEventType.PASSWORD_CHANGE.value,
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
        Initiate password reset process with database persistence
        """
        try:
            logger.info(f"🔐 Password reset request: {forgot_request.email}")
            
            user = await self.db_service.get_user_by_email(forgot_request.email)
            if not user:
                # Don't reveal if email exists
                return True, "Password reset email sent if account exists", None
            
            # Generate reset token and update user
            reset_token = user.generate_password_reset_token()
            success, message, updated_user = await self.db_service.update_user(
                user.id,
                password_reset_token=user.password_reset_token,
                password_reset_expires=user.password_reset_expires
            )
            
            if not success:
                return False, "Failed to generate reset token", None
            
            # Log security event
            await self.db_service.log_security_event(
                event_type=SecurityEventType.PASSWORD_RESET.value,
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
        Reset password with token using database persistence
        """
        try:
            logger.info(f"🔐 Password reset with token")
            
            # Find user with this reset token (simplified - in production use proper query)
            # For now, we'll need to implement a method in database service to find by token
            # This is a simplified approach
            users, _ = await self.db_service.list_users(limit=1000)  # Get all users to search
            user = None
            for u in users:
                if u.password_reset_token == reset_request.token:
                    user = u
                    break
            
            if not user:
                return False, "Invalid or expired reset token"
            
            # Verify and reset password
            if user.reset_password_with_token(reset_request.token, reset_request.new_password):
                # Update user in database
                success, message, updated_user = await self.db_service.update_user(
                    user.id,
                    password_hash=user.password_hash,
                    password_reset_token=user.password_reset_token,
                    password_reset_expires=user.password_reset_expires,
                    failed_login_attempts=user.failed_login_attempts,
                    last_failed_login=user.last_failed_login,
                    lockout_until=user.lockout_until
                )
                
                if not success:
                    return False, "Failed to reset password"
                
                # Log security event
                await self.db_service.log_security_event(
                    event_type=SecurityEventType.PASSWORD_RESET.value,
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
        """Get user profile information from database"""
        try:
            user = await self.db_service.get_user_by_id(user_id)
            if not user:
                return None
            
            # Get address information if available
            address_data = None
            if user.address_id:
                address = await self.db_service.get_address_by_id(user.address_id)
                if address:
                    address_data = {
                        "id": address.id,
                        "street": address.street,
                        "building_number": address.building_number,
                        "room_number": address.room_number,
                        "floor": address.floor,
                        "apartment_unit": address.apartment_unit,
                        "city": address.city,
                        "state": address.state,
                        "postal_code": address.postal_code,
                        "country": address.country,
                        "landmark": address.landmark,
                        "neighborhood": address.neighborhood,
                        "created_at": address.created_at.isoformat() if address.created_at else None,
                        "updated_at": address.updated_at.isoformat() if address.updated_at else None
                    }
            
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
                "address": address_data
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
        Update user profile with database persistence
        """
        try:
            logger.info(f"👤 Profile update request: {user_id}")
            
            user = await self.db_service.get_user_by_id(user_id)
            if not user:
                return False, "User not found", None
            
            # Update profile fields
            update_data = {}
            if update_request.name is not None:
                update_data["name"] = update_request.name.strip()
            if update_request.phone is not None:
                update_data["phone"] = update_request.phone
            
            success, message, updated_user = await self.db_service.update_user(user_id, **update_data)
            if not success:
                return False, message, None
            
            # TODO: Handle address update if provided
            
            # Log security event
            await self.db_service.log_security_event(
                event_type=SecurityEventType.PROFILE_UPDATE.value,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                metadata={"fields_updated": list(update_data.keys())}
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
        """Verify email with token using database persistence"""
        try:
            # Find user with this verification token (simplified approach)
            users, _ = await self.db_service.list_users(limit=1000)  # Get all users to search
            user = None
            for u in users:
                if u.email_verification_token == token:
                    user = u
                    break
            
            if not user:
                return False, "Invalid or expired verification token"
            
            if user.verify_email_token(token):
                # Update user in database
                success, message, updated_user = await self.db_service.update_user(
                    user.id,
                    email_verified=user.email_verified,
                    email_verification_token=user.email_verification_token,
                    email_verification_expires=user.email_verification_expires
                )
                
                if success:
                    logger.info(f"✅ Email verified successfully: {user.email}")
                    return True, "Email verified successfully"
                else:
                    return False, "Failed to update verification status"
            else:
                return False, "Invalid or expired verification token"
                
        except Exception as e:
            logger.error(f"❌ Email verification failed: {str(e)}")
            return False, f"Email verification failed: {str(e)}"
    
    # Utility Methods
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from database"""
        return await self.db_service.get_user_by_email(email)
    
    async def list_users(
        self, 
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List users with filtering and pagination"""
        try:
            users, total = await self.db_service.list_users(role, status, limit, offset)
            
            # Convert to response format
            user_list = []
            for user in users:
                profile = await self.get_user_profile(user.id)
                if profile:
                    user_list.append(profile)
            
            return user_list, total
            
        except Exception as e:
            logger.error(f"❌ Failed to list users: {str(e)}")
            return [], 0


# Global service instance
_user_service_db = None

def get_user_service() -> UserServiceDB:
    """Get singleton database user service instance"""
    global _user_service_db
    if _user_service_db is None:
        _user_service_db = UserServiceDB()
    return _user_service_db