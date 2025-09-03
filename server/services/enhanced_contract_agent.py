import json
import re
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import word2number

from pydantic import BaseModel
from fastapi import HTTPException

from models.llm.base import get_model
from schemas.rental_agreement_schemas import (
    RentalAgreementType, RentalAgreementUnion, RentalAgreementExtractionResult,
    MonthToMonthRentalAgreement, FixedTermRentalAgreement, RentToOwnAgreement,
    StandardResidentialRentalAgreement, ShortTermRentalAgreement, SubleaseAgreement,
    RoomRentalAgreement, CommercialLeaseAgreement, LandLeaseAgreement,
    LeaveAndLicenseAgreement, PayingGuestAgreement, AmountInfo, ContactInfo,
    PropertyInfo, PaymentTerms, PaymentFrequency, PropertyType
)

logger = logging.getLogger(__name__)


class ContractTypeIdentificationAgent:
    """Agent specialized in identifying contract types"""
    
    def __init__(self):
        self.model = get_model()
        self.type_keywords = {
            RentalAgreementType.MONTH_TO_MONTH: [
                "month to month", "monthly tenancy", "periodic tenancy", 
                "30 days notice", "notice to quit"
            ],
            RentalAgreementType.FIXED_TERM: [
                "fixed term", "lease term", "eleven months", "12 months",
                "one year", "two years", "term lease"
            ],
            RentalAgreementType.RENT_TO_OWN: [
                "rent to own", "lease to own", "option to purchase",
                "lease purchase", "rent-to-buy"
            ],
            RentalAgreementType.SHORT_TERM_VACATION: [
                "vacation rental", "short term", "holiday rental",
                "airbnb", "temporary accommodation", "guest house"
            ],
            RentalAgreementType.SUBLEASE: [
                "sublease", "sub-lease", "subletting", "sublet",
                "subtenant", "original tenant"
            ],
            RentalAgreementType.ROOM_RENTAL: [
                "room rental", "single room", "shared accommodation",
                "room sharing", "bedroom rent"
            ],
            RentalAgreementType.COMMERCIAL_LEASE: [
                "commercial lease", "business premises", "office space",
                "shop rent", "commercial property", "retail space"
            ],
            RentalAgreementType.LAND_LEASE: [
                "land lease", "ground lease", "agricultural land",
                "plot rental", "vacant land"
            ],
            RentalAgreementType.LEAVE_AND_LICENSE: [
                "leave and license", "licence agreement", "temporary occupation",
                "licensee", "licensor"
            ],
            RentalAgreementType.PAYING_GUEST: [
                "paying guest", "pg accommodation", "hostel",
                "mess facility", "meals included"
            ]
        }
    
    def identify_contract_type(self, contract_text: str) -> Tuple[RentalAgreementType, float]:
        """
        Identify contract type using both rule-based and LLM approach
        Returns: (contract_type, confidence_score)
        """
        try:
            # Rule-based identification
            rule_based_type, rule_confidence = self._rule_based_identification(contract_text)
            
            # LLM-based identification
            llm_type, llm_confidence = self._llm_based_identification(contract_text)
            
            # Combine results
            if rule_based_type == llm_type:
                final_confidence = min(0.95, (rule_confidence + llm_confidence) / 2 + 0.1)
                return rule_based_type, final_confidence
            elif rule_confidence > llm_confidence:
                return rule_based_type, rule_confidence * 0.8
            else:
                return llm_type, llm_confidence * 0.8
                
        except Exception as e:
            logger.error(f"Error in contract type identification: {e}")
            return RentalAgreementType.STANDARD_RESIDENTIAL, 0.5
    
    def _rule_based_identification(self, text: str) -> Tuple[RentalAgreementType, float]:
        """Rule-based contract type identification"""
        text_lower = text.lower()
        scores = {}
        
        for contract_type, keywords in self.type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            scores[contract_type] = score / len(keywords) if keywords else 0
        
        best_type = max(scores, key=scores.get)
        confidence = min(0.9, scores[best_type] * 2)
        
        return best_type, confidence
    
    def _llm_based_identification(self, text: str) -> Tuple[RentalAgreementType, float]:
        """LLM-based contract type identification"""
        prompt = f"""
You are a contract analysis expert. Analyze the following contract text and identify the specific type of rental/lease agreement.

Contract Types:
1. month_to_month - Month-to-Month Lease (automatic renewal, 30-day notice)
2. fixed_term - Fixed-Term Lease (specific duration like 11/12 months)
3. rent_to_own - Rent-to-Own (option to purchase)
4. standard_residential - Standard Residential Rental
5. short_term_vacation - Short-Term/Vacation Rental
6. sublease - Sublease Agreement
7. room_rental - Room Rental (within larger property)
8. commercial_lease - Commercial Lease (business property)
9. land_lease - Land Lease (land only, no buildings)
10. leave_and_license - Leave and License (Indian, temporary occupation)
11. paying_guest - Paying Guest/PG (includes meals/facilities)

Respond with ONLY a JSON object:
{{
    "contract_type": "one_of_the_above_types",
    "confidence": 0.85,
    "reasoning": "brief explanation"
}}

Contract Text:
{text[:3000]}  # Limit text to avoid token limits
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            contract_type = RentalAgreementType(result.get("contract_type", "standard_residential"))
            confidence = float(result.get("confidence", 0.7))
            
            return contract_type, confidence
            
        except Exception as e:
            logger.error(f"LLM identification error: {e}")
            return RentalAgreementType.STANDARD_RESIDENTIAL, 0.5
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"contract_type": "standard_residential", "confidence": 0.5}
        except:
            return {"contract_type": "standard_residential", "confidence": 0.5}


class AmountParsingAgent:
    """Agent specialized in parsing amounts from text"""
    
    def __init__(self):
        self.currency_patterns = {
            'INR': [r'Rs\.?\s*', r'₹\s*', r'Rupees?\s+', r'INR\s*'],
            'USD': [r'\$\s*', r'USD\s*', r'Dollars?\s+'],
            'EUR': [r'€\s*', r'EUR\s*', r'Euros?\s+']
        }
        
        self.text_to_number_patterns = {
            'thousand': 1000, 'lakh': 100000, 'crore': 10000000,
            'million': 1000000, 'billion': 1000000000
        }
    
    def parse_amount(self, text: str, context: str = "") -> AmountInfo:
        """Parse amount from various text formats"""
        if not text:
            return AmountInfo()
        
        # Clean and normalize text
        clean_text = re.sub(r'\s+', ' ', text.strip())
        
        # Try different parsing strategies
        strategies = [
            self._parse_numeric_with_currency,
            self._parse_written_amount,
            self._parse_mixed_format,
            self._parse_simple_numeric
        ]
        
        best_result = AmountInfo()
        best_confidence = 0
        
        for strategy in strategies:
            try:
                result, confidence = strategy(clean_text, context)
                if confidence > best_confidence:
                    best_result = result
                    best_confidence = confidence
            except Exception as e:
                logger.debug(f"Amount parsing strategy failed: {e}")
                continue
        
        return best_result
    
    def _parse_numeric_with_currency(self, text: str, context: str) -> Tuple[AmountInfo, float]:
        """Parse numeric amounts with currency symbols"""
        for currency, patterns in self.currency_patterns.items():
            for pattern in patterns:
                match = re.search(f'{pattern}([0-9,]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        numeric_value = Decimal(amount_str)
                        return AmountInfo(
                            numeric_value=numeric_value,
                            text_value=text,
                            currency=currency
                        ), 0.9
                    except:
                        continue
        return AmountInfo(), 0.0
    
    def _parse_written_amount(self, text: str, context: str) -> Tuple[AmountInfo, float]:
        """Parse written amounts like 'Four Thousand Rupees'"""
        try:
            # Use word2number library for basic conversion
            number_part = re.sub(r'(rupees?|dollars?|rs\.?|₹|\$)', '', text, flags=re.IGNORECASE).strip()
            numeric_value = word2number.w2n(number_part.lower())
            
            currency = "INR"  # Default
            if any(curr in text.lower() for curr in ['rupees', 'rs.', '₹']):
                currency = "INR"
            elif any(curr in text.lower() for curr in ['dollars', '$', 'usd']):
                currency = "USD"
            
            return AmountInfo(
                numeric_value=Decimal(str(numeric_value)),
                text_value=text,
                currency=currency
            ), 0.85
            
        except Exception:
            return AmountInfo(), 0.0
    
    def _parse_mixed_format(self, text: str, context: str) -> Tuple[AmountInfo, float]:
        """Parse mixed formats like 'Rs.4,000.00 (Rupees Four Thousand)'"""
        # Extract numeric part
        numeric_match = re.search(r'([0-9,]+(?:\.[0-9]+)?)', text)
        if numeric_match:
            try:
                numeric_value = Decimal(numeric_match.group(1).replace(',', ''))
                currency = "INR"  # Default, can be enhanced
                
                return AmountInfo(
                    numeric_value=numeric_value,
                    text_value=text,
                    currency=currency
                ), 0.8
            except:
                pass
        
        return AmountInfo(), 0.0
    
    def _parse_simple_numeric(self, text: str, context: str) -> Tuple[AmountInfo, float]:
        """Parse simple numeric values"""
        numeric_match = re.search(r'([0-9,]+(?:\.[0-9]+)?)', text)
        if numeric_match:
            try:
                numeric_value = Decimal(numeric_match.group(1).replace(',', ''))
                
                # Infer currency from context
                currency = "INR"  # Default
                if "dollar" in context.lower() or "$" in context:
                    currency = "USD"
                
                return AmountInfo(
                    numeric_value=numeric_value,
                    text_value=text,
                    currency=currency
                ), 0.6
            except:
                pass
        
        return AmountInfo(), 0.0


class SpecializedExtractionAgent:
    """Agent that performs specialized extraction based on contract type"""
    
    def __init__(self):
        self.model = get_model()
        self.amount_parser = AmountParsingAgent()
    
    def extract_contract_data(self, 
                            contract_text: str, 
                            contract_type: RentalAgreementType) -> RentalAgreementUnion:
        """Extract data specialized for the identified contract type"""
        
        extraction_methods = {
            RentalAgreementType.MONTH_TO_MONTH: self._extract_month_to_month,
            RentalAgreementType.FIXED_TERM: self._extract_fixed_term,
            RentalAgreementType.RENT_TO_OWN: self._extract_rent_to_own,
            RentalAgreementType.STANDARD_RESIDENTIAL: self._extract_standard_residential,
            RentalAgreementType.SHORT_TERM_VACATION: self._extract_short_term,
            RentalAgreementType.SUBLEASE: self._extract_sublease,
            RentalAgreementType.ROOM_RENTAL: self._extract_room_rental,
            RentalAgreementType.COMMERCIAL_LEASE: self._extract_commercial,
            RentalAgreementType.LAND_LEASE: self._extract_land_lease,
            RentalAgreementType.LEAVE_AND_LICENSE: self._extract_leave_license,
            RentalAgreementType.PAYING_GUEST: self._extract_paying_guest
        }
        
        extraction_method = extraction_methods.get(
            contract_type, 
            self._extract_standard_residential
        )
        
        return extraction_method(contract_text)
    
    def _create_base_prompt(self, contract_type: str, specific_fields: str) -> str:
        """Create base extraction prompt"""
        return f"""
