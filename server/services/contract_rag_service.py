from pydantic import BaseModel
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from fastapi import HTTPException
from db.db import get_pinecone_client, get_async_database
from models.llm import get_embedding_model, get_chat_model
from langchain_core.runnables import RunnablePassthrough, RunnableMap
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from schemas.contract_schemas import ContractInvoiceData, InvoiceGenerationResponse
from models.llm.base import get_model
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create a chat history for the session."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


class ContractRAGService:
    """RAG service specifically for contract invoice data generation"""
    
    def __init__(self):
        self.embedding_service = get_embedding_model()
        self.chat_model = get_chat_model()
        logger.info("🚀 Contract RAG Service initialized")
    
    def generate_invoice_data(self, user_id: str, contract_name: str, query: str = None) -> InvoiceGenerationResponse:
        """
        Generate structured invoice data from contract using RAG
        
        Args:
            user_id: User ID
            contract_name: Name of the contract
            query: Optional specific query (default: extract invoice data)
            
        Returns:
            InvoiceGenerationResponse with structured data
        """
        try:
            if not query:
                query = "Extract all rental/lease information including monthly rent, tenant/landlord details, property information, payment terms, lease dates, and all billing-related data from this rental agreement"
            
            logger.info(f"🚀 Generating invoice data for contract: {contract_name}")
            
            # Get contract context using RAG
            context = self._retrieve_contract_context(user_id, contract_name, query)
            
            # Generate structured invoice data
            invoice_data = self._extract_invoice_data_from_context(context, contract_name)
            
            # Parse the response into structured data
            structured_data = self._parse_invoice_response(invoice_data)
            
            return InvoiceGenerationResponse(
                status="success",
                message="✅ Invoice data generated successfully",
                contract_name=contract_name,
                user_id=user_id,
                invoice_data=structured_data,
                raw_response=invoice_data,
                confidence_score=0.85,  # You can implement confidence scoring
                generated_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to generate invoice data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate invoice data: {str(e)}"
            )
    
    def _retrieve_contract_context(self, user_id: str, contract_name: str, query: str) -> str:
        """Retrieve relevant contract context using vector search"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embedding_model.embed_query(query)
            
            # Search Pinecone for relevant chunks
            index = get_pinecone_client()
            response = index.query(
                vector=query_embedding,
                top_k=10,
                include_metadata=True,
                filter={
                    "user_id": user_id,
                    "contract_name": contract_name,
                    "document_type": "contract"
                }
            )
            
            if not response.matches:
                raise HTTPException(
                    status_code=404,
                    detail=f"No contract data found for {contract_name}"
                )
            
            # Combine relevant text chunks
            context_chunks = []
            for match in response.matches:
                if match.metadata and "text" in match.metadata:
                    context_chunks.append(match.metadata["text"])
            
            context = "\n\n".join(context_chunks)
            logger.info(f"✅ Retrieved context: {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve contract context: {str(e)}")
            raise
    
    def _extract_invoice_data_from_context(self, context: str, contract_name: str) -> str:
        """Extract invoice data from contract context using LLM"""
        try:
            # Create specialized prompt for invoice data extraction (enhanced for rental agreements)
            system_prompt = f"""You are an expert rental agreement analyst specializing in extracting invoice and billing information from rental contracts and lease agreements.

Your task is to analyze the provided rental agreement/lease contract text and extract ALL relevant information for rent invoice generation in a structured JSON format.

**RENTAL AGREEMENT SPECIFIC EXTRACTION:**
1. **Property & Contract Details**: property address, lease title, contract number, lease dates (start, end)
2. **Parties**: tenant (client) and landlord (service provider) details (name, email, address, phone, tax ID)
3. **Rent & Payment Terms**: monthly rent, security deposit, currency, due date, late fees, payment method
4. **Property Services**: rent amount, utilities, maintenance fees, parking fees, pet fees, etc.
5. **Billing Schedule**: monthly rent cycle, first rent due date, ongoing schedule
6. **Lease Terms**: lease duration, renewal terms, special rental conditions

**IMPORTANT FOR RENTAL AGREEMENTS:**
- Tenant = client role, Landlord = service_provider role
- Monthly rent = primary recurring charge
- Security deposit is separate from monthly billing
- Look for rent escalation clauses, utility responsibilities
- Extract pet fees, parking fees, utility allowances if mentioned

