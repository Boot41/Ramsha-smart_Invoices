from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from enum import Enum
from dataclasses import dataclass
from schemas.contract_schemas import ContractInvoiceData
from schemas.unified_invoice_schemas import UnifiedInvoiceData
from schemas.workflow_schemas import ProcessingStatus

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"          # Must be fixed before proceeding
    WARNING = "warning"      # Should be reviewed but can proceed
    INFO = "info"           # Nice to have, informational only

class FieldType(Enum):
    """Types of fields for validation"""
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    DATE = "date"
    CURRENCY = "currency"
    PHONE = "phone"

@dataclass
class ValidationIssue:
    """Represents a validation issue found in the data"""
    field_name: str
    issue_type: str
    severity: ValidationSeverity
    message: str
    current_value: Any
    suggested_value: Optional[Any] = None
    requires_human_input: bool = False

@dataclass
class ValidationResult:
    """Result of validation process"""
    is_valid: bool
    validation_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    missing_required_fields: List[str]
    human_input_required: bool
    confidence_score: float
    validation_timestamp: str

class InvoiceDataValidationService:
    """Service for validating extracted invoice data and handling human-in-the-loop"""
    
    def __init__(self):
        self.required_fields = self._define_required_fields()
        self.field_validators = self._setup_field_validators()
        self.logger = logging.getLogger(__name__)
    
    def _define_required_fields(self) -> Dict[str, Dict[str, Any]]:
        """Define required fields for invoice data validation"""
        return {
            # Client information
            "client.name": {
                "type": FieldType.TEXT,
                "required": True,
                "description": "Client/tenant name",
                "validation_rules": {"min_length": 2, "max_length": 100}
            },
            
            # Service provider information
            "service_provider.name": {
                "type": FieldType.TEXT,
                "required": True,
                "description": "Service provider/landlord name",
                "validation_rules": {"min_length": 2, "max_length": 100}
            },
            
            # Payment information
            "payment_terms.amount": {
                "type": FieldType.CURRENCY,
                "required": True,
                "description": "Main payment amount (rent/service fee)",
                "validation_rules": {"min_value": 0, "max_value": 1000000}
            },
            
            "payment_terms.currency": {
                "type": FieldType.TEXT,
                "required": True,
                "description": "Currency code (USD, EUR, INR, etc.)",
                "validation_rules": {"allowed_values": ["USD", "EUR", "INR", "GBP", "CAD", "AUD"]}
            },
            
            "payment_terms.frequency": {
                "type": FieldType.TEXT,
                "required": True,
                "description": "Payment frequency",
                "validation_rules": {"allowed_values": ["monthly", "quarterly", "annually", "biannually", "weekly", "one_time"]}
            },
            
            # Contract information
            "contract_type": {
                "type": FieldType.TEXT,
                "required": False,
                "description": "Type of contract",
                "validation_rules": {"allowed_values": ["rental_lease", "service_agreement", "consulting_agreement", "maintenance_contract", "supply_contract", "other"]}
            },
            
            # Optional but recommended fields
            "client.email": {
                "type": FieldType.EMAIL,
                "required": False,
                "description": "Client email address",
                "validation_rules": {"format": "email"}
            },
            
            "service_provider.email": {
                "type": FieldType.EMAIL,
                "required": False,
                "description": "Service provider email address",
                "validation_rules": {"format": "email"}
            },
            
            "start_date": {
                "type": FieldType.DATE,
                "required": False,
                "description": "Contract start date",
                "validation_rules": {"format": "YYYY-MM-DD"}
            },
            
            "payment_terms.due_days": {
                "type": FieldType.NUMBER,
                "required": False,
                "description": "Payment due day of month",
                "validation_rules": {"min_value": 1, "max_value": 31}
            }
        }
    
    def _setup_field_validators(self) -> Dict[FieldType, callable]:
        """Setup field type validators"""
        return {
            FieldType.TEXT: self._validate_text_field,
            FieldType.NUMBER: self._validate_number_field,
            FieldType.EMAIL: self._validate_email_field,
            FieldType.DATE: self._validate_date_field,
            FieldType.CURRENCY: self._validate_currency_field,
            FieldType.PHONE: self._validate_phone_field
        }
    
    def validate_invoice_data(self, invoice_data: ContractInvoiceData, user_id: str, contract_name: str) -> ValidationResult:
        """
        Validate extracted invoice data for completeness and correctness
        
        Args:
            invoice_data: The extracted invoice data to validate
            user_id: User ID for logging/tracking
            contract_name: Contract name for context
            
        Returns:
            ValidationResult with validation status and issues
        """
        self.logger.info(f"🔍 Starting validation for contract: {contract_name}")
        
        issues = []
        missing_required_fields = []
        validation_score = 1.0
        
        # Convert invoice data to dict for easier validation
        data_dict = self._invoice_data_to_dict(invoice_data)
        self.logger.debug(f"Converted data dict keys: {list(data_dict.keys()) if data_dict else 'None'}")
        
        # Validate required fields
        for field_path, field_config in self.required_fields.items():
            field_value = self._get_nested_field(data_dict, field_path)
            
            self.logger.debug(f"Validating field {field_path}: value={field_value}, required={field_config['required']}")
            
            if field_config["required"] and (field_value is None or field_value == ""):
                missing_required_fields.append(field_path)
                issues.append(ValidationIssue(
                    field_name=field_path,
                    issue_type="missing_required",
                    severity=ValidationSeverity.ERROR,
                    message=f"Required field '{field_path}' is missing: {field_config['description']}",
                    current_value=field_value,
                    requires_human_input=True
                ))
                validation_score -= 0.15  # Significant penalty for missing required fields
                self.logger.debug(f"Missing required field {field_path}, score now: {validation_score:.2f}")
            
            elif field_value is not None and field_value != "":
                # Validate field format/content
                validation_issue = self._validate_field_content(field_path, field_value, field_config)
                if validation_issue:
                    issues.append(validation_issue)
                    if validation_issue.severity == ValidationSeverity.ERROR:
                        validation_score -= 0.10
                    elif validation_issue.severity == ValidationSeverity.WARNING:
                        validation_score -= 0.05
                    self.logger.debug(f"Validation issue for {field_path}: {validation_issue.message}")
        
        # Additional business logic validations
        business_issues = self._perform_business_validation(data_dict)
        issues.extend(business_issues)
        
        # Calculate final scores
        validation_score = max(0.0, validation_score)  # Don't go below 0
        
        # Determine validity - data is valid if:
        # 1. No missing required fields AND
        # 2. No ERROR severity issues AND  
        # 3. Validation score meets minimum threshold
        is_valid = (
            len(missing_required_fields) == 0 and 
            all(issue.severity != ValidationSeverity.ERROR for issue in issues) and
            validation_score >= 0.6  # Minimum score threshold for validity
        )
        
        # Determine human input requirement more intelligently
        human_input_required = self._determine_human_input_required(
            missing_required_fields, issues, validation_score
        )
        
        self.logger.debug(f"Validation results - Score: {validation_score:.2f}, Valid: {is_valid}, Human input: {human_input_required}")
        
        # Calculate confidence based on completeness and validation issues
        confidence_score = self._calculate_confidence_score(data_dict, issues)
        
        result = ValidationResult(
            is_valid=is_valid,
            validation_score=validation_score,
            issues=issues,
            missing_required_fields=missing_required_fields,
            human_input_required=human_input_required,
            confidence_score=confidence_score,
            validation_timestamp=datetime.now().isoformat()
        )
        
        self.logger.info(f"✅ Validation completed - Valid: {is_valid}, Score: {validation_score:.2f}, Confidence: {confidence_score:.2f}, Issues: {len(issues)}, Missing fields: {len(missing_required_fields)}, Human input required: {human_input_required}")
        if missing_required_fields:
            self.logger.info(f"Missing required fields: {missing_required_fields}")
        if issues:
            self.logger.info(f"Issues found: {[f'{i.field_name}: {i.message}' for i in issues[:3]]}{' ...' if len(issues) > 3 else ''}")
        
        return result
    
    def _invoice_data_to_dict(self, invoice_data: ContractInvoiceData) -> Dict[str, Any]:
        """Convert ContractInvoiceData to nested dictionary for easier validation"""
        try:
            return invoice_data.model_dump()
        except AttributeError:
            # Handle case where it might be a dict already
            if isinstance(invoice_data, dict):
                return invoice_data
            else:
                raise ValueError(f"Invalid invoice data format: {type(invoice_data)}")
    
    def _get_nested_field(self, data_dict: Dict[str, Any], field_path: str) -> Any:
        """Get nested field value using dot notation (e.g., 'client.name')"""
        keys = field_path.split('.')
        value = data_dict
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _validate_field_content(self, field_path: str, field_value: Any, field_config: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Validate individual field content based on its type and rules"""
        field_type = field_config["type"]
        validation_rules = field_config.get("validation_rules", {})
        
        validator = self.field_validators.get(field_type)
        if validator:
            return validator(field_path, field_value, validation_rules, field_config["description"])
        
        return None
    
    def _validate_text_field(self, field_path: str, value: Any, rules: Dict, description: str) -> Optional[ValidationIssue]:
        """Validate text fields"""
        if not isinstance(value, str):
            return ValidationIssue(
                field_name=field_path,
                issue_type="invalid_type",
                severity=ValidationSeverity.ERROR,
                message=f"Field '{field_path}' should be text, got {type(value).__name__}",
                current_value=value,
                requires_human_input=True
            )
        
        # Check length constraints
        if "min_length" in rules and len(value.strip()) < rules["min_length"]:
            return ValidationIssue(
                field_name=field_path,
                issue_type="too_short",
                severity=ValidationSeverity.WARNING,
                message=f"Field '{field_path}' is too short (minimum {rules['min_length']} characters)",
                current_value=value,
                requires_human_input=True
            )
        
        if "max_length" in rules and len(value) > rules["max_length"]:
            return ValidationIssue(
                field_name=field_path,
                issue_type="too_long",
                severity=ValidationSeverity.WARNING,
                message=f"Field '{field_path}' is too long (maximum {rules['max_length']} characters)",
                current_value=value,
                requires_human_input=False  # Auto-truncation possible
            )
        
        # Check allowed values - be more lenient for better automation
        if "allowed_values" in rules:
            # Check exact matches first (case-insensitive)
            if value.lower().strip() not in [v.lower() for v in rules["allowed_values"]]:
                # Try to find close matches
                suggested = self._suggest_closest_value(value, rules["allowed_values"])
                # Only require human input if the suggestion is very different
                similarity_threshold = 0.6
                requires_human = not self._strings_similar(value, suggested, similarity_threshold)
                
                return ValidationIssue(
                    field_name=field_path,
                    issue_type="invalid_value",
                    severity=ValidationSeverity.WARNING if not requires_human else ValidationSeverity.ERROR,
                    message=f"Field '{field_path}' has unexpected value. Allowed: {rules['allowed_values']}",
                    current_value=value,
                    suggested_value=suggested,
                    requires_human_input=requires_human
                )
        
        return None
    
    def _strings_similar(self, str1: str, str2: str, threshold: float = 0.6) -> bool:
        """Check if two strings are similar enough"""
        if not str1 or not str2:
            return False
        
        str1_lower = str1.lower().strip()
        str2_lower = str2.lower().strip()
        
        # Exact match
        if str1_lower == str2_lower:
            return True
        
        # Substring match
        if str1_lower in str2_lower or str2_lower in str1_lower:
            return True
        
        # Character overlap similarity
        set1, set2 = set(str1_lower), set(str2_lower)
        overlap = len(set1 & set2)
        union = len(set1 | set2)
        similarity = overlap / union if union > 0 else 0
        
        return similarity >= threshold
    
    def _validate_number_field(self, field_path: str, value: Any, rules: Dict, description: str) -> Optional[ValidationIssue]:
        """Validate numeric fields"""
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return ValidationIssue(
                    field_name=field_path,
                    issue_type="invalid_type",
                    severity=ValidationSeverity.ERROR,
                    message=f"Field '{field_path}' should be a number, got {type(value).__name__}",
                    current_value=value,
                    requires_human_input=True
                )
        
        # Check range constraints
        if "min_value" in rules and value < rules["min_value"]:
            return ValidationIssue(
                field_name=field_path,
                issue_type="value_too_low",
                severity=ValidationSeverity.WARNING,
                message=f"Field '{field_path}' is below minimum value ({rules['min_value']})",
                current_value=value,
                requires_human_input=True
            )
        
        if "max_value" in rules and value > rules["max_value"]:
            return ValidationIssue(
                field_name=field_path,
                issue_type="value_too_high",
                severity=ValidationSeverity.WARNING,
                message=f"Field '{field_path}' exceeds maximum value ({rules['max_value']})",
                current_value=value,
                requires_human_input=True
            )
        
        return None
    
    def _validate_currency_field(self, field_path: str, value: Any, rules: Dict, description: str) -> Optional[ValidationIssue]:
        """Validate currency amount fields"""
        return self._validate_number_field(field_path, value, rules, description)
    
    def _validate_email_field(self, field_path: str, value: Any, rules: Dict, description: str) -> Optional[ValidationIssue]:
        """Validate email fields"""
        import re
        
        if not isinstance(value, str):
            return ValidationIssue(
                field_name=field_path,
                issue_type="invalid_type",
                severity=ValidationSeverity.ERROR,
                message=f"Email field '{field_path}' should be text",
                current_value=value,
                requires_human_input=True
            )
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return ValidationIssue(
                field_name=field_path,
                issue_type="invalid_format",
                severity=ValidationSeverity.WARNING,
                message=f"Field '{field_path}' doesn't appear to be a valid email address",
                current_value=value,
                requires_human_input=True
            )
        
        return None
    
    def _validate_date_field(self, field_path: str, value: Any, rules: Dict, description: str) -> Optional[ValidationIssue]:
        """Validate date fields"""
        if isinstance(value, str):
            try:
                # Try to parse various date formats
                from dateutil.parser import parse
                parsed_date = parse(value)
                # Convert to standard format if valid
                return None
            except:
                return ValidationIssue(
                    field_name=field_path,
                    issue_type="invalid_date_format",
                    severity=ValidationSeverity.WARNING,
                    message=f"Field '{field_path}' doesn't appear to be a valid date",
                    current_value=value,
                    suggested_value="YYYY-MM-DD format recommended",
                    requires_human_input=True
                )
        
        return None
    
    def _validate_phone_field(self, field_path: str, value: Any, rules: Dict, description: str) -> Optional[ValidationIssue]:
        """Validate phone number fields"""
        import re
        
        if not isinstance(value, str):
            return ValidationIssue(
                field_name=field_path,
                issue_type="invalid_type",
                severity=ValidationSeverity.ERROR,
                message=f"Phone field '{field_path}' should be text",
                current_value=value,
                requires_human_input=True
            )
        
        # Basic phone validation - allows various formats
        phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'  # Very basic international format
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', value)  # Remove common separators
        
        if not re.match(phone_pattern, cleaned_phone):
            return ValidationIssue(
                field_name=field_path,
                issue_type="invalid_format",
                severity=ValidationSeverity.WARNING,
                message=f"Field '{field_path}' doesn't appear to be a valid phone number",
                current_value=value,
                requires_human_input=True
            )
        
        return None
    
    def _perform_business_validation(self, data_dict: Dict[str, Any]) -> List[ValidationIssue]:
        """Perform business logic validations"""
        issues = []
        
        # Check if client and service provider are different
        client_name = self._get_nested_field(data_dict, "client.name")
        provider_name = self._get_nested_field(data_dict, "service_provider.name")
        
        if client_name and provider_name and client_name.lower().strip() == provider_name.lower().strip():
            issues.append(ValidationIssue(
                field_name="client.name",
                issue_type="duplicate_entity",
                severity=ValidationSeverity.WARNING,
                message="Client and service provider appear to be the same entity",
                current_value=client_name,
                requires_human_input=False
            ))
        
        # Check payment amount reasonableness
        amount = self._get_nested_field(data_dict, "payment_terms.amount")
        currency = self._get_nested_field(data_dict, "payment_terms.currency")
        
        if amount and currency:
            # Basic reasonableness checks based on currency
            currency_ranges = {
                "USD": {"min": 10, "max": 50000, "typical_max": 10000},
                "EUR": {"min": 10, "max": 45000, "typical_max": 9000},
                "INR": {"min": 500, "max": 2000000, "typical_max": 500000},
                "GBP": {"min": 10, "max": 40000, "typical_max": 8000}
            }
            
            if currency in currency_ranges:
                range_info = currency_ranges[currency]
                if amount < range_info["min"]:
                    issues.append(ValidationIssue(
                        field_name="payment_terms.amount",
                        issue_type="unusually_low",
                        severity=ValidationSeverity.INFO,
                        message=f"Payment amount seems unusually low for {currency}",
                        current_value=amount,
                        requires_human_input=False
                    ))
                elif amount > range_info["typical_max"]:
                    issues.append(ValidationIssue(
                        field_name="payment_terms.amount",
                        issue_type="unusually_high",
                        severity=ValidationSeverity.INFO,
                        message=f"Payment amount seems unusually high for {currency} - please verify",
                        current_value=amount,
                        requires_human_input=False
                    ))
        
        return issues
    
    def _suggest_closest_value(self, current_value: str, allowed_values: List[str]) -> str:
        """Suggest the closest allowed value using simple string similarity"""
        if not current_value or not allowed_values:
            return allowed_values[0] if allowed_values else ""
        
        current_lower = current_value.lower()
        best_match = allowed_values[0]
        best_score = 0
        
        for allowed in allowed_values:
            allowed_lower = allowed.lower()
            # Simple substring matching
            if current_lower in allowed_lower or allowed_lower in current_lower:
                score = len(set(current_lower) & set(allowed_lower)) / len(set(current_lower) | set(allowed_lower))
                if score > best_score:
                    best_score = score
                    best_match = allowed
        
        return best_match
    
    def _determine_human_input_required(self, missing_fields: List[str], issues: List[ValidationIssue], validation_score: float) -> bool:
        """Determine if human input is required based on validation results"""
        
        # Always require human input for missing required fields
        if missing_fields:
            return True
        
        # Require human input for critical errors that need human review
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR and i.requires_human_input]
        if critical_issues:
            return True
        
        # For high quality data with good scores, don't require human input
        if validation_score >= 0.8 and len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0:
            return False
        
        # For medium quality data with only warnings, allow automated processing
        if validation_score >= 0.6 and all(i.severity != ValidationSeverity.ERROR for i in issues):
            # Only require human input if warnings specifically request it
            warning_human_required = [i for i in issues if i.severity == ValidationSeverity.WARNING and i.requires_human_input]
            return len(warning_human_required) > 0
            
        # For lower quality data, require human review
        return True
    
    def _calculate_confidence_score(self, data_dict: Dict[str, Any], issues: List[ValidationIssue]) -> float:
        """Calculate confidence score based on data completeness and validation issues"""
        
        # If no data at all, return 0
        if not data_dict:
            self.logger.debug("Empty data dict - confidence score: 0.0")
            return 0.0
            
        base_confidence = 0.3  # Start with higher base for existing data
        
        # Count all fields that have values
        total_fields = len(self.required_fields)
        filled_fields = 0
        required_filled = 0
        total_required = 0
        
        for field_path, field_config in self.required_fields.items():
            value = self._get_nested_field(data_dict, field_path)
            has_value = value is not None and str(value).strip()
            
            if has_value:
                filled_fields += 1
                
            if field_config["required"]:
                total_required += 1
                if has_value:
                    required_filled += 1
        
        # Required fields completeness contributes 40% to confidence
        if total_required > 0:
            required_completeness = required_filled / total_required
            base_confidence += required_completeness * 0.4
        
        # Overall field completeness contributes 20% to confidence
        if total_fields > 0:
            overall_completeness = filled_fields / total_fields
            base_confidence += overall_completeness * 0.2
        
        # Reduce confidence based on validation issues
        error_penalty = sum(0.15 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_penalty = sum(0.05 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        
        base_confidence = max(0.0, base_confidence - error_penalty - warning_penalty)
        
        self.logger.debug(f"Confidence calculation - Required: {required_filled}/{total_required}, Total: {filled_fields}/{total_fields}, Errors: {error_penalty:.2f}, Warnings: {warning_penalty:.2f}, Final: {base_confidence:.2f}")
        
        return min(1.0, base_confidence)
    
    def create_human_input_request(self, validation_result: ValidationResult, user_id: str, contract_name: str) -> Dict[str, Any]:
        """
        Create a structured request for human input to resolve validation issues
        
        Args:
            validation_result: Result from validation
            user_id: User ID
            contract_name: Contract name
            
        Returns:
            Dictionary with human input request details
        """
        human_input_issues = [issue for issue in validation_result.issues if issue.requires_human_input]
        
        request = {
            "user_id": user_id,
            "contract_name": contract_name,
            "validation_timestamp": validation_result.validation_timestamp,
            "status": "pending_human_input",
            "priority": "high" if validation_result.missing_required_fields else "medium",
            "required_actions": [],
            "suggestions": [],
            "context": {
                "validation_score": validation_result.validation_score,
                "confidence_score": validation_result.confidence_score,
                "total_issues": len(validation_result.issues),
                "critical_issues": len([i for i in validation_result.issues if i.severity == ValidationSeverity.ERROR])
            }
        }
        
        # Group issues by type for better UX
        missing_fields = []
        incorrect_fields = []
        
        for issue in human_input_issues:
            if issue.issue_type == "missing_required":
                # Get field type safely
                field_type = self.required_fields.get(issue.field_name, {}).get("type", FieldType.TEXT)
                type_value = field_type.value if hasattr(field_type, 'value') else str(field_type)
                
                missing_fields.append({
                    "field": issue.field_name,
                    "description": self.required_fields.get(issue.field_name, {}).get("description", ""),
                    "type": type_value,
                    "message": issue.message
                })
            else:
                incorrect_fields.append({
                    "field": issue.field_name,
                    "current_value": issue.current_value,
                    "suggested_value": issue.suggested_value,
                    "issue_type": issue.issue_type,
                    "message": issue.message,
                    "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity
                })
        
        if missing_fields:
            request["required_actions"].append({
                "action_type": "provide_missing_fields",
                "title": "Provide Missing Required Information",
                "description": "The following required fields are missing and need to be provided:",
                "fields": missing_fields
            })
        
        if incorrect_fields:
            request["required_actions"].append({
                "action_type": "review_incorrect_fields",
                "title": "Review and Correct Field Values", 
                "description": "The following fields may need review or correction:",
                "fields": incorrect_fields
            })
        
        # Add suggestions for improvement
        for issue in validation_result.issues:
            if issue.severity == ValidationSeverity.INFO:
                request["suggestions"].append({
                    "field": issue.field_name,
                    "message": issue.message,
                    "current_value": issue.current_value
                })
        
        self.logger.info(f"📋 Created human input request for {contract_name}: {len(missing_fields)} missing fields, {len(incorrect_fields)} incorrect fields")
        
        return request
    
    def validate_raw_invoice_data(self, raw_data: Dict[str, Any], user_id: str, contract_name: str) -> ValidationResult:
        """
        Validate raw invoice data without Pydantic model conversion
        Used when Pydantic validation fails but we want to provide custom validation feedback
        
        Args:
            raw_data: Raw dictionary data to validate
            user_id: User ID for logging/tracking
            contract_name: Contract name for context
            
        Returns:
            ValidationResult with validation status and issues
        """
        self.logger.info(f"🔍 Starting raw data validation for contract: {contract_name}")
        
        issues = []
        missing_required_fields = []
        validation_score = 1.0
        
        # Use raw data directly for validation
        data_dict = raw_data
        self.logger.debug(f"Raw data dict keys: {list(data_dict.keys()) if data_dict else 'None'}")
        
        # Validate required fields
        for field_path, field_config in self.required_fields.items():
            field_value = self._get_nested_field(data_dict, field_path)
            
            self.logger.debug(f"Validating field {field_path}: value={field_value}, required={field_config['required']}")
            
            if field_config["required"] and (field_value is None or field_value == ""):
                missing_required_fields.append(field_path)
                issues.append(ValidationIssue(
                    field_name=field_path,
                    issue_type="missing_required",
                    severity=ValidationSeverity.ERROR,
                    message=f"Required field '{field_path}' is missing: {field_config['description']}",
                    current_value=field_value,
                    requires_human_input=True
                ))
                validation_score -= 0.15  # Significant penalty for missing required fields
                self.logger.debug(f"Missing required field {field_path}, score now: {validation_score:.2f}")
            
            elif field_value is not None and field_value != "":
                # Validate field format/content with more lenient rules for raw data
                validation_issue = self._validate_field_content_lenient(field_path, field_value, field_config)
                if validation_issue:
                    issues.append(validation_issue)
                    if validation_issue.severity == ValidationSeverity.ERROR:
                        validation_score -= 0.10
                    elif validation_issue.severity == ValidationSeverity.WARNING:
                        validation_score -= 0.05
                    self.logger.debug(f"Validation issue for {field_path}: {validation_issue.message}")
        
        # Additional business logic validations
        business_issues = self._perform_business_validation(data_dict)
        issues.extend(business_issues)
        
        # Calculate final scores
        validation_score = max(0.0, validation_score)  # Don't go below 0
        
        # Determine validity - data is valid if:
        # 1. No missing required fields AND
        # 2. No ERROR severity issues AND  
        # 3. Validation score meets minimum threshold
        is_valid = (
            len(missing_required_fields) == 0 and 
            all(issue.severity != ValidationSeverity.ERROR for issue in issues) and
            validation_score >= 0.6  # Minimum score threshold for validity
        )
        
        # Determine human input requirement more intelligently
        human_input_required = self._determine_human_input_required(
            missing_required_fields, issues, validation_score
        )
        
        # Calculate confidence based on completeness and validation issues
        confidence_score = self._calculate_confidence_score(data_dict, issues)
        
        self.logger.debug(f"Raw validation results - Score: {validation_score:.2f}, Valid: {is_valid}, Human input: {human_input_required}")
        
        result = ValidationResult(
            is_valid=is_valid,
            validation_score=validation_score,
            issues=issues,
            missing_required_fields=missing_required_fields,
            human_input_required=human_input_required,
            confidence_score=confidence_score,
            validation_timestamp=datetime.now().isoformat()
        )
        
        self.logger.info(f"✅ Raw validation completed - Valid: {is_valid}, Score: {validation_score:.2f}, Confidence: {confidence_score:.2f}, Issues: {len(issues)}, Missing fields: {len(missing_required_fields)}, Human input required: {human_input_required}")
        if missing_required_fields:
            self.logger.info(f"Missing required fields: {missing_required_fields}")
        if issues:
            self.logger.info(f"Issues found: {[f'{i.field_name}: {i.message}' for i in issues[:3]]}{' ...' if len(issues) > 3 else ''}")
        
        return result
    
    def validate_unified_invoice_data(self, invoice_data: UnifiedInvoiceData, user_id: str, contract_name: str) -> ValidationResult:
        """
        Validate unified invoice data for completeness and correctness
        
        Args:
            invoice_data: The unified invoice data to validate
            user_id: User ID for logging/tracking
            contract_name: Contract name for context
            
        Returns:
            ValidationResult with validation status and issues
        """
        self.logger.info(f"🔍 Starting unified validation for contract: {contract_name}")
        
        issues = []
        missing_required_fields = []
        validation_score = 1.0
        
        # Convert unified invoice data to dict for validation
        data_dict = invoice_data.model_dump()
        self.logger.debug(f"Unified data dict keys: {list(data_dict.keys()) if data_dict else 'None'}")
        
        # Validate required fields using the same logic as before
        for field_path, field_config in self.required_fields.items():
            field_value = self._get_nested_field(data_dict, field_path)
            
            self.logger.debug(f"Validating field {field_path}: value={field_value}, required={field_config['required']}")
            
            if field_config["required"] and (field_value is None or field_value == ""):
                missing_required_fields.append(field_path)
                issues.append(ValidationIssue(
                    field_name=field_path,
                    issue_type="missing_required",
                    severity=ValidationSeverity.ERROR,
                    message=f"Required field '{field_path}' is missing: {field_config['description']}",
                    current_value=field_value,
                    requires_human_input=True
                ))
                validation_score -= 0.15
                self.logger.debug(f"Missing required field {field_path}, score now: {validation_score:.2f}")
            
            elif field_value is not None and field_value != "":
                # Validate field format/content
                validation_issue = self._validate_field_content(field_path, field_value, field_config)
                if validation_issue:
                    issues.append(validation_issue)
                    if validation_issue.severity == ValidationSeverity.ERROR:
                        validation_score -= 0.10
                    elif validation_issue.severity == ValidationSeverity.WARNING:
                        validation_score -= 0.05
                    self.logger.debug(f"Validation issue for {field_path}: {validation_issue.message}")
        
        # Additional business logic validations
        business_issues = self._perform_business_validation(data_dict)
        issues.extend(business_issues)
        
        # Calculate final scores
        validation_score = max(0.0, validation_score)
        
        # Determine validity
        is_valid = (
            len(missing_required_fields) == 0 and 
            all(issue.severity != ValidationSeverity.ERROR for issue in issues) and
            validation_score >= 0.6
        )
        
        # Determine human input requirement
        human_input_required = self._determine_human_input_required(
            missing_required_fields, issues, validation_score
        )
        
        # Calculate confidence based on completeness and validation issues
        confidence_score = self._calculate_confidence_score(data_dict, issues)
        
        self.logger.debug(f"Unified validation results - Score: {validation_score:.2f}, Valid: {is_valid}, Human input: {human_input_required}")
        
        result = ValidationResult(
            is_valid=is_valid,
            validation_score=validation_score,
            issues=issues,
            missing_required_fields=missing_required_fields,
            human_input_required=human_input_required,
            confidence_score=confidence_score,
            validation_timestamp=datetime.now().isoformat()
        )
        
        self.logger.info(f"✅ Unified validation completed - Valid: {is_valid}, Score: {validation_score:.2f}, Confidence: {confidence_score:.2f}, Issues: {len(issues)}, Missing fields: {len(missing_required_fields)}, Human input required: {human_input_required}")
        if missing_required_fields:
            self.logger.info(f"Missing required fields: {missing_required_fields}")
        if issues:
            self.logger.info(f"Issues found: {[f'{i.field_name}: {i.message}' for i in issues[:3]]}{' ...' if len(issues) > 3 else ''}")
        
        return result
    
    def _validate_field_content_lenient(self, field_path: str, field_value: Any, field_config: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Lenient validation for raw data that doesn't strictly follow Pydantic models"""
        field_type = field_config["type"]
        validation_rules = field_config.get("validation_rules", {})
        
        # For raw data validation, be more lenient with types and formats
        if field_type == FieldType.EMAIL:
            if isinstance(field_value, str) and "@" not in field_value:
                return ValidationIssue(
                    field_name=field_path,
                    issue_type="invalid_format",
                    severity=ValidationSeverity.WARNING,  # Warning instead of error for raw data
                    message=f"Field '{field_path}' doesn't appear to be a valid email address",
                    current_value=field_value,
                    requires_human_input=True
                )
        
        elif field_type == FieldType.DATE:
            if isinstance(field_value, str) and field_value.strip():
                try:
                    from dateutil.parser import parse
                    parse(field_value)
                except:
                    return ValidationIssue(
                        field_name=field_path,
                        issue_type="invalid_date_format",
                        severity=ValidationSeverity.WARNING,
                        message=f"Field '{field_path}' doesn't appear to be a valid date",
                        current_value=field_value,
                        suggested_value="YYYY-MM-DD format recommended",
                        requires_human_input=True
                    )
        
        elif field_type == FieldType.TEXT:
            return self._validate_text_field(field_path, field_value, validation_rules, field_config["description"])
        
        elif field_type in [FieldType.NUMBER, FieldType.CURRENCY]:
            return self._validate_number_field(field_path, field_value, validation_rules, field_config["description"])
        
        return None


# Singleton service instance
_validation_service = None

def get_validation_service() -> InvoiceDataValidationService:
    """Get singleton validation service instance"""
    global _validation_service
    if _validation_service is None:
        _validation_service = InvoiceDataValidationService()
    return _validation_service