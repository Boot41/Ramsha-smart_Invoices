from pydantic import BaseModel
from fastapi import HTTPException
from db.db import get_pinecone_client
from models.llm.embedding import get_embedding_service
from models.llm.base import get_model
from schemas.contract_schemas import ContractInvoiceData, InvoiceGenerationResponse, ContractParty, LineItem
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)


class RentalInvoiceSchema(BaseModel):
    tenant_name: str
    landlord_name: str
    monthly_rent: float
    lease_start: str
    lease_end: str
    payment_terms: str



class ContractRAGService:
    """RAG service specifically for contract invoice data generation"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.chat_model = get_model()
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
            query_embedding = self.embedding_service.embed_query(query)
            
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
            # Create specialized prompt for invoice data extraction (enhanced for all contract types)
            system_prompt = f'''You are an expert contract analyst specializing in extracting invoice and billing information from rental and lease agreements.

Your task is to analyze the provided contract text and extract ALL relevant information for invoice generation into a structured JSON format.

**CRITICAL EXTRACTION GUIDELINES:**

1.  **Identify All Charges**: Locate every distinct financial charge in the contract. This includes recurring charges like monthly rent and maintenance, and one-time charges like security deposits or late fees.
2.  **Create Line Items**: Each distinct charge MUST be a separate object in the `line_items` array. Do NOT group them together.
3.  **Categorize Correctly**: Assign a category to each line item from the allowed list: `rent`, `deposit`, `utility`, `maintenance_fee`, `late_fee`, `other`.
4.  **Words to Numbers**: If an amount is written in words (e.g., "Rupees Four Thousand"), you MUST convert it to a number (e.g., 4000).
5.  **No External Information**: Use ONLY the information present in the provided "Contract Text". Do not invent or infer details not present.
6.  **Handle Ambiguity**: If a value is not clearly stated, use `null`.

**DETAILED FIELD INSTRUCTIONS:**

-   **Parties (client, service_provider)**: For rental agreements, the tenant is the "client" and the landlord/owner is the "service_provider". Extract their full name, email, phone, and address if available.
-   **line_items**:
    -   `item_description`: A clear description of the charge (e.g., "Monthly Rent for Apartment 4B", "Refundable Security Deposit").
    -   `amount`: The numeric value of the charge.
    -   `currency`: The currency code (e.g., "INR", "USD"). Default to "INR" if "Rs." is mentioned.
    -   `category`: The specific category of the charge. A security deposit MUST have the category "deposit".
    -   `billing_cycle`: How often the charge occurs (e.g., "monthly", "one_time").
    -   `due_days`: For recurring charges, the day of the month it's due (e.g., for "due by the 5th of each month", use `5`).

**EXAMPLE PARSING:**
-   Text: "The tenant shall pay a monthly rent of Rs. 5,000 (Rupees Five Thousand) due on the 1st of each month."
-   Line Item: `{{"item_description": "Monthly Rent", "amount": 5000, "currency": "INR", "category": "rent", "billing_cycle": "monthly", "due_days": 1}}`
-   Text: "A security deposit of Rs. 20,000 shall be paid upon signing."
-   Line Item: `{{"item_description": "Security Deposit", "amount": 20000, "currency": "INR", "category": "deposit", "billing_cycle": "one_time", "due_days": null}}`

**IMPORTANT FORMATTING REQUIREMENTS:**
-   Return ONLY a valid JSON object. No introductory text or apologies.
-   Use the exact field names as specified in the JSON structure.
-   Dates must be in YYYY-MM-DD format.
-   Amounts must be decimal numbers, without currency symbols or commas.

**JSON Structure:**
{{
  "contract_title": "string or null",
  "contract_type": "rental_lease",
  "client": {{
    "name": "string or null",
    "email": "email or null",
    "address": "string or null",
    "phone": "string or null",
    "role": "client"
  }},
  "service_provider": {{
    "name": "string or null",
    "email": "email or null", 
    "address": "string or null",
    "phone": "string or null",
    "role": "service_provider"
  }},
  "start_date": "YYYY-MM-DD or null",
  "end_date": "YYYY-MM-DD or null",
  "line_items": [
    {{
      "item_description": "string",
      "amount": "decimal or null",
      "currency": "USD|EUR|INR|GBP",
      "category": "rent|deposit|utility|maintenance_fee|late_fee|other",
      "billing_cycle": "monthly|quarterly|annually|one_time",
      "due_days": "integer or null"
    }}
  ],
  "notes": "string or null"
}}

Contract Text:
{context}'''
            
            model = get_model()
            response = model.generate_content(system_prompt)
            result = response.text
            
            logger.info(f"✅ Extracted invoice data from context")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to extract invoice data: {str(e)}")
            raise
    
    def _parse_invoice_response(self, raw_response: str) -> ContractInvoiceData:
        """Parse LLM response into structured ContractInvoiceData"""
        try:
            # Clean the response to extract the JSON object
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                # If no JSON object is found, assume the whole response is a JSON string
                json_str = raw_response
            
            # Parse JSON
            parsed_data = json.loads(json_str)
            
            # Create ContractInvoiceData object using the parsed data
            invoice_data = ContractInvoiceData(
                **parsed_data,
                confidence_score=0.85, # This could be dynamically assigned by the LLM in the future
                extracted_at=datetime.now()
            )
            
            logger.info("✅ Successfully parsed invoice data into structured format")
            return invoice_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {str(e)}")
            # Return a minimal structure with fallback data to prevent validation errors
            return ContractInvoiceData(
                client=ContractParty(name="Unknown Client", role="client"),
                service_provider=ContractParty(name="Unknown Service Provider", role="service_provider"),
                line_items=[],
                notes=f"Failed to parse structured data from LLM. Raw response: {raw_response[:500]}...",
                confidence_score=0.3,
                extracted_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"❌ Failed to create structured data object: {str(e)}")
            logger.error(f"❌ Parsed data that caused error: {parsed_data}")
            
            # Try to extract what we can from the parsed data before falling back
            try:
                # Extract basic information that usually works
                client_data = parsed_data.get("client", {})
                service_provider_data = parsed_data.get("service_provider", {})
                
                # Clean line items by removing null currency values
                line_items_data = parsed_data.get("line_items", [])
                cleaned_line_items = []
                for item in line_items_data:
                    if item.get("currency") is None:
                        item["currency"] = "USD"  # Set default currency for null values
                    cleaned_line_items.append(item)
                
                # Try to create with cleaned data
                return ContractInvoiceData(
                    contract_title=parsed_data.get("contract_title"),
                    contract_type=parsed_data.get("contract_type"),
                    client=ContractParty(**client_data) if client_data.get("name") else ContractParty(name="Unknown Client", role="client"),
                    service_provider=ContractParty(**service_provider_data) if service_provider_data.get("name") else ContractParty(name="Unknown Service Provider", role="service_provider"),
                    start_date=parsed_data.get("start_date"),
                    end_date=parsed_data.get("end_date"),
                    line_items=[LineItem(**item) for item in cleaned_line_items],
                    notes=parsed_data.get("notes", f"Recovered data after validation error: {str(e)}"),
                    confidence_score=0.7,  # Higher confidence since we recovered the data
                    extracted_at=datetime.now()
                )
            except Exception as recovery_error:
                logger.error(f"❌ Failed to recover data: {str(recovery_error)}")
                # Final fallback to minimal structure
                return ContractInvoiceData(
                    client=ContractParty(name="Unknown Client", role="client"),
                    service_provider=ContractParty(name="Unknown Service Provider", role="service_provider"),
                    line_items=[],
                    notes=f"An error occurred while processing the extracted data: {str(e)}",
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
            system_prompt = f'''You are a contract analysis expert. Answer the user's question based on the contract information provided.

Instructions:
1. Use only information from the provided contract text
2. Be accurate and specific in your response
3. If information is not available, clearly state that
4. Keep responses concise but comprehensive
5. Focus on the contract named: {contract_name}

Contract Information:
{context}

User Question: {query}

Answer:'''
            
            model = get_model()
            response = model.generate_content(system_prompt)
            result = response.text
            
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