You are an expert in extracting {contract_type} agreement data. Analyze the contract text and extract information in the specified JSON format.

CRITICAL INSTRUCTIONS:
1. Extract amounts in both numeric and text formats where available
2. Parse dates in YYYY-MM-DD format
3. Look for rent amounts in patterns like "Rs.4,000.00 (Rupees Four Thousand)"
4. Extract contact details including names, addresses, phones, emails
5. Identify payment terms, due dates, security deposits
6. Return ONLY valid JSON

{specific_fields}

Contract Text:
"""
    
    def _extract_month_to_month(self, text: str) -> MonthToMonthRentalAgreement:
        """Extract month-to-month rental data"""
        prompt = self._create_base_prompt(
            "month-to-month rental",
            """
JSON Structure:
{
  "landlord": {"name": "str", "address": "str", "phone": "str", "email": "str"},
  "tenant": {"name": "str", "address": "str", "phone": "str", "email": "str"},
  "property_info": {"description": "str", "address": "str", "property_type": "residential|commercial", "size": "str"},
  "payment_terms": {
    "rent_amount": {"numeric_value": 4000.00, "text_value": "Four Thousand", "currency": "INR"},
    "security_deposit": {"numeric_value": 8000.00, "currency": "INR"},
    "due_date": 10,
    "frequency": "monthly"
  },
  "start_date": "2024-01-01",
  "end_date": null,
  "notice_period_days": 30,
  "automatic_renewal": true
}
"""
        )
        
        return self._call_extraction_llm(prompt + text, MonthToMonthRentalAgreement)
    
    def _extract_fixed_term(self, text: str) -> FixedTermRentalAgreement:
        """Extract fixed-term rental data"""
        prompt = self._create_base_prompt(
            "fixed-term rental",
            """
