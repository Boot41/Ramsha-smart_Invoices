from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import hashlib
import uuid
import secrets
from schemas.user_schemas import UserRole
from schemas.auth_schemas import AuthStatus
from models.document import DocumentModel


class UserModel:
    """User model for database operations and business logic"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        email: str = "",
        password_hash: str = "",
        name: str = "",
        phone: Optional[str] = None,
        role: UserRole = UserRole.RENT_PAYER,
        status: AuthStatus = AuthStatus.ACTIVE,
        address_id: Optional[str] = None,
        tenant_email: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        last_login: Optional[datetime] = None,
        email_verified: bool = False,
        phone_verified: bool = False,
        email_verification_token: Optional[str] = None,
        email_verification_expires: Optional[datetime] = None,
        password_reset_token: Optional[str] = None,
        password_reset_expires: Optional[datetime] = None,
        failed_login_attempts: int = 0,
        last_failed_login: Optional[datetime] = None,
        account_locked_until: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id or self._generate_id()
        self.email = email.lower().strip()
        self.password_hash = password_hash
        self.name = name.strip()
        self.phone = phone
        self.role = role
        self.status = status
        self.address_id = address_id
        self.tenant_email = tenant_email.lower().strip() if tenant_email else None
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at
        self.last_login = last_login
        self.email_verified = email_verified
        self.phone_verified = phone_verified
        self.email_verification_token = email_verification_token
        self.email_verification_expires = email_verification_expires
        self.password_reset_token = password_reset_token
        self.password_reset_expires = password_reset_expires
        self.failed_login_attempts = failed_login_attempts
        self.last_failed_login = last_failed_login
        self.account_locked_until = account_locked_until
        self.metadata = metadata or {}
    
    def _generate_id(self) -> str:
        """Generate unique user ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256 with salt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def set_password(self, password: str):
        """Set new password (hashed)"""
        self.password_hash = self.hash_password(password)
        self.updated_at = datetime.now(timezone.utc)
        # Clear any existing password reset tokens
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def generate_email_verification_token(self) -> str:
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = datetime.now(timezone.utc).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )  # Expires at end of day
        self.updated_at = datetime.now(timezone.utc)
        return self.email_verification_token
    
    def verify_email_token(self, token: str) -> bool:
        """Verify email verification token"""
        if not self.email_verification_token or not self.email_verification_expires:
            return False
        
        if datetime.now(timezone.utc) > self.email_verification_expires:
            return False
        
        if self.email_verification_token != token:
            return False
        
        # Mark email as verified
        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_expires = None
        self.updated_at = datetime.now(timezone.utc)
        return True
    
    def generate_password_reset_token(self) -> str:
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.now(timezone.utc).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )  # Expires at end of day
        self.updated_at = datetime.now(timezone.utc)
        return self.password_reset_token
    
    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if datetime.now(timezone.utc) > self.password_reset_expires:
            return False
        
        return self.password_reset_token == token
    
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using valid token"""
        if not self.verify_password_reset_token(token):
            return False
        
        self.set_password(new_password)
        # Clear reset tokens and failed attempts
        self.password_reset_token = None
        self.password_reset_expires = None
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        return True
    
    def record_login_attempt(self, success: bool, ip_address: Optional[str] = None):
        """Record login attempt"""
        if success:
            self.last_login = datetime.now(timezone.utc)
            self.failed_login_attempts = 0
            self.last_failed_login = None
            if self.account_locked_until:
                self.account_locked_until = None
        else:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.now(timezone.utc)
            
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.account_locked_until = datetime.now(timezone.utc).replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )  # Locked until end of day
        
        self.updated_at = datetime.now(timezone.utc)
    
    def is_account_locked(self) -> bool:
        """Check if account is locked"""
        if not self.account_locked_until:
            return False
        
        if datetime.now(timezone.utc) > self.account_locked_until:
            # Unlock expired lock
            self.account_locked_until = None
            self.failed_login_attempts = 0
            self.updated_at = datetime.now(timezone.utc)
            return False
        
        return True
    
    def update_profile(self, name: Optional[str] = None, phone: Optional[str] = None):
        """Update user profile information"""
        if name is not None:
            self.name = name.strip()
        if phone is not None:
            self.phone = phone
        self.updated_at = datetime.now(timezone.utc)
    
    def change_status(self, new_status: AuthStatus, reason: Optional[str] = None):
        """Change user account status"""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
        # Log status change in metadata
        if 'status_changes' not in self.metadata:
            self.metadata['status_changes'] = []
        
        self.metadata['status_changes'].append({
            'from': old_status.value,
            'to': new_status.value,
            'reason': reason,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def can_login(self) -> tuple[bool, Optional[str]]:
        """Check if user can login"""
        if self.status != AuthStatus.ACTIVE:
            return False, f"Account is {self.status.value}"
        
        if self.is_account_locked():
            return False, "Account is temporarily locked due to failed login attempts"
        
        return True, None
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary"""
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "status": self.status.value if isinstance(self.status, AuthStatus) else self.status,
            "address_id": self.address_id,
            "tenant_email": self.tenant_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "failed_login_attempts": self.failed_login_attempts,
            "metadata": self.metadata
        }
        
        if include_sensitive:
            data.update({
                "password_hash": self.password_hash,
                "email_verification_token": self.email_verification_token,
                "email_verification_expires": self.email_verification_expires.isoformat() if self.email_verification_expires else None,
                "password_reset_token": self.password_reset_token,
                "password_reset_expires": self.password_reset_expires.isoformat() if self.password_reset_expires else None,
                "last_failed_login": self.last_failed_login.isoformat() if self.last_failed_login else None,
                "account_locked_until": self.account_locked_until.isoformat() if self.account_locked_until else None
            })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserModel":
        """Create model from dictionary"""
        # Convert string values back to enums
        if isinstance(data.get("role"), str):
            data["role"] = UserRole(data["role"])
        if isinstance(data.get("status"), str):
            data["status"] = AuthStatus(data["status"])
        
        # Convert ISO strings back to datetime
        datetime_fields = [
            "created_at", "updated_at", "last_login", "email_verification_expires",
            "password_reset_expires", "last_failed_login", "account_locked_until"
        ]
        for field in datetime_fields:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def validate_role_constraints(self) -> List[str]:
        """Validate role-specific constraints"""
        errors = []
        
        if self.role == UserRole.RENT_PAYER:
            if not self.tenant_email:
                errors.append("Rent payer must have associated tenant email")
        
        if self.role == UserRole.TENANT:
            if self.tenant_email:
                errors.append("Tenant should not have tenant email")
        
        return errors
    
    def get_permissions(self) -> Dict[str, bool]:
        """Get user permissions based on role"""
        if self.role == UserRole.TENANT:
            return {
                "dashboard_access": True,
                "view_all_properties": True,
                "create_rental_agreements": True,
                "edit_rental_agreements": True,
                "delete_rental_agreements": True,
                "manage_rent_payers": True,
                "view_reports": True,
                "export_data": True,
                "send_payment_reminders": True
            }
        elif self.role == UserRole.RENT_PAYER:
            return {
                "dashboard_access": True,
                "view_own_payments": True,
                "view_payment_due": True,
                "make_payments": True,
                "view_payment_receipts": True,
                "view_rental_agreement": True,
                "update_profile": True
            }
        else:
            return {}
    
    def __repr__(self) -> str:
        return f"UserModel(id={self.id}, email={self.email}, role={self.role}, status={self.status})"
    
    def __str__(self) -> str:
        return f"{self.name} <{self.email}> ({self.role.value})"