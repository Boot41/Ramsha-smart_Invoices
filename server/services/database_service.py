from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, date
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from db.postgresdb import AsyncSessionLocal
from models.database_models import User, Address, SecurityEvent, UserSession, UserRole, UserStatus, Invoice, InvoiceTemplate, InvoiceStatus
from schemas.auth_schemas import (
    UserRegistrationRequest, UpdateProfileRequest, 
    SecurityEventType, AuthStatus
)
from schemas.address_schemas import AddressCreate, AddressUpdate

logger = logging.getLogger(__name__)

def serialize_dates_for_json(obj):
    """Recursively serialize date objects to ISO format strings for JSON storage"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_dates_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates_for_json(item) for item in obj]
    else:
        return obj


class DatabaseService:
    """Database service for user and authentication operations"""
    
    def __init__(self):
        logger.info("✅ Database Service initialized")
    
    def get_session(self):
        """Get database session as context manager"""
        return AsyncSessionLocal()
    
    # User Operations
    async def create_user(
        self, 
        registration: UserRegistrationRequest,
        address_data: Optional[AddressCreate] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """Create a new user in the database"""
        try:
            async with self.get_session() as session:
                # Check if user already exists
                existing_user = await self.get_user_by_email(registration.email)
                if existing_user:
                    return False, "User with this email already exists", None
                
                # Create address if provided
                address = None
                if address_data:
                    address = Address(
                        street=address_data.street,
                        building_number=address_data.building_number,
                        room_number=address_data.room_number,
                        floor=address_data.floor,
                        apartment_unit=address_data.apartment_unit,
                        city=address_data.city,
                        state=address_data.state,
                        postal_code=address_data.postal_code,
                        country=address_data.country,
                        landmark=address_data.landmark,
                        neighborhood=address_data.neighborhood
                    )
                    session.add(address)
                    await session.flush()  # Get the address ID
                
                # Create user
                user = User(
                    email=registration.email.lower().strip(),
                    first_name=registration.first_name,
                    last_name=registration.last_name,
                    phone=registration.phone,
                    role=UserRole(registration.role.value),
                    status=UserStatus.ACTIVE,
                    tenant_email=registration.tenant_email.lower().strip() if registration.tenant_email else None,
                    address_id=address.id if address else None,
                    email_verified=False,
                    user_metadata={}
                )
                
                # Set password
                user.set_password(registration.password)
                
                # Generate email verification token
                user.generate_email_verification_token()
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"✅ User created in database: {user.email}")
                return True, "User created successfully", user
                
        except IntegrityError as e:
            logger.error(f"❌ Database integrity error creating user: {str(e)}")
            return False, "User with this email already exists", None
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error creating user: {str(e)}")
            return False, f"Database error: {str(e)}", None
        except Exception as e:
            logger.error(f"❌ Unexpected error creating user: {str(e)}")
            return False, f"Unexpected error: {str(e)}", None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting user by ID: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(User).where(User.email == email.lower().strip())
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting user by email: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, **kwargs) -> Tuple[bool, str, Optional[User]]:
        """Update user information"""
        try:
            async with self.get_session() as session:
                user = await self.get_user_by_id(user_id)
                if not user:
                    return False, "User not found", None
                
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                return True, "User updated successfully", user
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error updating user: {str(e)}")
            return False, f"Database error: {str(e)}", None
        except Exception as e:
            logger.error(f"❌ Unexpected error updating user: {str(e)}")
            return False, f"Unexpected error: {str(e)}", None
    
    async def update_user_password(self, user_id: str, new_password: str) -> Tuple[bool, str]:
        """Update user password"""
        try:
            async with self.get_session() as session:
                user = await self.get_user_by_id(user_id)
                if not user:
                    return False, "User not found"
                
                user.set_password(new_password)
                session.add(user)
                await session.commit()
                
                return True, "Password updated successfully"
                
        except Exception as e:
            logger.error(f"❌ Error updating user password: {str(e)}")
            return False, f"Password update failed: {str(e)}"
    
    async def record_login_attempt(
        self, 
        user_id: str, 
        success: bool, 
        ip_address: Optional[str] = None
    ) -> bool:
        """Record login attempt"""
        try:
            async with self.get_session() as session:
                user = await self.get_user_by_id(user_id)
                if not user:
                    return False
                
                user.record_login_attempt(success, ip_address)
                session.add(user)
                await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error recording login attempt: {str(e)}")
            return False
    
    # Address Operations
    async def create_address(self, address_data: AddressCreate) -> Optional[Address]:
        """Create a new address"""
        try:
            async with self.get_session() as session:
                address = Address(
                    street=address_data.street,
                    building_number=address_data.building_number,
                    room_number=address_data.room_number,
                    floor=address_data.floor,
                    apartment_unit=address_data.apartment_unit,
                    city=address_data.city,
                    state=address_data.state,
                    postal_code=address_data.postal_code,
                    country=address_data.country,
                    landmark=address_data.landmark,
                    neighborhood=address_data.neighborhood
                )
                
                session.add(address)
                await session.commit()
                await session.refresh(address)
                
                return address
                
        except Exception as e:
            logger.error(f"❌ Error creating address: {str(e)}")
            return None
    
    async def get_address_by_id(self, address_id: str) -> Optional[Address]:
        """Get address by ID"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(Address).where(Address.id == address_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting address by ID: {str(e)}")
            return None
    
    async def update_address(
        self, 
        address_id: str, 
        address_data: AddressUpdate
    ) -> Optional[Address]:
        """Update address information"""
        try:
            async with self.get_session() as session:
                address = await self.get_address_by_id(address_id)
                if not address:
                    return None
                
                # Update only non-None fields
                update_data = address_data.dict(exclude_unset=True)
                for key, value in update_data.items():
                    if hasattr(address, key):
                        setattr(address, key, value)
                
                session.add(address)
                await session.commit()
                await session.refresh(address)
                
                return address
                
        except Exception as e:
            logger.error(f"❌ Error updating address: {str(e)}")
            return None
    
    # Security Event Operations
    async def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log security event to database"""
        try:
            async with self.get_session() as session:
                event = SecurityEvent(
                    event_type=event_type,
                    user_id=user_id,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    event_metadata=metadata or {}
                )
                
                session.add(event)
                await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error logging security event: {str(e)}")
            return False
    
    async def get_security_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SecurityEvent]:
        """Get security events with filtering"""
        try:
            async with self.get_session() as session:
                query = select(SecurityEvent).order_by(SecurityEvent.timestamp.desc())
                
                if user_id:
                    query = query.where(SecurityEvent.user_id == user_id)
                if event_type:
                    query = query.where(SecurityEvent.event_type == event_type)
                
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"❌ Error getting security events: {str(e)}")
            return []
    
    # User Session Operations
    async def create_session(
        self,
        user_id: str,
        session_token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> Optional[UserSession]:
        """Create a user session"""
        try:
            async with self.get_session() as session:
                user_session = UserSession(
                    user_id=user_id,
                    session_token=session_token,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_info=device_info
                )
                
                session.add(user_session)
                await session.commit()
                await session.refresh(user_session)
                
                return user_session
                
        except Exception as e:
            logger.error(f"❌ Error creating session: {str(e)}")
            return None
    
    async def get_active_sessions(self, user_id: str) -> List[UserSession]:
        """Get active sessions for a user"""
        try:
            async with self.get_session() as session:
                query = select(UserSession).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.now(timezone.utc)
                    )
                ).order_by(UserSession.last_activity.desc())
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"❌ Error getting active sessions: {str(e)}")
            return []
    
    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a user session"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    update(UserSession)
                    .where(UserSession.session_token == session_token)
                    .values(is_active=False)
                )
                await session.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Error invalidating session: {str(e)}")
            return False
    
    # Utility Methods
    async def get_user_count(self) -> int:
        """Get total number of users"""
        try:
            async with self.get_session() as session:
                result = await session.execute(select(User.id))
                return len(result.scalars().all())
        except Exception as e:
            logger.error(f"❌ Error getting user count: {str(e)}")
            return 0
    
    async def list_users(
        self,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[User], int]:
        """List users with filtering and pagination"""
        try:
            async with self.get_session() as session:
                # Base query
                query = select(User).order_by(User.created_at.desc())
                count_query = select(User.id)
                
                # Apply filters
                if role:
                    query = query.where(User.role == role)
                    count_query = count_query.where(User.role == role)
                if status:
                    query = query.where(User.status == status)
                    count_query = count_query.where(User.status == status)
                
                # Get count
                count_result = await session.execute(count_query)
                total = len(count_result.scalars().all())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Get users
                result = await session.execute(query)
                users = result.scalars().all()
                
                return users, total
                
        except Exception as e:
            logger.error(f"❌ Error listing users: {str(e)}")
            return [], 0

    # Invoice Operations
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Optional[Invoice]:
        """Create a new invoice in the database"""
        try:
            async with self.get_session() as session:
                # Extract data from invoice JSON
                header = invoice_data.get("invoice_header", {})
                parties = invoice_data.get("parties", {})
                client = parties.get("client", {})
                provider = parties.get("service_provider", {})
                payment_info = invoice_data.get("payment_information", {})
                totals = invoice_data.get("totals", {}) or invoice_data.get("financial_details", {})
                contract_details = invoice_data.get("contract_details", {})
                metadata = invoice_data.get("metadata", {}) or invoice_data.get("processing_metadata", {})
                
                # Parse dates
                invoice_date = datetime.fromisoformat(header.get("invoice_date", datetime.now().isoformat()))
                due_date = datetime.fromisoformat(header.get("due_date", datetime.now().isoformat()))
                
                invoice = Invoice(
                    invoice_number=header.get("invoice_number", header.get("invoice_id", "")),
                    workflow_id=header.get("workflow_id", ""),
                    user_id=metadata.get("user_id") or invoice_data.get("processing_metadata", {}).get("user_id"),
                    invoice_date=invoice_date,
                    due_date=due_date,
                    status=InvoiceStatus.GENERATED,
                    
                    # Client information
                    client_name=client.get("name", ""),
                    client_email=client.get("email"),
                    client_address=client.get("address"),
                    client_phone=client.get("phone"),
                    
                    # Service provider information
                    service_provider_name=provider.get("name", ""),
                    service_provider_email=provider.get("email"),
                    service_provider_address=provider.get("address"),
                    service_provider_phone=provider.get("phone"),
                    
                    # Financial information
                    subtotal=float(totals.get("subtotal", 0)),
                    tax_amount=float(totals.get("tax_amount", 0)),
                    total_amount=float(totals.get("total_amount", 0)),
                    currency=payment_info.get("currency", "USD"),
                    
                    # Contract details
                    contract_title=contract_details.get("contract_type"),
                    contract_type=contract_details.get("contract_type"),
                    contract_reference=header.get("contract_reference"),
                    
                    # Complete invoice data - serialize dates for JSON storage
                    invoice_data=serialize_dates_for_json(invoice_data),
                    
                    # AI metadata
                    generated_by_agent="correction_agent",
                    confidence_score=float(metadata.get("confidence_score", 0)),
                    quality_score=float(metadata.get("quality_score", 0)),
                    human_reviewed=metadata.get("human_input_applied", False)
                )
                
                session.add(invoice)
                await session.commit()
                await session.refresh(invoice)
                
                logger.info(f"✅ Invoice created in database: {invoice.invoice_number}")
                return invoice
                
        except Exception as e:
            logger.error(f"❌ Error creating invoice: {str(e)}")
            return None
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(Invoice).where(Invoice.id == invoice_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting invoice by ID: {str(e)}")
            return None
    
    async def get_invoice_by_workflow_id(self, workflow_id: str) -> Optional[Invoice]:
        """Get invoice by workflow ID"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(Invoice).where(Invoice.workflow_id == workflow_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting invoice by workflow ID: {str(e)}")
            return None
    
    async def list_invoices(
        self,
        user_id: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Invoice], int]:
        """List invoices with filtering and pagination"""
        try:
            async with self.get_session() as session:
                # Base query
                query = select(Invoice).order_by(Invoice.created_at.desc())
                count_query = select(Invoice.id)
                
                # Apply filters
                if user_id:
                    query = query.where(Invoice.user_id == user_id)
                    count_query = count_query.where(Invoice.user_id == user_id)
                if status:
                    query = query.where(Invoice.status == status)
                    count_query = count_query.where(Invoice.status == status)
                
                # Get count
                count_result = await session.execute(count_query)
                total = len(count_result.scalars().all())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Get invoices
                result = await session.execute(query)
                invoices = result.scalars().all()
                
                return invoices, total
                
        except Exception as e:
            logger.error(f"❌ Error listing invoices: {str(e)}")
            return [], 0
    
    # Invoice Template Operations
    async def create_invoice_template(
        self,
        invoice_id: str,
        template_name: str,
        component_name: str,
        template_type: str,
        file_path: str,
        component_code: str,
        model_used: Optional[str] = None
    ) -> Optional[InvoiceTemplate]:
        """Create a new invoice template"""
        try:
            async with self.get_session() as session:
                template = InvoiceTemplate(
                    invoice_id=invoice_id,
                    template_name=template_name,
                    component_name=component_name,
                    template_type=template_type,
                    file_path=file_path,
                    component_code=component_code,
                    generated_by="ui_invoice_generator",
                    model_used=model_used,
                    is_active=True
                )
                
                session.add(template)
                await session.commit()
                await session.refresh(template)
                
                logger.info(f"✅ Invoice template created: {template_name}")
                return template
                
        except Exception as e:
            logger.error(f"❌ Error creating invoice template: {str(e)}")
            return None
    
    async def list_invoice_templates(
        self,
        invoice_id: Optional[str] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[InvoiceTemplate], int]:
        """List invoice templates with filtering"""
        try:
            async with self.get_session() as session:
                # Base query
                query = select(InvoiceTemplate).order_by(InvoiceTemplate.created_at.desc())
                count_query = select(InvoiceTemplate.id)
                
                # Apply filters
                if invoice_id:
                    query = query.where(InvoiceTemplate.invoice_id == invoice_id)
                    count_query = count_query.where(InvoiceTemplate.invoice_id == invoice_id)
                
                query = query.where(InvoiceTemplate.is_active == is_active)
                count_query = count_query.where(InvoiceTemplate.is_active == is_active)
                
                # Get count
                count_result = await session.execute(count_query)
                total = len(count_result.scalars().all())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Get templates
                result = await session.execute(query)
                templates = result.scalars().all()
                
                return templates, total
                
        except Exception as e:
            logger.error(f"❌ Error listing invoice templates: {str(e)}")
            return [], 0


# Global service instance
_database_service = None

def get_database_service() -> DatabaseService:
    """Get singleton database service instance"""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service