**IMPORTANT FORMATTING REQUIREMENTS:**
- Return ONLY a valid JSON object
- Use the exact field names as specified
- For dates, use YYYY-MM-DD format
- For amounts, use decimal numbers without currency symbols
- If information is not found, use null for that field
- Be thorough and extract all relevant billing information

**JSON Structure:**
{{
  "contract_title": "string or null",
  "contract_type": "service_agreement|rental_lease|maintenance_contract|supply_contract|consulting_agreement|other",
  "contract_number": "string or null",
  "client": {{
    "name": "string",
    "email": "email or null",
    "address": "string or null",
    "phone": "string or null",
    "tax_id": "string or null",
    "role": "client"
  }},
  "service_provider": {{
    "name": "string",
    "email": "email or null", 
    "address": "string or null",
    "phone": "string or null",
    "tax_id": "string or null",
    "role": "service_provider"
  }},
  "start_date": "YYYY-MM-DD or null",
  "end_date": "YYYY-MM-DD or null",
  "effective_date": "YYYY-MM-DD or null",
  "payment_terms": {{
    "amount": decimal or null,
    "currency": "USD",
    "frequency": "monthly|quarterly|biannually|annually|one_time|custom",
    "due_days": number or null,
    "late_fee": decimal or null,
    "discount_terms": "string or null"
  }},
  "services": [
    {{
      "description": "string",
      "quantity": decimal or null,
      "unit_price": decimal or null,
      "total_amount": decimal or null,
      "unit": "string or null"
    }}
  ],
  "invoice_frequency": "monthly|quarterly|biannually|annually|one_time|custom",
  "first_invoice_date": "YYYY-MM-DD or null",
  "next_invoice_date": "YYYY-MM-DD or null",
  "special_terms": "string or null",
  "notes": "string or null"
}}

Contract Text:
{context}"""
            
            # Generate response using LangChain
            model = get_model()
            response = model.invoke(system_prompt)
            result = response.content
            
            logger.info(f"✅ Extracted invoice data from context")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to extract invoice data: {str(e)}")
            raise
    
    def _parse_invoice_response(self, raw_response: str) -> ContractInvoiceData:
        """Parse LLM response into structured ContractInvoiceData"""
        try:
            # Clean the response to extract JSON
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = raw_response
            
            # Parse JSON
            parsed_data = json.loads(json_str)
            
            # Create ContractInvoiceData object
            invoice_data = ContractInvoiceData(
                **parsed_data,
                confidence_score=0.85,
                extracted_at=datetime.now()
            )
            
            logger.info("✅ Successfully parsed invoice data into structured format")
            return invoice_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {str(e)}")
            # Return empty structure with raw response in notes
            return ContractInvoiceData(
                notes=f"Failed to parse structured data. Raw response: {raw_response[:500]}...",
                confidence_score=0.3,
                extracted_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"❌ Failed to create structured data: {str(e)}")
            return ContractInvoiceData(
                notes=f"Error processing data: {str(e)}",
                confidence_score=0.2,
                extracted_at=datetime.now()
            )
    
    def query_contract(self, user_id: str, contract_name: str, query: str) -> str:
        """
        General contract querying using RAG
        
        Args:
            user_id: User ID
            contract_name: Contract name
            query: User query
            
        Returns:
            Response string
        """
        try:
            logger.info(f"🚀 Processing contract query: {query}")
            
            # Get context
            context = self._retrieve_contract_context(user_id, contract_name, query)
            
            # Create prompt for general querying
            system_prompt = f"""You are a contract analysis expert. Answer the user's question based on the contract information provided.

Instructions:
1. Use only information from the provided contract text
2. Be accurate and specific in your response
3. If information is not available, clearly state that
4. Keep responses concise but comprehensive
5. Focus on the contract named: {contract_name}

Contract Information:
{context}

User Question: {query}

Answer:"""
            
            # Generate response using LangChain
            model = get_model()
            response = model.invoke(system_prompt)
            result = response.content
            
            logger.info("✅ Contract query processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to process contract query: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process contract query: {str(e)}"
            )


# Global service instance
_contract_rag_service = None

def get_contract_rag_service() -> ContractRAGService:
    """Get singleton contract RAG service instance"""
    global _contract_rag_service
    if _contract_rag_service is None:
        _contract_rag_service = ContractRAGService()
    return _contract_rag_service