JSON Structure:
{
  "landlord": {"name": "str", "address": "str", "phone": "str", "email": "str"},
  "tenant": {"name": "str", "address": "str", "phone": "str", "email": "str"},
  "property_info": {"description": "str", "address": "str", "property_type": "str", "size": "str"},
  "payment_terms": {
    "rent_amount": {"numeric_value": 0.00, "text_value": "str", "currency": "INR"},
    "security_deposit": {"numeric_value": 0.00, "currency": "INR"},
    "due_date": 10,
    "frequency": "monthly"
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "term_length_months": 11,
  "early_termination_penalty": {"numeric_value": 0.00, "currency": "INR"},
  "lock_in_period": 6
}
"""
        )
        
        return self._call_extraction_llm(prompt + text, FixedTermRentalAgreement)
    
    def _extract_commercial(self, text: str) -> CommercialLeaseAgreement:
        """Extract commercial lease data"""
        prompt = self._create_base_prompt(
            "commercial lease",
            """
JSON Structure:
{
  "landlord": {"name": "str", "business_registration": "str", "address": "str", "phone": "str"},
  "tenant": {"name": "str", "business_registration": "str", "address": "str", "phone": "str"},
  "property_info": {"description": "str", "address": "str", "property_type": "commercial", "size": "str"},
  "payment_terms": {
    "rent_amount": {"numeric_value": 0.00, "currency": "INR"},
    "security_deposit": {"numeric_value": 0.00, "currency": "INR"},
    "maintenance_charges": {"numeric_value": 0.00, "currency": "INR"},
    "due_date": 10,
    "frequency": "monthly"
  },
  "business_name": "str",
  "permitted_use": "str",
  "operating_hours": "str",
  "base_rent": {"numeric_value": 0.00, "currency": "INR"},
  "common_area_maintenance": {"numeric_value": 0.00, "currency": "INR"},
  "start_date": "2024-01-01",
  "end_date": "2027-01-01"
}
"""
        )
        
        return self._call_extraction_llm(prompt + text, CommercialLeaseAgreement)
    
    def _extract_paying_guest(self, text: str) -> PayingGuestAgreement:
        """Extract PG agreement data"""
        prompt = self._create_base_prompt(
            "paying guest (PG)",
            """
JSON Structure:
{
  "landlord": {"name": "str", "address": "str", "phone": "str"},
  "tenant": {"name": "str", "address": "str", "phone": "str"},
  "property_info": {"description": "str", "address": "str", "size": "str"},
  "payment_terms": {
    "rent_amount": {"numeric_value": 0.00, "currency": "INR"},
    "security_deposit": {"numeric_value": 0.00, "currency": "INR"},
    "due_date": 5,
    "frequency": "monthly"
  },
  "meals_included": true,
  "utilities_included": ["electricity", "water", "wifi"],
  "sharing_type": "single occupancy",
  "common_facilities": ["kitchen", "washing machine"],
  "pg_rules": ["no smoking", "no alcohol"],
  "start_date": "2024-01-01"
}
"""
        )
        
        return self._call_extraction_llm(prompt + text, PayingGuestAgreement)
    
    # Add similar methods for other contract types...
    def _extract_standard_residential(self, text: str) -> StandardResidentialRentalAgreement:
        """Fallback extraction for standard residential"""
        prompt = self._create_base_prompt(
            "standard residential rental",
            """
JSON Structure:
{
  "landlord": {"name": "str", "address": "str", "phone": "str", "email": "str"},
  "tenant": {"name": "str", "address": "str", "phone": "str", "email": "str"},
  "property_info": {"description": "str", "address": "str", "property_type": "residential", "size": "str"},
  "payment_terms": {
    "rent_amount": {"numeric_value": 0.00, "text_value": "str", "currency": "INR"},
    "security_deposit": {"numeric_value": 0.00, "currency": "INR"},
    "due_date": 10,
    "frequency": "monthly"
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
"""
        )
        
        return self._call_extraction_llm(prompt + text, StandardResidentialRentalAgreement)
    
    # Simplified implementation for other types - can be expanded
    def _extract_rent_to_own(self, text: str) -> RentToOwnAgreement:
        return self._call_extraction_llm(text, RentToOwnAgreement)
    
    def _extract_short_term(self, text: str) -> ShortTermRentalAgreement:
        return self._call_extraction_llm(text, ShortTermRentalAgreement)
    
    def _extract_sublease(self, text: str) -> SubleaseAgreement:
        return self._call_extraction_llm(text, SubleaseAgreement)
    
    def _extract_room_rental(self, text: str) -> RoomRentalAgreement:
        return self._call_extraction_llm(text, RoomRentalAgreement)
    
    def _extract_land_lease(self, text: str) -> LandLeaseAgreement:
        return self._call_extraction_llm(text, LandLeaseAgreement)
    
    def _extract_leave_license(self, text: str) -> LeaveAndLicenseAgreement:
        return self._call_extraction_llm(text, LeaveAndLicenseAgreement)
    
    def _call_extraction_llm(self, prompt: str, model_class) -> Any:
        """Call LLM for extraction and parse into Pydantic model"""
        try:
            response = self.model.generate_content(prompt)
            json_data = self._parse_json_response(response.text)
            
            # Parse nested AmountInfo objects
            json_data = self._process_amount_fields(json_data)
            
            # Create the model instance with default values
            return model_class(**json_data)
            
        except Exception as e:
            logger.error(f"Extraction LLM call failed: {e}")
            # Return minimal valid instance
            return model_class(
                agreement_type=RentalAgreementType.STANDARD_RESIDENTIAL,
                landlord=ContactInfo(name="Unknown"),
                tenant=ContactInfo(name="Unknown"),
                property_info=PropertyInfo(),
                payment_terms=PaymentTerms()
            )
    
    def _process_amount_fields(self, data: Dict) -> Dict:
        """Process amount fields to create AmountInfo objects"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['rent_amount', 'security_deposit', 'advance_payment', 
                          'maintenance_charges', 'late_fee', 'base_rent', 
                          'common_area_maintenance', 'cleaning_fee', 'license_fee']:
                    if isinstance(value, dict):
                        data[key] = AmountInfo(**value)
                elif isinstance(value, dict):
                    data[key] = self._process_amount_fields(value)
                elif isinstance(value, list):
                    data[key] = [self._process_amount_fields(item) if isinstance(item, dict) else item for item in value]
        return data
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            return {}


class ValidationAgent:
    """Agent for multi-pass validation and confidence scoring"""
    
    def __init__(self):
        self.model = get_model()
    
    def validate_extraction(self, 
                          extracted_data: RentalAgreementUnion, 
                          original_text: str) -> Tuple[RentalAgreementUnion, float, List[str]]:
        """
        Validate extracted data and provide confidence score
        Returns: (validated_data, confidence_score, validation_notes)
        """
        validation_notes = []
        confidence_factors = []
        
        # Validate required fields
        required_confidence = self._validate_required_fields(extracted_data)
        confidence_factors.append(('required_fields', required_confidence))
        
        # Validate amounts
        amount_confidence = self._validate_amounts(extracted_data, original_text)
        confidence_factors.append(('amounts', amount_confidence))
        
        # Validate dates
        date_confidence = self._validate_dates(extracted_data)
        confidence_factors.append(('dates', date_confidence))
        
        # Cross-reference with original text
        text_match_confidence = self._cross_reference_text(extracted_data, original_text)
        confidence_factors.append(('text_match', text_match_confidence))
        
        # Calculate overall confidence
        overall_confidence = sum(weight * score for _, score in confidence_factors) / len(confidence_factors)
        
        # Generate validation notes
        for factor, score in confidence_factors:
            if score < 0.7:
                validation_notes.append(f"Low confidence in {factor} extraction ({score:.2f})")
        
        return extracted_data, overall_confidence, validation_notes
    
    def _validate_required_fields(self, data: RentalAgreementUnion) -> float:
        """Validate that required fields are present"""
        required_fields = ['landlord', 'tenant', 'property_info']
        present_fields = 0
        
        for field in required_fields:
            if hasattr(data, field) and getattr(data, field) is not None:
                field_obj = getattr(data, field)
                if hasattr(field_obj, 'name') and field_obj.name:
                    present_fields += 1
        
        return present_fields / len(required_fields)
    
    def _validate_amounts(self, data: RentalAgreementUnion, text: str) -> float:
        """Validate extracted amounts against original text"""
        # Simple validation - check if rent amount exists and is reasonable
        if hasattr(data, 'payment_terms') and data.payment_terms:
            if hasattr(data.payment_terms, 'rent_amount') and data.payment_terms.rent_amount:
                rent_amount = data.payment_terms.rent_amount
                if hasattr(rent_amount, 'numeric_value') and rent_amount.numeric_value:
                    # Basic sanity check - rent should be positive and reasonable
                    if 100 <= rent_amount.numeric_value <= 1000000:  # Reasonable range
                        return 0.8
                    return 0.4
            return 0.3
        return 0.2
    
    def _validate_dates(self, data: RentalAgreementUnion) -> float:
        """Validate date fields"""
        date_fields = ['start_date', 'end_date', 'agreement_date']
        valid_dates = 0
        total_dates = 0
        
        for field in date_fields:
            if hasattr(data, field):
                date_value = getattr(data, field)
                total_dates += 1
                if isinstance(date_value, date):
                    valid_dates += 1
        
        return valid_dates / total_dates if total_dates > 0 else 0.5
    
    def _cross_reference_text(self, data: RentalAgreementUnion, text: str) -> float:
        """Cross-reference extracted data with original text"""
        matches = 0
        total_checks = 0
        
        # Check if names appear in text
        if hasattr(data, 'landlord') and data.landlord and data.landlord.name:
            total_checks += 1
            if data.landlord.name.lower() in text.lower():
                matches += 1
        
        if hasattr(data, 'tenant') and data.tenant and data.tenant.name:
            total_checks += 1
            if data.tenant.name.lower() in text.lower():
                matches += 1
        
        return matches / total_checks if total_checks > 0 else 0.5


class EnhancedContractProcessingAgent:
    """Main orchestrating agent for contract processing"""
    
    def __init__(self):
        self.type_identification_agent = ContractTypeIdentificationAgent()
        self.extraction_agent = SpecializedExtractionAgent()
        self.validation_agent = ValidationAgent()
        self.amount_parser = AmountParsingAgent()
        
        logger.info("🚀 Enhanced Contract Processing Agent initialized")
    
    def process_contract(self, 
                        contract_text: str, 
                        user_preferences: Optional[Dict] = None) -> RentalAgreementExtractionResult:
        """
        Main processing pipeline with multi-agent workflow
        """
        try:
            logger.info("📋 Starting enhanced contract processing")
            
            # Step 1: Identify contract type
            logger.info("🔍 Identifying contract type...")
            contract_type, type_confidence = self.type_identification_agent.identify_contract_type(contract_text)
            logger.info(f"✅ Identified as {contract_type.value} (confidence: {type_confidence:.2f})")
            
            # Step 2: Specialized extraction
            logger.info("📤 Extracting specialized data...")
            extracted_data = self.extraction_agent.extract_contract_data(contract_text, contract_type)
            logger.info("✅ Data extraction completed")
            
            # Step 3: Validation and confidence scoring
            logger.info("🔬 Validating extracted data...")
            validated_data, validation_confidence, validation_notes = self.validation_agent.validate_extraction(
                extracted_data, contract_text
            )
            logger.info(f"✅ Validation completed (confidence: {validation_confidence:.2f})")
            
            # Step 4: Calculate final confidence
            final_confidence = (type_confidence * 0.3 + validation_confidence * 0.7)
            
            # Step 5: Determine if human review is needed
            requires_review = (
                final_confidence < 0.7 or 
                len(validation_notes) > 2 or
                any("low confidence" in note.lower() for note in validation_notes)
            )
            
            # Create result
            result = RentalAgreementExtractionResult(
                identified_type=contract_type,
                confidence_score=final_confidence,
                agreement_data=validated_data,
                extraction_notes=validation_notes,
                requires_human_review=requires_review,
                extracted_at=datetime.now()
            )
            
            logger.info(f"🎉 Contract processing completed - Final confidence: {final_confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Contract processing failed: {e}")
            # Return minimal result for error cases
            return RentalAgreementExtractionResult(
                identified_type=RentalAgreementType.STANDARD_RESIDENTIAL,
                confidence_score=0.2,
                agreement_data=StandardResidentialRentalAgreement(
                    agreement_type=RentalAgreementType.STANDARD_RESIDENTIAL,
                    landlord=ContactInfo(name="Unknown"),
                    tenant=ContactInfo(name="Unknown"),
                    property_info=PropertyInfo(),
                    payment_terms=PaymentTerms()
                ),
                extraction_notes=[f"Processing error: {str(e)}"],
                requires_human_review=True,
                extracted_at=datetime.now()
            )


# Global service instance
_enhanced_contract_agent = None

def get_enhanced_contract_agent() -> EnhancedContractProcessingAgent:
    """Get singleton enhanced contract processing agent"""
    global _enhanced_contract_agent
    if _enhanced_contract_agent is None:
        _enhanced_contract_agent = EnhancedContractProcessingAgent()
    return _enhanced_contract_agent