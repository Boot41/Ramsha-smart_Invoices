from typing import Dict, Any
import logging
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from services.database_service import get_database_service
from services.websocket_manager import get_websocket_manager
import uuid

logger = logging.getLogger(__name__)

class InvoiceGeneratorAgent(BaseAgent):
    """Agent responsible for creating invoice records in the database"""
    
    def __init__(self):
        super().__init__(AgentType.INVOICE_GENERATION)
        self.db_service = get_database_service()
        self.websocket_manager = get_websocket_manager()
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """
        Create invoice record in database from final invoice data
        
        Args:
            state: Current workflow state containing invoice data
            
        Returns:
            Updated workflow state with invoice_id
        """
        workflow_id = state.get('workflow_id')
        self.logger.info(f"📄 Starting invoice creation for workflow_id: {workflow_id}")
        
        try:
            # Extract invoice data from state
            invoice_data = self._extract_invoice_data(state)
            if not invoice_data:
                raise ValueError("No invoice data found for database creation")
            
            # Extract required fields
            user_id = state.get("user_id")
            if not user_id:
                self.logger.warning("⚠️ user_id not found in state, checking workflow_id for fallback")
                # Try to extract user_id from workflow or use a default
                user_id = state.get("workflow_user_id") or "system"
                if user_id == "system":
                    self.logger.warning("⚠️ Using 'system' as fallback user_id")
            
            # Generate invoice number
            invoice_number = self._generate_invoice_number()
            
            # Calculate dates
            invoice_date = datetime.now().date()
            due_date = self._calculate_due_date(invoice_data, invoice_date)
            
            # Extract client and provider information
            client_info = self._extract_client_info(invoice_data)
            provider_info = self._extract_provider_info(invoice_data)
            
            # Extract financial information
            financial_info = self._extract_financial_info(invoice_data)
            
            # Generate invoice UUID
            invoice_uuid = str(uuid.uuid4())
            
            # Get contract UUID from state (if available)
            contract_uuid = state.get("contract_id") or state.get("contract_uuid")
            
            # Create comprehensive invoice data as JSONB
            final_invoice_data = {
                "invoice_header": {
                    "invoice_uuid": invoice_uuid,
                    "invoice_number": invoice_number,
                    "workflow_id": workflow_id,
                    "contract_uuid": contract_uuid,
                    "invoice_date": invoice_date.isoformat(),
                    "due_date": due_date.isoformat(),
                    "status": "generated",
                    "created_at": datetime.now().isoformat()
                },
                "parties": {
                    "client": {
                        "name": client_info["name"],
                        "email": client_info.get("email"),
                        "address": client_info.get("address"),
                        "phone": client_info.get("phone")
                    },
                    "service_provider": {
                        "name": provider_info["name"],
                        "email": provider_info.get("email"),
                        "address": provider_info.get("address"),
                        "phone": provider_info.get("phone")
                    }
                },
                "payment_information": {
                    "currency": financial_info.get("currency", "USD"),
                    "amount": financial_info["total_amount"],
                    "payment_terms": {
                        "due_days": (due_date - invoice_date).days,
                        "frequency": invoice_data.get("payment_terms", {}).get("frequency", "one-time")
                    }
                },
                "financial_details": {
                    "subtotal": financial_info["subtotal"],
                    "tax_amount": financial_info.get("tax_amount", 0.0),
                    "total_amount": financial_info["total_amount"],
                    "currency": financial_info.get("currency", "USD")
                },
                "contract_details": {
                    "contract_title": state.get("contract_name", "Service Contract"),
                    "contract_type": "service",
                    "contract_reference": contract_uuid,
                    "workflow_id": workflow_id
                },
                "processing_metadata": {
                    "user_id": user_id,
                    "generated_by_agent": "invoice_generator",
                    "confidence_score": state.get("confidence_level", 0.8),
                    "quality_score": state.get("quality_score", 0.8),
                    "human_reviewed": state.get("human_input_applied", False),
                    "validation_passed": state.get("validation_results", {}).get("is_valid", False),
                    "created_timestamp": datetime.now().isoformat(),
                    "workflow_id": workflow_id,
                    "original_invoice_data": invoice_data
                }
            }
            
            # Create invoice record
            invoice_record = await self.db_service.create_invoice(final_invoice_data)
            
            if invoice_record:
                # Store invoice_id and invoice data in state
                state["invoice_id"] = invoice_record.id
                state["invoice_uuid"] = invoice_uuid
                state["invoice_number"] = invoice_record.invoice_number
                state["invoice_created"] = True
                state["final_invoice_data"] = final_invoice_data  # Store complete invoice data for frontend
                
                # Update processing status
                state["processing_status"] = ProcessingStatus.SUCCESS.value
                
                # Notify WebSocket clients with complete invoice data
                if workflow_id:
                    await self.websocket_manager.broadcast_workflow_event(workflow_id, 'invoice_created', {
                        'agent': 'invoice_generator',
                        'message': f'Invoice {invoice_record.invoice_number} created successfully',
                        'invoice_id': invoice_record.id,
                        'invoice_uuid': invoice_uuid,
                        'invoice_number': invoice_record.invoice_number,
                        'contract_uuid': contract_uuid,
                        'total_amount': float(financial_info["total_amount"]),
                        'currency': financial_info.get("currency", "USD"),
                        'invoice_data': final_invoice_data  # Include full invoice data
                    })
                
                self.logger.info(f"✅ Invoice created successfully: {invoice_record.invoice_number} (UUID: {invoice_uuid}, DB ID: {invoice_record.id})")
                return state
            else:
                raise ValueError("Failed to create invoice record")
                
        except Exception as e:
            self.logger.error(f"❌ Invoice creation failed: {str(e)}")
            
            # Notify error via WebSocket
            if workflow_id:
                await self.websocket_manager.broadcast_workflow_event(workflow_id, 'agent_error', {
                    'agent': 'invoice_generator',
                    'message': f'Invoice creation failed: {str(e)}',
                    'error_type': 'invoice_creation_error'
                })
            
            state["processing_status"] = ProcessingStatus.FAILED.value
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "invoice_generator",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return state
    
    def _extract_invoice_data(self, state: WorkflowState) -> Dict[str, Any]:
        """Extract invoice data from state"""
        
        # Try final invoice first (from correction agent)
        if state.get("final_invoice"):
            return state["final_invoice"]
        
        # Try invoice_data from validation or RAG
        if state.get("invoice_data"):
            return state["invoice_data"]
        
        # Try contract data as fallback
        if state.get("contract_data"):
            return state["contract_data"]
        
        return None
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"INV-{timestamp}-{unique_id}"
    
    def _calculate_due_date(self, invoice_data: Dict[str, Any], invoice_date: datetime.date) -> datetime.date:
        """Calculate due date from invoice data"""
        
        # Try to get payment due days from invoice data
        payment_due_days = None
        
        # Check various possible locations for due days
        if isinstance(invoice_data, dict):
            payment_due_days = (
                invoice_data.get("payment_due_days") or
                invoice_data.get("payment_terms", {}).get("due_days") or
                invoice_data.get("payment_terms", {}).get("payment_due_days")
            )
        
        # Default to 30 days if not specified
        if not payment_due_days or not isinstance(payment_due_days, (int, float)):
            payment_due_days = 30
        
        return invoice_date + timedelta(days=int(payment_due_days))
    
    def _extract_client_info(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract client information from invoice data"""
        
        client_info = {"name": "Unknown Client"}
        
        if isinstance(invoice_data, dict):
            # Try various possible locations for client info
            client = (
                invoice_data.get("client") or
                invoice_data.get("customer") or
                invoice_data.get("tenant") or
                {}
            )
            
            if isinstance(client, dict):
                client_info.update({
                    "name": client.get("name", "Unknown Client"),
                    "email": client.get("email"),
                    "address": client.get("address"),
                    "phone": client.get("phone")
                })
            elif isinstance(client, str):
                client_info["name"] = client
        
        return client_info
    
    def _extract_provider_info(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract service provider information from invoice data"""
        
        provider_info = {"name": "Service Provider"}
        
        if isinstance(invoice_data, dict):
            # Try various possible locations for provider info
            provider = (
                invoice_data.get("service_provider") or
                invoice_data.get("provider") or
                invoice_data.get("landlord") or
                invoice_data.get("company") or
                {}
            )
            
            if isinstance(provider, dict):
                provider_info.update({
                    "name": provider.get("name", "Service Provider"),
                    "email": provider.get("email"),
                    "address": provider.get("address"),
                    "phone": provider.get("phone")
                })
            elif isinstance(provider, str):
                provider_info["name"] = provider
        
        return provider_info
    
    def _extract_financial_info(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial information from invoice data"""
        
        financial_info = {
            "subtotal": 0.0,
            "total_amount": 0.0,
            "currency": "USD"
        }
        
        if isinstance(invoice_data, dict):
            # Try various possible locations for financial info
            payment_terms = invoice_data.get("payment_terms", {})
            
            # Extract amount
            amount = (
                payment_terms.get("amount") or
                invoice_data.get("payment_amount") or
                invoice_data.get("amount") or
                0.0
            )
            
            if isinstance(amount, (int, float)):
                financial_info["subtotal"] = float(amount)
                financial_info["total_amount"] = float(amount)  # Simplified, could add tax logic
            elif isinstance(amount, str):
                try:
                    # Try to parse amount string
                    amount_str = amount.replace("$", "").replace(",", "")
                    amount_float = float(amount_str)
                    financial_info["subtotal"] = amount_float
                    financial_info["total_amount"] = amount_float
                except (ValueError, TypeError):
                    pass
            
            # Extract currency
            currency = (
                payment_terms.get("currency") or
                invoice_data.get("currency") or
                "USD"
            )
            financial_info["currency"] = currency
        
        return financial_info