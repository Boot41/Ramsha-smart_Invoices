from typing import Dict, Any
import logging
import asyncio
from datetime import datetime
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from services.contract_processor import get_contract_processor, ContractProcessor
from services.contract_rag_service import get_contract_rag_service, ContractRAGService
from services.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)

class ContractProcessingAgent(BaseAgent):
    """Agent responsible for processing the contract, including RAG."""

    def __init__(self):
        super().__init__(AgentType.CONTRACT_PROCESSING)
        self.contract_processor: ContractProcessor = get_contract_processor()
        self.rag_service: ContractRAGService = get_contract_rag_service()
        self.websocket_manager = get_websocket_manager()

    async def process(self, state: WorkflowState) -> WorkflowState:
        """
        Processes the contract by extracting text, storing embeddings, and using RAG.
        """
        workflow_id = state.get('workflow_id')
        self.logger.info(f"🚀 Starting contract processing for workflow_id: {workflow_id}")
        
        user_id = state.get("user_id")
        contract_file = state.get("contract_file")
        contract_name = state.get("contract_name")

        if not all([user_id, contract_file, contract_name]):
            raise ValueError("Missing user_id, contract_file, or contract_name in workflow state.")

        # Check if we're in evaluation mode (text content) or normal mode (PDF bytes)
        is_evaluation_mode = isinstance(contract_file, str) and not contract_file.endswith('.pdf')
        
        await self.websocket_manager.notify_workflow_status(workflow_id, "in_progress", "Step 1: Processing and embedding contract...")
        if is_evaluation_mode:
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
        await self.websocket_manager.notify_workflow_status(workflow_id, "in_progress", "Step 2: Extracting structured data using RAG service...")
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
        await self.websocket_manager.notify_workflow_status(workflow_id, "in_progress", "Step 3: Updating workflow state with results...")
        state["contract_data"] = rag_response.invoice_data.model_dump()
        state["contract_data"]["raw_rag_response"] = rag_response.raw_response
        
        # Also store in invoice_data format expected by evaluation framework
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