"""
Natural Language Correction Service

This service processes natural language queries to extract missing invoice fields
instead of requiring users to fill out structured forms.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from services.llm_service import get_llm_service
from schemas.unified_invoice_schemas import UnifiedInvoiceData, PartyRole, CurrencyCode, InvoiceFrequency

logger = logging.getLogger(__name__)


class NaturalLanguageCorrectionService:
    """Service for processing natural language corrections to invoice data"""
    
    def __init__(self):
        # Use proper Vertex AI text generation model instead of embedding-only service
        from models.llm.base import get_model
        self.model = get_model(model_name="gemini-1.5-pro", temperature=0.1)
    
    async def process_natural_language_query(
        self,
        query: str,
        current_invoice_data: UnifiedInvoiceData,
        missing_fields: List[str],
        validation_issues: List[str]
    ) -> Dict[str, Any]:
        """
        Process a natural language query to extract missing invoice fields
        
        Args:
            query: Natural language input from user
            current_invoice_data: Current invoice data with missing fields
            missing_fields: List of fields that need to be filled
            validation_issues: List of validation issues to address
            
        Returns:
            Dictionary of field corrections to apply
        """
        logger.info(f"🗣️ Processing natural language query: '{query[:100]}...'")
        
        try:
            # Create context for LLM
            context = self._build_context(current_invoice_data, missing_fields, validation_issues)
            logger.info(f"📋 Built context with {len(missing_fields)} missing fields")
            
            # Generate extraction prompt
            prompt = self._create_extraction_prompt(query, context, missing_fields)
            logger.info(f"📝 Generated extraction prompt ({len(prompt)} chars)")
            
            # Use Vertex AI model to extract structured data from query
            logger.info("🤖 Calling LLM for field extraction...")
            response = self.model.generate_content(prompt)
            
            # Parse LLM response into corrections
            response_text = response.text if hasattr(response, 'text') else str(response)
            logger.info(f"📥 LLM response received ({len(response_text)} chars)")
            logger.debug(f"🔍 Raw LLM response: {response_text[:500]}...")
            
            corrections = self._parse_llm_response(response_text, missing_fields)
            logger.info(f"🧩 Parsed {len(corrections)} raw corrections from LLM")
            
            # Validate and clean corrections
            validated_corrections = self._validate_corrections(corrections, missing_fields)
            logger.info(f"✅ Validated {len(validated_corrections)} field corrections")
            
            # Log each validated correction
            for field, value in validated_corrections.items():
                logger.info(f"   🔸 {field} → {value}")
            
            confidence = self._calculate_confidence(validated_corrections, missing_fields)
            logger.info(f"📊 Extraction confidence: {confidence:.2f}")
            
            return {
                "success": True,
                "corrections": validated_corrections,
                "original_query": query,
                "extraction_confidence": confidence,
                "raw_response": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process natural language query: {str(e)}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "corrections": {},
                "original_query": query
            }
    
    def _build_context(self, current_data: UnifiedInvoiceData, missing_fields: List[str], issues: List[str]) -> Dict[str, Any]:
        """Build context information for LLM prompt"""
        # Get service description from first service item if available
        current_service_description = None
        if current_data.services and len(current_data.services) > 0:
            current_service_description = current_data.services[0].description
        
        return {
            "current_client_name": current_data.client.name if current_data.client else None,
            "current_service_provider_name": current_data.service_provider.name if current_data.service_provider else None,
            "current_amount": str(current_data.payment_terms.amount) if current_data.payment_terms and current_data.payment_terms.amount else None,
            "current_currency": current_data.payment_terms.currency if current_data.payment_terms else "USD",
            "current_frequency": current_data.payment_terms.frequency if current_data.payment_terms else None,
            "current_service_description": current_service_description,
            "missing_fields": missing_fields,
            "validation_issues": issues
        }
    
    def _create_extraction_prompt(self, query: str, context: Dict[str, Any], missing_fields: List[str]) -> str:
        """Create LLM prompt for field extraction"""
        
        field_descriptions = {
            # Party information
            "client.name": "The client's or customer's name",
            "client.email": "The client's email address",
            "client.address": "The client's address",
            "client.phone": "The client's phone number",
            "service_provider.name": "The service provider's or company's name",
            "service_provider.email": "The service provider's email",
            "service_provider.address": "The service provider's address",
            # Payment information
            "payment_terms.amount": "The payment amount or price (number only)",
            "payment_terms.currency": "The currency code (USD, EUR, etc.)",
            "payment_terms.frequency": "Payment frequency (monthly, quarterly, annually, one_time)",
            "payment_terms.due_days": "Number of days until payment is due",
            # Service information
            "services.0.description": "Description of the service or product",
            "services.0.quantity": "Quantity of the service (number)",
            "services.0.unit_price": "Unit price per service (number)",
            # Contract dates and info
            "start_date": "Contract/service start date",
            "end_date": "Contract/service end date",
            "contract_title": "Title or name of the contract",
            # Invoice frequency mapping
            "invoice_frequency": "How often invoices are generated (monthly, quarterly, annually, one_time)"
        }
        
        prompt = f"""
