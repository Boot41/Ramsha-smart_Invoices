from typing import Dict, Any
import logging
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

    def process(self, state: WorkflowState) -> WorkflowState:
        """
        Processes the contract by extracting text, storing embeddings, and using RAG.
        """
        self.logger.info(f"🚀 Starting contract processing for workflow_id: {state.get('workflow_id')}")
        
        user_id = state.get("user_id")
        contract_file = state.get("contract_file")
        contract_name = state.get("contract_name")

        if not all([user_id, contract_file, contract_name]):
            raise ValueError("Missing user_id, contract_file, or contract_name in workflow state.")

        # Step 1: Process the contract to extract text, create embeddings, and store in Pinecone.
        # This is a prerequisite for the RAG service.
        self.logger.info("Step 1: Processing and embedding contract...")
        processing_result = self.contract_processor.process_contract(
            pdf_file=contract_file,
            user_id=user_id,
            contract_name=contract_name
        )
        self.logger.info(f"✅ Contract processing and embedding complete. Result: {processing_result.get('message')}")

        # Step 2: Use the RAG service to extract structured invoice data.
        self.logger.info("Step 2: Extracting structured data using RAG service...")
        rag_response = self.rag_service.generate_invoice_data(
            user_id=user_id,
            contract_name=contract_name
        )
        self.logger.info("✅ RAG service executed successfully.")

        # Step 3: Update the workflow state with the results.
        state["contract_data"] = rag_response.invoice_data.model_dump()
        state["contract_data"]["raw_rag_response"] = rag_response.raw_response
        state["processing_status"] = ProcessingStatus.SUCCESS.value
        
        # Use the base agent method to update metrics
        self.update_state_metrics(
            state, 
            confidence=rag_response.invoice_data.confidence_score,
        )

        self.logger.info(f"✅ Contract processing agent finished for workflow_id: {state.get('workflow_id')}")
        
        return state
