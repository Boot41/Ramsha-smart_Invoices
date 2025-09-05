"""
Contract Processing ADK Agent

Converts the legacy ContractProcessingAgent to Google ADK pattern. This agent is responsible for processing contracts from various sources, extracting text, creating embeddings, and generating structured invoice data via RAG.
"""

# Standard library imports
import logging
import time
import os
from datetime import datetime
from typing import Dict, Any, AsyncGenerator

# Third-party imports
from google.adk.agents.invocation_context import InvocationContext
from pydantic import PrivateAttr

# Local application imports
from .base_adk_agent import BaseADKAgent, SimpleEvent
from schemas.workflow_schemas import AgentType, ProcessingStatus
from schemas.contract_schemas import ContractInvoiceData, InvoiceGenerationResponse
from schemas.unified_invoice_schemas import UnifiedInvoiceData
from services.contract_processor import get_contract_processor, ContractProcessor
from services.contract_rag_service import get_contract_rag_service, ContractRAGService
from services.mcp_service import get_mcp_service, OAuthExpiredError
from services.pinecone_service import get_pinecone_service

logger = logging.getLogger(__name__)


class ContractProcessingADKAgent(BaseADKAgent):
    """ADK Agent responsible for processing contracts and extracting structured data via RAG"""
    _contract_processor: ContractProcessor = PrivateAttr()
    _rag_service: ContractRAGService = PrivateAttr()
    
    def __init__(self):
        super().__init__(
            name="contract_processing_agent",
            agent_type=AgentType.CONTRACT_PROCESSING,
            description="Processes contracts, extracts text, creates embeddings, and generates structured invoice data using RAG",
            max_retries=3
        )
        self._contract_processor = get_contract_processor()
        self._rag_service = get_contract_rag_service()
    
    async def process_adk(self, state: Dict[str, Any], context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """
        ADK implementation for the contract processing workflow.

        Steps:
        1. Validate input parameters.
        2. Determine contract source and process the document to extract text and create embeddings.
        3. Use a RAG service to extract structured data from the processed content.
        4. Update the workflow state with the results.
        """
        workflow_id = state.get('workflow_id')
        yield self.create_progress_event(f"🚀 Starting ADK contract processing for workflow_id: {workflow_id}", 10.0)
        
        # --- 1. Validate Input Parameters ---
        user_id = state.get("user_id")
        contract_file = state.get("contract_file")
        contract_name = state.get("contract_name")
        
        # Extract existing_contract and contract_path from options if not in state directly
        options = state.get("options", {})
        existing_contract = state.get("existing_contract", options.get("existing_contract", False))
        contract_path = state.get("contract_path", options.get("contract_path"))
        
        yield self.create_progress_event(f"🔍 Initial state check - user_id: {user_id}, contract_name: {contract_name}, existing_contract: {existing_contract}, contract_path: {contract_path}", 15.0)
        
        if not user_id or not contract_name:
            error_msg = "Missing user_id or contract_name in workflow state"
            yield self.create_error_event("Validation failed", error_msg)
            raise ValueError(error_msg)

        # --- 2. Determine Source and Process Contract ---
        yield self.create_progress_event(f'📄 Step 1: Processing contract for workflow {workflow_id}', 20.0)
        
        # Normalize GDrive path from contract_name if necessary
        is_gdrive_source = (contract_path and contract_path.startswith('gdrive://')) or \
                           (contract_name and contract_name.startswith('gdrive://'))
        if is_gdrive_source and not contract_path:
            contract_path = contract_name
            state["contract_path"] = contract_path

        # Check validation conditions based on workflow type
        if existing_contract:
            if not contract_path:
                # Use contract_name as fallback path for existing contracts
                yield self.create_progress_event(f"⚠️ contract_path is missing, using contract_name as fallback: {contract_name}", 25.0, {"warning": True})
                contract_path = contract_name
                state["contract_path"] = contract_path
        else:
            # For new contracts, we need contract_file
            if not contract_file:
                error_msg = "Missing contract_file for new contract processing"
                yield self.create_error_event("Missing contract file", error_msg)
                raise ValueError(error_msg)

        processing_result = None
        try:
            if existing_contract:
                # Handle existing contracts
                if is_gdrive_source:
                    yield self.create_progress_event("📄 Processing existing contract from Google Drive...", 30.0)
                    processing_result = await self._process_gdrive_contract(contract_path, user_id, contract_name)
                else:
                    # Non-Google Drive existing contracts
                    yield self.create_progress_event("🔄 Using pre-processed contract data...", 30.0)
                    processing_result = self._handle_pre_processed_contract(contract_path, user_id, contract_name)
            
            elif isinstance(contract_file, str) and not contract_file.endswith('.pdf'):
                yield self.create_progress_event("🧪 Evaluation mode: processing text content directly", 30.0)
                processing_result = self._contract_processor.process_text_content(
                    text_content=contract_file, user_id=user_id, contract_name=contract_name)
            
            else:
                # Normal mode: Process PDF file
                yield self.create_progress_event("📄 Processing uploaded PDF contract file...", 30.0)
                processing_result = await self._contract_processor.process_contract(
                    pdf_file=contract_file, user_id=user_id, contract_name=contract_name)

            yield self.create_progress_event("Contract content processed successfully", 50.0)

        except Exception as e:
            # Check if this is an OAuth expiration error that should be propagated
            if isinstance(e, OAuthExpiredError):
                # Re-raise OAuth errors to be handled by the route
                raise e
            
            # Also check error message for backward compatibility
            error_msg_lower = str(e).lower()
            if "invalid_request" in error_msg_lower or "unauthorized" in error_msg_lower or "oauth_expired" in error_msg_lower:
                # Re-raise as OAuth error
                raise OAuthExpiredError("Google Drive authentication has expired. Please re-authenticate.") from e
            
            error_msg = f"Failed to process contract: {str(e)}"
            yield self.create_error_event("Contract processing failed", error_msg)
            raise e

        # --- 3. Extract Structured Data using RAG ---
        yield self.create_progress_event(f'🔍 Step 2: Extracting structured data for workflow {workflow_id}', 70.0)
        
        try:
            time.sleep(2)  # Allow time for Pinecone indexing to settle
            rag_response = self._rag_service.generate_invoice_data(user_id=user_id, contract_name=contract_name)
            yield self.create_progress_event("Structured data extracted successfully", 90.0, {"confidence": rag_response.confidence_score})
            
        except Exception as e:
            if "No contract data found" in str(e):
                yield self.create_progress_event(f"⚠️ No contract data in Pinecone for '{contract_name}'. Using fallback.", 90.0, {"fallback": True, "warning": True})
                rag_response = await self._create_fallback_rag_response(contract_name, user_id)
            else:
                error_msg = f"RAG service failed: {str(e)}"
                yield self.create_error_event("RAG extraction failed", error_msg)
                raise e
        
        # --- 4. Update Workflow State ---
        yield self.create_progress_event(f'✅ Step 3: Updating workflow state for workflow {workflow_id}', 95.0)
        
        unified_data = UnifiedInvoiceData.from_legacy_format(rag_response.invoice_data.model_dump())
        unified_data.metadata.workflow_id = workflow_id
        unified_data.metadata.user_id = user_id
        unified_data.metadata.confidence_score = rag_response.confidence_score
        
        unified_data_dict = unified_data.model_dump()
        unified_data_dict["raw_rag_response"] = rag_response.raw_response
        self.update_invoice_data(state, unified_data_dict, "contract_processing_agent")
        
        # Store agent-specific and legacy formats for backward compatibility
        state["contract_processing_result"] = {"rag_response": rag_response.model_dump(), "confidence_score": rag_response.confidence_score, "generated_at": datetime.now().isoformat(), "processing_successful": True}
        state["contract_data"] = rag_response.invoice_data.model_dump()
        state["contract_data"]["raw_rag_response"] = rag_response.raw_response
        state["invoice_data"] = {"invoice_response": rag_response.model_dump(), "generated_at": datetime.now().isoformat(), "confidence": rag_response.confidence_score}
        state["processing_status"] = ProcessingStatus.SUCCESS.value
        
        self.update_state_metrics(state, confidence=rag_response.confidence_score)
        context.state.update(state)
        
        yield self.create_progress_event(f"✅ ADK Contract processing finished for workflow_id: {workflow_id}", 100.0)
        yield self.create_success_event(
            "Contract processing completed successfully",
            data={"contract_name": contract_name, "confidence_score": rag_response.confidence_score, "workflow_id": workflow_id},
            confidence=rag_response.confidence_score
        )
    
    async def _process_gdrive_contract(self, contract_path: str, user_id: str, contract_name: str) -> Dict[str, Any]:
        """Fetches and processes a contract from a Google Drive source path."""
        try:
            file_id = contract_path.split('/')[-1]
            self.logger.info(f"🔍 Extracting Google Drive file ID: {file_id}")
            
            mcp_service = get_mcp_service()
            file_content, mime_type = mcp_service.read_file_content(file_id)
            self.logger.info(f"📄 GDrive content type: {mime_type}, size: {len(file_content) if file_content else 0}")
            
            if not file_content:
                raise Exception("Failed to fetch file content from Google Drive")

            self.logger.info("✅ Successfully fetched file content from Google Drive")
            
            if mime_type == "application/pdf" or contract_name.lower().endswith('.pdf'):
                self.logger.info("📁 Processing GDrive PDF by downloading to a temporary file")
                temp_file_path = mcp_service.download_file_to_temp(file_id, contract_name)
                with open(temp_file_path, 'rb') as f:
                    pdf_bytes = f.read()
                os.unlink(temp_file_path)
                return await self._contract_processor.process_contract(
                    pdf_file=pdf_bytes, user_id=user_id, contract_name=contract_name)
            else:
                self.logger.info("📝 Processing GDrive text content directly")
                return self._contract_processor.process_text_content(
                    text_content=file_content, user_id=user_id, contract_name=contract_name)
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch or process Google Drive file: {str(e)}")
            
            # Check if this is an OAuth expiration error
            if isinstance(e, OAuthExpiredError):
                # Re-raise the OAuth error to be handled by the route
                raise e
            
            # Also check error message for backward compatibility
            error_msg_lower = str(e).lower()
            if "invalid_request" in error_msg_lower or "unauthorized" in error_msg_lower or "oauth_expired" in error_msg_lower:
                # Re-raise as OAuth error
                raise OAuthExpiredError("Google Drive authentication has expired. Please re-authenticate.") from e
            
            # Fallback to dummy processing result for other errors
            return {
                'status': 'success',
                'message': f'Using existing contract (fetch failed): {contract_name}',
                'contract_name': contract_name,
                'user_id': user_id,
                'existing_contract': True,
                'contract_path': contract_path,
                'fetch_error': str(e)
            }

    def _handle_pre_processed_contract(self, contract_path: str, user_id: str, contract_name: str) -> Dict[str, Any]:
        """Handles a contract that is already processed and exists in the system."""
        self.logger.info(f"🔄 Using existing pre-processed contract: {contract_name}")
        return {
            'status': 'success',
            'message': f'Using existing contract: {contract_name}',
            'contract_name': contract_name,
            'user_id': user_id,
            'existing_contract': True,
            'contract_path': contract_path
        }

    async def _create_fallback_rag_response(self, contract_name: str, user_id: str) -> InvoiceGenerationResponse:
        """Creates a fallback RAG response when no contract data is found in the vector store."""
        self.logger.info(f"⚠️ Creating fallback response for missing contract data for '{contract_name}'")
        minimal_data = ContractInvoiceData(
            contract_title=contract_name,
            contract_type="other",
            notes=f"No contract data found for '{contract_name}'. This may be a test or sample contract.",
            confidence_score=0.1,
            extracted_at=datetime.now()
        )
        return InvoiceGenerationResponse(
            status="partial_success",
            message=f"No contract data found for '{contract_name}' - using minimal structure",
            contract_name=contract_name,
            user_id=user_id,
            invoice_data=minimal_data,
            raw_response="No contract data found in the vector database.",
            confidence_score=0.1,
            generated_at=datetime.now().isoformat()
        )
    