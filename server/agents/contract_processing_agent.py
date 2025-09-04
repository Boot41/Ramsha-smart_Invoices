from typing import Dict, Any
import logging
import asyncio
from datetime import datetime
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from services.contract_processor import get_contract_processor, ContractProcessor
from services.contract_rag_service import get_contract_rag_service, ContractRAGService

logger = logging.getLogger(__name__)

class ContractProcessingAgent(BaseAgent):
    """Agent responsible for processing the contract, including RAG."""

    def __init__(self):
        super().__init__(AgentType.CONTRACT_PROCESSING)
        self.contract_processor: ContractProcessor = get_contract_processor()
        self.rag_service: ContractRAGService = get_contract_rag_service()

    async def process(self, state: WorkflowState) -> WorkflowState:
        """
        Processes the contract by extracting text, storing embeddings, and using RAG.
        """
        workflow_id = state.get('workflow_id')
        self.logger.info(f"🚀 Starting contract processing for workflow_id: {workflow_id}")
        
        user_id = state.get("user_id")
        contract_file = state.get("contract_file")
        contract_name = state.get("contract_name")
        existing_contract = state.get("existing_contract", False)
        contract_path = state.get("contract_path")

        self.logger.info(f"🔍 Contract processing state check - user_id: {user_id}, contract_name: {contract_name}, existing_contract: {existing_contract}, contract_path: {contract_path}")

        # For existing contracts, we don't need contract_file but need contract_path
        if existing_contract:
            if not all([user_id, contract_name]):
                raise ValueError("Missing user_id or contract_name in workflow state for existing contract.")
            if not contract_path:
                # Use contract_name as fallback path for existing contracts
                self.logger.warning(f"⚠️ contract_path is missing, using contract_name as fallback: {contract_name}")
                contract_path = contract_name
                state["contract_path"] = contract_path
        else:
            # For new contracts, we need contract_file
            if not all([user_id, contract_file, contract_name]):
                raise ValueError("Missing user_id, contract_file, or contract_name in workflow state.")

        self.logger.info(f'📄 Step 1: Processing contract for workflow {workflow_id}')
        
        if existing_contract:
            # For existing contracts, fetch and process the file from Google Drive
            self.logger.info(f"📥 Fetching existing contract from: {contract_path}")
            
            if contract_path and contract_path.startswith('gdrive://'):
                try:
                    # Extract Google Drive file ID from path
                    file_id = contract_path.split('/')[-1]
                    self.logger.info(f"🔍 Extracting Google Drive file ID: {file_id}")
                    
                    # Use MCP service to fetch file content
                    from services.mcp_service import get_mcp_service
                    mcp_service = get_mcp_service()
                    
                    # Fetch file content from Google Drive
                    file_content, mime_type = mcp_service.read_file_content(file_id)
                    self.logger.info(f"📄 File content type: {mime_type}, size: {len(file_content) if file_content else 0} chars")
                    
                    if file_content:
                        self.logger.info(f"✅ Successfully fetched file content from Google Drive")
                        
                        # Handle PDF files - download to temp file for proper processing
                        if mime_type == "application/pdf" or contract_name.lower().endswith('.pdf'):
                            self.logger.info("📁 Processing PDF file - downloading to temp file")
                            temp_file_path = mcp_service.download_file_to_temp(file_id, contract_name)
                            
                            # Read the temporary file as bytes
                            with open(temp_file_path, 'rb') as f:
                                pdf_bytes = f.read()
                            
                            # Clean up temp file
                            import os
                            os.unlink(temp_file_path)
                            
                            # Process the PDF bytes
                            processing_result = await self.contract_processor.process_contract(
                                pdf_file=pdf_bytes,
                                user_id=user_id,
                                contract_name=contract_name
                            )
                        else:
                            # Handle text content directly
                            self.logger.info("📝 Processing text content directly")
                            processing_result = self.contract_processor.process_text_content(
                                text_content=file_content,
                                user_id=user_id,
                                contract_name=contract_name
                            )
                    else:
                        raise Exception("Failed to fetch file content from Google Drive")
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to fetch Google Drive file: {str(e)}")
                    
                    # Import the OAuth error class
                    from services.mcp_service import OAuthExpiredError
                    
                    # Check if this is an OAuth expiration error
                    if isinstance(e, OAuthExpiredError):
                        # Re-raise the OAuth error to be handled by the route
                        raise e
                    
                    # Also check error message for backward compatibility
                    error_msg = str(e).lower()
                    if "invalid_request" in error_msg or "unauthorized" in error_msg or "oauth_expired" in error_msg:
                        # Re-raise as OAuth error
                        raise OAuthExpiredError("Google Drive authentication has expired. Please re-authenticate.")
                    
                    # Fallback to dummy processing result for other errors
                    processing_result = {
                        'status': 'success',
                        'message': f'Using existing contract (fetch failed): {contract_name}',
                        'contract_name': contract_name,
                        'user_id': user_id,
                        'existing_contract': True,
                        'contract_path': contract_path,
                        'fetch_error': str(e)
                    }
            else:
                # For non-Google Drive existing contracts, assume already processed
                self.logger.info(f"🔄 Using existing contract: {contract_name} at path: {contract_path}")
                processing_result = {
                    'status': 'success',
                    'message': f'Using existing contract: {contract_name}',
                    'contract_name': contract_name,
                    'user_id': user_id,
                    'existing_contract': True,
                    'contract_path': contract_path
                }
        elif isinstance(contract_file, str) and not contract_file.endswith('.pdf'):
            # Evaluation mode: text content
            # For evaluation: skip PDF processing, use text directly
            self.logger.info("🧪 Evaluation mode detected - processing text content directly")
            
            # Process text content for embedding
            processing_result = self.contract_processor.process_text_content(
                text_content=contract_file,
                user_id=user_id,
                contract_name=contract_name
            )
            self.logger.info(f"✅ Text processing and embedding complete. Result: {processing_result.get('message')}")
        else:
            # Normal mode: Process PDF file
            self.logger.info("Step 1: Processing and embedding contract...")
            processing_result = await self.contract_processor.process_contract(
                pdf_file=contract_file,
                user_id=user_id,
                contract_name=contract_name
            )
            self.logger.info(f"✅ Contract processing and embedding complete. Result: {processing_result.get('message')}")

        # Step 2: Use the RAG service to extract structured invoice data.
        self.logger.info(f'🔍 Step 2: Extracting structured data using RAG service for workflow {workflow_id}')
        self.logger.info("Step 2: Extracting structured data using RAG service...")
        try:
            # Add small delay to allow Pinecone indexing to complete
            import time
            time.sleep(2)
            
            rag_response = self.rag_service.generate_invoice_data(
                user_id=user_id,
                contract_name=contract_name
            )
            self.logger.info("✅ RAG service executed successfully.")
        except Exception as e:
            # If RAG service fails (e.g., no contract data found), create a minimal response
            if "No contract data found" in str(e):
                self.logger.warning(f"⚠️ No contract data found in Pinecone for '{contract_name}'. Using fallback processing...")
                
                # Create a minimal response structure for failed processing
                from schemas.contract_schemas import ContractInvoiceData, InvoiceGenerationResponse
                
                # Create minimal invoice data
                minimal_data = ContractInvoiceData(
                    contract_title=contract_name,
                    contract_type="other",
                    notes=f"No contract data found for '{contract_name}'. This may be a test/sample contract.",
                    confidence_score=0.1,
                    extracted_at=datetime.now()
                )
                
                rag_response = InvoiceGenerationResponse(
                    status="partial_success",
                    message=f"⚠️ No contract data found for '{contract_name}' - using minimal structure",
                    contract_name=contract_name,
                    user_id=user_id,
                    invoice_data=minimal_data,
                    raw_response=f"No contract data found for '{contract_name}' in the database.",
                    confidence_score=0.1,
                    generated_at=datetime.now().isoformat()
                )
                self.logger.info("✅ Created fallback response for missing contract data")
            else:
                # Re-raise other exceptions
                raise e

        # Step 3: Update the workflow state with the results.
        self.logger.info(f'✅ Step 3: Updating workflow state with results for workflow {workflow_id}')
        state["contract_data"] = rag_response.invoice_data.model_dump()
        state["contract_data"]["raw_rag_response"] = rag_response.raw_response
        
        # Convert to unified format and store
        from schemas.unified_invoice_schemas import UnifiedInvoiceData
        unified_data = UnifiedInvoiceData.from_legacy_format(rag_response.invoice_data.model_dump())
        unified_data.metadata.workflow_id = workflow_id
        unified_data.metadata.user_id = user_id
        unified_data.metadata.confidence_score = rag_response.confidence_score
        
        # Store in unified format (primary)
        state["unified_invoice_data"] = unified_data.model_dump()
        
        # Also store in legacy format for backward compatibility
        state["invoice_data"] = {
            "invoice_response": rag_response.model_dump(),
            "generated_at": datetime.now().isoformat(),
            "confidence": rag_response.confidence_score
        }
        
        state["processing_status"] = ProcessingStatus.SUCCESS.value
        
        # Use the base agent method to update metrics
        self.update_state_metrics(
            state, 
            confidence=rag_response.invoice_data.confidence_score,
        )

        self.logger.info(f"✅ Contract processing agent finished for workflow_id: {state.get('workflow_id')}")
        
        return state