You are an AI assistant that extracts invoice information from natural language queries.

USER QUERY: "{query}"

CONTEXT:
Current invoice data has these values:
- Client Name: {context.get('current_client_name', 'NOT SET')}
- Service Provider Name: {context.get('current_service_provider_name', 'NOT SET')}
- Payment Amount: {context.get('current_amount', 'NOT SET')}
- Currency: {context.get('current_currency', 'NOT SET')}
- Service Description: {context.get('current_service_description', 'NOT SET')}

MISSING FIELDS THAT NEED TO BE FILLED:
{chr(10).join([f"- {field}: {field_descriptions.get(field, 'Unknown field')}" for field in missing_fields])}

TASK:
Extract values from the user query for the missing fields listed above. Only extract information that is clearly stated in the query.

RESPONSE FORMAT:
Return a JSON object with field paths as keys and extracted values as values. Use these exact field paths:
{json.dumps(list(field_descriptions.keys()), indent=2)}

EXAMPLE RESPONSE:
{{
    "client.name": "John Smith",
    "service_provider.name": "TechCorp LLC",
    "payment_terms.amount": "1500.00",
    "payment_terms.currency": "USD",
    "payment_terms.frequency": "monthly",
    "services.0.description": "Web development services"
}}

IMPORTANT RULES:
1. Only include fields that are explicitly mentioned in the user query
2. Use exact field path names from the list above
3. For amounts, extract only the numeric value (e.g., "1500.00" not "$1,500")
4. For currencies, use 3-letter codes (USD, EUR, etc.)
5. For frequencies, use: monthly, quarterly, annually, weekly, daily, one_time
6. If information is unclear or not mentioned, don't include that field
7. Return valid JSON only, no additional text

EXTRACT THE INFORMATION:
"""

        return prompt
    
    def _parse_llm_response(self, response: str, missing_fields: List[str]) -> Dict[str, Any]:
        """Parse LLM response to extract corrections"""
        try:
            # Clean response - remove any text before/after JSON
            response = response.strip()
            
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            # Parse JSON
            corrections = json.loads(json_str)
            
            # Filter to only missing fields
            filtered_corrections = {}
            for field in missing_fields:
                if field in corrections and corrections[field]:
                    filtered_corrections[field] = corrections[field]
            
            return filtered_corrections
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            
            # Fallback: try to extract using regex patterns
            return self._fallback_extraction(response, missing_fields)
    
    def _fallback_extraction(self, text: str, missing_fields: List[str]) -> Dict[str, Any]:
        """Fallback extraction using regex patterns"""
        corrections = {}
        text_lower = text.lower()
        
        # Common patterns for different field types
        patterns = {
            "client.name": [
                r"client(?:\s+is|\s+name(?:\s+is)?)(?:\s+)([A-Za-z\s]+?)(?:\s+and|\s+,|\.|\n|$)",
                r"customer(?:\s+is|\s+name(?:\s+is)?)(?:\s+)([A-Za-z\s]+?)(?:\s+and|\s+,|\.|\n|$)"
            ],
            "service_provider.name": [
                r"service provider(?:\s+is|\s+name(?:\s+is)?)(?:\s+)([A-Za-z\s]+?)(?:\s+and|\s+,|\.|\n|$)",
                r"provider(?:\s+is|\s+name(?:\s+is)?)(?:\s+)([A-Za-z\s]+?)(?:\s+and|\s+,|\.|\n|$)",
                r"company(?:\s+is|\s+name(?:\s+is)?)(?:\s+)([A-Za-z\s]+?)(?:\s+and|\s+,|\.|\n|$)"
            ],
            "payment_terms.amount": [
                r"amount(?:\s+is)?(?:\s+)[\$]?(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"fee(?:\s+is)?(?:\s+)[\$]?(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"cost(?:\s+is)?(?:\s+)[\$]?(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"[\$](\d+(?:,\d{3})*(?:\.\d{2})?)"
            ],
            "payment_terms.frequency": [
                r"(monthly|quarterly|annually|weekly|daily|one[_\s]time)",
                r"every\s+(month|quarter|year|week|day)"
            ],
            "services.0.description": [
                r"for\s+([a-zA-Z\s]+?)(?:\s+starting|\s+beginning|\.|\n|$)",
                r"services?\s+(?:include\s+|are\s+)?([a-zA-Z\s]+?)(?:\s+starting|\s+beginning|\.|\n|$)"
            ]
        }
        
        for field in missing_fields:
            if field in patterns:
                for pattern in patterns[field]:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        
                        # Clean up the value
                        if field == "payment_terms.amount":
                            value = value.replace(",", "")
                        elif field == "payment_terms.frequency":
                            if value in ["month", "monthly"]:
                                value = "monthly"
                            elif value in ["quarter", "quarterly"]:
                                value = "quarterly"
                            elif value in ["year", "annually"]:
                                value = "annually"
                        
                        corrections[field] = value
                        break
        
        return corrections
    
    def _validate_corrections(self, corrections: Dict[str, Any], missing_fields: List[str]) -> Dict[str, Any]:
        """Validate and clean extracted corrections"""
        validated = {}
        
        for field, value in corrections.items():
            if field not in missing_fields:
                continue
                
            # Clean and validate based on field type
            if field.endswith(".amount"):
                try:
                    # Convert to decimal, handle various formats
                    clean_value = str(value).replace("$", "").replace(",", "").strip()
                    decimal_value = Decimal(clean_value)
                    validated[field] = str(decimal_value)
                except:
                    logger.warning(f"Invalid amount value: {value}")
                    
            elif field.endswith(".currency"):
                currency_value = str(value).upper().strip()
                if len(currency_value) == 3:
                    validated[field] = currency_value
                    
            elif field.endswith(".frequency") or field == "invoice_frequency":
                freq_value = str(value).lower().strip().replace(" ", "_")
                # Map various frequency formats to standard values
                frequency_mapping = {
                    "month": "monthly", "monthly": "monthly", "per month": "monthly", "every month": "monthly",
                    "quarter": "quarterly", "quarterly": "quarterly", "per quarter": "quarterly", "every quarter": "quarterly",
                    "year": "annually", "annual": "annually", "annually": "annually", "yearly": "annually", "per year": "annually", "every year": "annually",
                    "week": "weekly", "weekly": "weekly", "per week": "weekly", "every week": "weekly",
                    "day": "daily", "daily": "daily", "per day": "daily", "every day": "daily",
                    "once": "one_time", "one time": "one_time", "onetime": "one_time", "one_time": "one_time",
                    "biannual": "biannually", "biannually": "biannually", "twice yearly": "biannually"
                }
                mapped_freq = frequency_mapping.get(freq_value, freq_value)
                if mapped_freq in ["monthly", "quarterly", "annually", "weekly", "daily", "one_time", "biannually"]:
                    validated[field] = mapped_freq
                    
            elif field.endswith(".name") or field.endswith(".description"):
                name_value = str(value).strip()
                if name_value and len(name_value) > 1:
                    validated[field] = name_value
                    
            elif field.endswith(".email"):
                email_value = str(value).strip()
                if "@" in email_value and "." in email_value:
                    validated[field] = email_value
                    
            else:
                # Default: include if non-empty
                string_value = str(value).strip()
                if string_value:
                    validated[field] = string_value
        
        return validated
    
    def _calculate_confidence(self, corrections: Dict[str, Any], missing_fields: List[str]) -> float:
        """Calculate confidence score based on how many missing fields were filled"""
        if not missing_fields:
            return 1.0
        
        filled_count = len(corrections)
        total_count = len(missing_fields)
        
        return round(filled_count / total_count, 2)
    
    async def preview_corrections(self, query: str, current_invoice_data: UnifiedInvoiceData) -> Dict[str, Any]:
        """Preview what would be extracted from a query without applying changes"""
        
        # Mock missing fields for preview
        mock_missing_fields = ["client.name", "service_provider.name", "payment_terms.amount", "service_details.description"]
        
        result = await self.process_natural_language_query(
            query=query,
            current_invoice_data=current_invoice_data,
            missing_fields=mock_missing_fields,
            validation_issues=[]
        )
        
        return {
            "preview": True,
            "query": query,
            "extracted_fields": result.get("corrections", {}),
            "confidence": result.get("extraction_confidence", 0.0),
            "success": result.get("success", False)
        }


# Singleton instance
_natural_language_service = None

def get_natural_language_correction_service() -> NaturalLanguageCorrectionService:
    """Get singleton instance of natural language correction service"""
    global _natural_language_service
    if _natural_language_service is None:
        _natural_language_service = NaturalLanguageCorrectionService()
    return _natural_language_service