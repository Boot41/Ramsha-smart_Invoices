#!/usr/bin/env python3
"""
Validation Agent Evaluation Framework

This module provides comprehensive evaluation tests for the validation agent,
testing validation accuracy, human-in-the-loop functionality, and edge cases.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging
from dataclasses import dataclass
from copy import deepcopy

def datetime_serializer(obj):
    """JSON serializer for datetime, date, and decimal objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Decimal':
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

from agents.validation_agent import ValidationAgent
from services.validation_service import get_validation_service
from schemas.workflow_schemas import WorkflowState, ProcessingStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationEvaluationResult:
    """Result of a single validation evaluation"""
    test_name: str
    passed: bool
    score: float
    details: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    validation_accuracy: float = 0.0
    human_input_correctly_detected: bool = False

@dataclass 
class ValidationTestCase:
    """Test case for validation agent evaluation"""
    name: str
    description: str
    input_invoice_data: Dict[str, Any]
    expected_validation_result: Dict[str, Any]
    expected_human_input_required: bool = False
    expected_missing_fields: List[str] = None
    test_human_input: Optional[Dict[str, Any]] = None
    expected_after_human_input: Dict[str, Any] = None

class ValidationAgentEvaluator:
    """Comprehensive evaluator for validation agent functionality"""
    
    def __init__(self):
        self.validation_agent = ValidationAgent()
        self.validation_service = get_validation_service()
        self.results: List[ValidationEvaluationResult] = []
        
    def create_validation_test_cases(self) -> List[ValidationTestCase]:
        """Create comprehensive test cases for validation scenarios"""
        
        return [
            # Test Case 1: Perfect Valid Data
            ValidationTestCase(
                name="perfect_valid_data",
                description="Invoice data with all required fields correctly filled",
                input_invoice_data={
                    "client": {
                        "name": "John Smith",
                        "email": "john.smith@email.com",
                        "address": "123 Main St, Anytown, NY 12345",
                        "phone": "+1-555-123-4567"
                    },
                    "service_provider": {
                        "name": "Property Management LLC",
                        "email": "info@propmanagement.com",
                        "address": "456 Business Ave, Metro City, NY 10001",
                        "phone": "+1-555-987-6543"
                    },
                    "payment_terms": {
                        "amount": 1200.00,
                        "currency": "USD",
                        "frequency": "monthly",
                        "due_days": 1
                    },
                    "contract_type": "rental_lease",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                },
                expected_validation_result={
                    "is_valid": True,
                    "human_input_required": False,
                    "validation_score_min": 0.9,
                    "confidence_score_min": 0.8
                },
                expected_human_input_required=False
            ),
            
            # Test Case 2: Missing Required Fields
            ValidationTestCase(
                name="missing_required_fields",
                description="Invoice data missing critical required fields",
                input_invoice_data={
                    "client": {
                        "name": "Jane Doe"
                        # Missing email, address, phone
                    },
                    "service_provider": {
                        # Missing name entirely
                        "email": "incomplete@service.com"
                    },
                    "payment_terms": {
                        # Missing amount and currency
                        "frequency": "monthly"
                    }
                },
                expected_validation_result={
                    "is_valid": False,
                    "human_input_required": True,
                    "validation_score_max": 0.5,
                    "missing_fields_min": 3
                },
                expected_human_input_required=True,
                expected_missing_fields=["service_provider.name", "payment_terms.amount", "payment_terms.currency"],
                test_human_input={
                    "service_provider.name": "Complete Service Co",
                    "payment_terms.amount": 850.00,
                    "payment_terms.currency": "USD"
                },
                expected_after_human_input={
                    "is_valid": True,
                    "human_input_required": False,
                    "validation_score_min": 0.8
                }
            ),
            
            # Test Case 3: Invalid Field Formats
            ValidationTestCase(
                name="invalid_field_formats",
                description="Invoice data with incorrectly formatted fields",
                input_invoice_data={
                    "client": {
                        "name": "Bob Johnson",
                        "email": "invalid-email-format",  # Invalid email
                        "phone": "not-a-phone-number"     # Invalid phone
                    },
                    "service_provider": {
                        "name": "Service Provider Inc",
                        "email": "valid@service.com"
                    },
                    "payment_terms": {
                        "amount": -500.00,  # Invalid negative amount
                        "currency": "INVALID_CURRENCY",  # Invalid currency code
                        "frequency": "sometimes",  # Invalid frequency
                        "due_days": 45  # Unrealistic due days
                    },
                    "start_date": "not-a-date"  # Invalid date format
                },
                expected_validation_result={
                    "is_valid": False,
                    "human_input_required": True,
                    "validation_score_max": 0.6,
                    "issues_min": 5
                },
                expected_human_input_required=True,
                test_human_input={
                    "client.email": "bob.johnson@email.com",
                    "client.phone": "+1-555-234-5678",
                    "payment_terms.amount": 500.00,
                    "payment_terms.currency": "USD",
                    "payment_terms.frequency": "monthly",
                    "payment_terms.due_days": 5,
                    "start_date": "2024-02-01"
                },
                expected_after_human_input={
                    "is_valid": True,
                    "validation_score_min": 0.85
                }
            ),
            
            # Test Case 4: Edge Case - Minimal Valid Data
            ValidationTestCase(
                name="minimal_valid_data",
                description="Minimal required fields only, should be valid",
                input_invoice_data={
                    "client": {
                        "name": "Minimal Client"
                    },
                    "service_provider": {
                        "name": "Minimal Service"
                    },
                    "payment_terms": {
                        "amount": 100.00,
                        "currency": "USD",
                        "frequency": "monthly"
                    }
                },
                expected_validation_result={
                    "is_valid": True,
                    "human_input_required": False,
                    "validation_score_min": 0.7,
                    "confidence_score_min": 0.6
                },
                expected_human_input_required=False
            ),
            
            # Test Case 5: Business Logic Violations
            ValidationTestCase(
                name="business_logic_violations",
                description="Data that violates business logic rules",
                input_invoice_data={
                    "client": {
                        "name": "Same Entity Corp"
                    },
                    "service_provider": {
                        "name": "Same Entity Corp"  # Same as client - should trigger warning
                    },
                    "payment_terms": {
                        "amount": 0.01,  # Unreasonably low amount
                        "currency": "USD",
                        "frequency": "monthly"
                    }
                },
                expected_validation_result={
                    "is_valid": True,  # Valid but with warnings
                    "human_input_required": False,
                    "validation_score_min": 0.6,
                    "warnings_min": 2
                },
                expected_human_input_required=False
            ),
            
            # Test Case 6: International Contract (EUR)
            ValidationTestCase(
                name="international_contract_eur",
                description="European contract with EUR currency and higher amounts",
                input_invoice_data={
                    "client": {
                        "name": "European Client GmbH",
                        "email": "client@europe.eu"
                    },
                    "service_provider": {
                        "name": "Service Provider SA",
                        "email": "provider@europe.eu"
                    },
                    "payment_terms": {
                        "amount": 2500.00,
                        "currency": "EUR",
                        "frequency": "monthly",
                        "due_days": 15
                    },
                    "contract_type": "service_agreement"
                },
                expected_validation_result={
                    "is_valid": True,
                    "human_input_required": False,
                    "validation_score_min": 0.8,
                    "confidence_score_min": 0.7
                },
                expected_human_input_required=False
            ),
            
            # Test Case 7: Empty/Null Data
            ValidationTestCase(
                name="empty_null_data",
                description="Invoice data with null and empty values",
                input_invoice_data={
                    "client": None,
                    "service_provider": {},
                    "payment_terms": {
                        "amount": None,
                        "currency": "",
                        "frequency": None
                    },
                    "contract_type": "",
                    "start_date": None
                },
                expected_validation_result={
                    "is_valid": False,
                    "human_input_required": True,
                    "validation_score_max": 0.2,
                    "missing_fields_min": 5
                },
                expected_human_input_required=True,
                expected_missing_fields=["client.name", "service_provider.name", "payment_terms.amount", "payment_terms.currency", "payment_terms.frequency"],
                test_human_input={
                    "client.name": "Recovered Client",
                    "service_provider.name": "Recovered Service",
                    "payment_terms.amount": 750.00,
                    "payment_terms.currency": "USD",
                    "payment_terms.frequency": "monthly"
                }
            ),
            
            # Test Case 8: Partial Human Input Resolution
            ValidationTestCase(
                name="partial_human_input_resolution",
                description="Human input that only partially resolves validation issues",
                input_invoice_data={
                    "client": {
                        "name": "Client with Issues",
                        "email": "bad-email-format"
                    },
                    "service_provider": {
                        # Missing name
                        "email": "provider@service.com"
                    },
                    "payment_terms": {
                        "amount": 1500.00,
                        "currency": "INVALID",
                        "frequency": "monthly"
                    }
                },
                expected_validation_result={
                    "is_valid": False,
                    "human_input_required": True,
                    "issues_min": 3
                },
                expected_human_input_required=True,
                test_human_input={
                    # Only providing partial fixes
                    "service_provider.name": "Fixed Service Provider",
                    "payment_terms.currency": "USD"
                    # Not fixing client.email
                },
                expected_after_human_input={
                    "is_valid": False,  # Still invalid due to unfixed email
                    "human_input_required": True,  # Still needs more input
                    "validation_score_min": 0.6  # Should improve but not be perfect
                }
            )
        ]
    
    def create_workflow_state_for_validation(self, test_case: ValidationTestCase, user_id: str = "test-user") -> WorkflowState:
        """Create a workflow state for validation testing"""
        return {
            "workflow_id": f"validation-test-{test_case.name}",
            "user_id": user_id,
            "contract_file": "test-contract.pdf",
            "contract_name": test_case.name,
            "contract_data": test_case.input_invoice_data,
            "invoice_data": {
                "invoice_response": {
                    "invoice_data": test_case.input_invoice_data,
                    "raw_response": "Test data",
                    "confidence_score": 0.8
                },
                "generated_at": datetime.now().isoformat(),
                "confidence": 0.8
            },
            "validation_results": None,
            "schedule_data": None,
            "final_invoice": None,
            "attempt_count": 1,
            "max_attempts": 3,
            "errors": [],
            "feedback_history": [],
            "quality_score": 0.0,
            "confidence_level": 0.0,
            "processing_status": ProcessingStatus.IN_PROGRESS.value,
            "current_agent": "validation",
            "orchestrator_decision_count": 0,
            "retry_reasons": [],
            "learned_patterns": {},
            "improvement_suggestions": [],
            "success_metrics": {},
            "started_at": datetime.now().isoformat(),
            "last_updated_at": datetime.now().isoformat(),
            "workflow_completed": False,
        }
    
    async def evaluate_single_validation_test(self, test_case: ValidationTestCase) -> ValidationEvaluationResult:
        """Evaluate a single validation test case"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🧪 Running validation test: {test_case.name}")
            
            # Create initial workflow state
            state = self.create_workflow_state_for_validation(test_case)
            
            # Execute validation agent
            result_state = self.validation_agent.execute(state)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate initial validation results
            initial_score, initial_details = self._evaluate_validation_results(test_case, result_state, "initial")
            
            # Test human input functionality if expected
            human_input_score = 0.0
            human_input_correctly_detected = False
            
            if test_case.expected_human_input_required or test_case.test_human_input:
                human_input_score, human_input_correctly_detected = await self._test_human_input_functionality(
                    test_case, result_state
                )
            
            # Calculate overall score
            overall_score = (initial_score * 0.7) + (human_input_score * 0.3)
            
            # Determine if test passed
            passed = (
                overall_score >= 0.7 and
                initial_details.get("validation_accuracy", 0) >= 0.7 and
                (not test_case.expected_human_input_required or human_input_correctly_detected)
            )
            
            return ValidationEvaluationResult(
                test_name=test_case.name,
                passed=passed,
                score=overall_score,
                details={
                    **initial_details,
                    "human_input_score": human_input_score,
                    "test_description": test_case.description
                },
                execution_time=execution_time,
                validation_accuracy=initial_details.get("validation_accuracy", 0),
                human_input_correctly_detected=human_input_correctly_detected
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Validation test {test_case.name} failed with error: {str(e)}")
            
            return ValidationEvaluationResult(
                test_name=test_case.name,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _evaluate_validation_results(self, test_case: ValidationTestCase, result_state: WorkflowState, phase: str) -> tuple[float, Dict[str, Any]]:
        """Evaluate validation results against expected outcomes"""
        
        details = {
            f"{phase}_validation_results": result_state.get("validation_results"),
            f"{phase}_processing_status": result_state.get("processing_status"),
            "expected": test_case.expected_validation_result,
            "accuracy_breakdown": {}
        }
        
        validation_results = result_state.get("validation_results", {})
        expected = test_case.expected_validation_result
        
        score = 0.0
        total_checks = 0
        
        # Check is_valid expectation
        if "is_valid" in expected:
            total_checks += 1
            if validation_results.get("is_valid") == expected["is_valid"]:
                score += 1
                details["accuracy_breakdown"]["is_valid"] = "✅ Correct"
            else:
                details["accuracy_breakdown"]["is_valid"] = f"❌ Expected {expected['is_valid']}, got {validation_results.get('is_valid')}"
        
        # Check human_input_required expectation
        if "human_input_required" in expected:
            total_checks += 1
            if validation_results.get("human_input_required") == expected["human_input_required"]:
                score += 1
                details["accuracy_breakdown"]["human_input_required"] = "✅ Correct"
            else:
                details["accuracy_breakdown"]["human_input_required"] = f"❌ Expected {expected['human_input_required']}, got {validation_results.get('human_input_required')}"
        
        # Check validation score ranges
        validation_score = validation_results.get("validation_score", 0)
        if "validation_score_min" in expected:
            total_checks += 1
            if validation_score >= expected["validation_score_min"]:
                score += 1
                details["accuracy_breakdown"]["validation_score_min"] = f"✅ {validation_score:.2f} >= {expected['validation_score_min']}"
            else:
                details["accuracy_breakdown"]["validation_score_min"] = f"❌ {validation_score:.2f} < {expected['validation_score_min']}"
        
        if "validation_score_max" in expected:
            total_checks += 1
            if validation_score <= expected["validation_score_max"]:
                score += 1
                details["accuracy_breakdown"]["validation_score_max"] = f"✅ {validation_score:.2f} <= {expected['validation_score_max']}"
            else:
                details["accuracy_breakdown"]["validation_score_max"] = f"❌ {validation_score:.2f} > {expected['validation_score_max']}"
        
        # Check confidence score ranges
        confidence_score = validation_results.get("confidence_score", 0)
        if "confidence_score_min" in expected:
            total_checks += 1
            if confidence_score >= expected["confidence_score_min"]:
                score += 1
                details["accuracy_breakdown"]["confidence_score_min"] = f"✅ {confidence_score:.2f} >= {expected['confidence_score_min']}"
            else:
                details["accuracy_breakdown"]["confidence_score_min"] = f"❌ {confidence_score:.2f} < {expected['confidence_score_min']}"
        
        # Check missing fields count
        missing_fields_count = validation_results.get("missing_required_fields_count", 0)
        if "missing_fields_min" in expected:
            total_checks += 1
            if missing_fields_count >= expected["missing_fields_min"]:
                score += 1
                details["accuracy_breakdown"]["missing_fields_min"] = f"✅ {missing_fields_count} >= {expected['missing_fields_min']}"
            else:
                details["accuracy_breakdown"]["missing_fields_min"] = f"❌ {missing_fields_count} < {expected['missing_fields_min']}"
        
        # Check issues count
        issues_count = validation_results.get("issues_count", 0)
        if "issues_min" in expected:
            total_checks += 1
            if issues_count >= expected["issues_min"]:
                score += 1
                details["accuracy_breakdown"]["issues_min"] = f"✅ {issues_count} >= {expected['issues_min']}"
            else:
                details["accuracy_breakdown"]["issues_min"] = f"❌ {issues_count} < {expected['issues_min']}"
        
        # Check for expected missing fields
        if test_case.expected_missing_fields:
            total_checks += 1
            missing_fields = validation_results.get("missing_required_fields", [])
            expected_found = all(field in missing_fields for field in test_case.expected_missing_fields)
            if expected_found:
                score += 1
                details["accuracy_breakdown"]["expected_missing_fields"] = f"✅ Found expected missing fields: {test_case.expected_missing_fields}"
            else:
                details["accuracy_breakdown"]["expected_missing_fields"] = f"❌ Missing fields found: {missing_fields}, expected: {test_case.expected_missing_fields}"
        
        # Calculate accuracy percentage
        validation_accuracy = score / total_checks if total_checks > 0 else 0
        details["validation_accuracy"] = validation_accuracy
        
        return validation_accuracy, details
    
    async def _test_human_input_functionality(self, test_case: ValidationTestCase, initial_state: WorkflowState) -> tuple[float, bool]:
        """Test human input functionality"""
        score = 0.0
        correctly_detected = False
        
        try:
            # Check if human input was correctly detected as required
            validation_results = initial_state.get("validation_results", {})
            human_input_required = validation_results.get("human_input_required", False)
            
            if human_input_required == test_case.expected_human_input_required:
                correctly_detected = True
                score += 0.5
                logger.info(f"✅ Human input requirement correctly detected: {human_input_required}")
            else:
                logger.warning(f"❌ Human input detection mismatch. Expected: {test_case.expected_human_input_required}, Got: {human_input_required}")
            
            # Test human input processing if test data is provided
            if test_case.test_human_input and human_input_required:
                logger.info("🔄 Testing human input processing...")
                
                # Process human input
                updated_state = self.validation_agent.handle_human_input_response(
                    state=deepcopy(initial_state),
                    human_input_data=test_case.test_human_input
                )
                
                # Evaluate results after human input
                if test_case.expected_after_human_input:
                    post_input_score, _ = self._evaluate_validation_results(
                        test_case, updated_state, "post_human_input"
                    )
                    score += post_input_score * 0.5
                    logger.info(f"✅ Human input processing score: {post_input_score:.2f}")
                else:
                    score += 0.3  # Partial credit for successful processing
            
            elif test_case.test_human_input and not human_input_required:
                logger.warning("⚠️ Test case has human input data but validation didn't require it")
            
        except Exception as e:
            logger.error(f"❌ Human input functionality test failed: {str(e)}")
            score = 0.0
        
        return score, correctly_detected
    
    async def run_all_validation_evaluations(self) -> Dict[str, Any]:
        """Run all validation evaluation test cases"""
        test_cases = self.create_validation_test_cases()
        self.results = []
        
        logger.info(f"🚀 Starting validation agent evaluation with {len(test_cases)} test cases...")
        
        for test_case in test_cases:
            logger.info(f"📝 Running validation test: {test_case.name}")
            result = await self.evaluate_single_validation_test(test_case)
            self.results.append(result)
            
            # Log result
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"{status} {test_case.name} - Score: {result.score:.2f}, Validation Accuracy: {result.validation_accuracy:.2f}")
        
        # Generate summary report
        return self._generate_validation_summary_report()
    
    def _generate_validation_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report for validation evaluation"""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        avg_score = sum(r.score for r in self.results) / total_tests if total_tests > 0 else 0
        avg_validation_accuracy = sum(r.validation_accuracy for r in self.results) / total_tests if total_tests > 0 else 0
        avg_execution_time = sum(r.execution_time for r in self.results) / total_tests if total_tests > 0 else 0
        
        human_input_tests = [r for r in self.results if hasattr(r, 'human_input_correctly_detected')]
        human_input_accuracy = sum(1 for r in human_input_tests if r.human_input_correctly_detected) / len(human_input_tests) if human_input_tests else 0
        
        def clean_for_json(obj):
            """Recursively convert datetime and date objects to ISO strings"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, date):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            else:
                return obj
        
        report = {
            "summary": {
                "evaluation_type": "validation_agent",
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0,
                "average_score": avg_score,
                "average_validation_accuracy": avg_validation_accuracy,
                "average_execution_time": avg_execution_time,
                "human_input_detection_accuracy": human_input_accuracy * 100
            },
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "score": r.score,
                    "validation_accuracy": r.validation_accuracy,
                    "execution_time": r.execution_time,
                    "human_input_correctly_detected": r.human_input_correctly_detected,
                    "error": r.error_message,
                    "details": clean_for_json(r.details)
                }
                for r in self.results
            ],
            "validation_metrics": {
                "accuracy_by_category": self._calculate_accuracy_by_category(),
                "common_validation_failures": self._identify_common_failures(),
                "human_input_effectiveness": self._analyze_human_input_effectiveness()
            },
            "recommendations": self._generate_validation_recommendations()
        }
        
        return report
    
    def _calculate_accuracy_by_category(self) -> Dict[str, float]:
        """Calculate validation accuracy by different categories"""
        categories = {
            "required_field_detection": [],
            "format_validation": [],
            "business_logic": [],
            "human_input_detection": []
        }
        
        for result in self.results:
            # Categorize based on test name patterns
            if "missing" in result.test_name or "required" in result.test_name:
                categories["required_field_detection"].append(result.validation_accuracy)
            elif "format" in result.test_name or "invalid" in result.test_name:
                categories["format_validation"].append(result.validation_accuracy)
            elif "business" in result.test_name or "logic" in result.test_name:
                categories["business_logic"].append(result.validation_accuracy)
            elif "human_input" in result.test_name:
                categories["human_input_detection"].append(result.validation_accuracy)
        
        return {
            category: sum(scores) / len(scores) if scores else 0.0
            for category, scores in categories.items()
        }
    
    def _identify_common_failures(self) -> List[str]:
        """Identify common validation failure patterns"""
        failures = []
        failed_results = [r for r in self.results if not r.passed]
        
        for result in failed_results:
            if result.error_message:
                failures.append(f"Error in {result.test_name}: {result.error_message}")
            elif result.validation_accuracy < 0.5:
                failures.append(f"Low validation accuracy in {result.test_name}: {result.validation_accuracy:.2f}")
        
        return failures
    
    def _analyze_human_input_effectiveness(self) -> Dict[str, Any]:
        """Analyze effectiveness of human input functionality"""
        human_input_results = [r for r in self.results if hasattr(r, 'human_input_correctly_detected')]
        
        if not human_input_results:
            return {"status": "no_human_input_tests"}
        
        detection_rate = sum(1 for r in human_input_results if r.human_input_correctly_detected) / len(human_input_results)
        
        return {
            "detection_accuracy": detection_rate,
            "total_human_input_tests": len(human_input_results),
            "successful_detections": sum(1 for r in human_input_results if r.human_input_correctly_detected)
        }
    
    def _generate_validation_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on validation results"""
        recommendations = []
        
        failed_results = [r for r in self.results if not r.passed]
        
        if len(failed_results) > len(self.results) * 0.3:
            recommendations.append("High validation failure rate detected. Review core validation logic and field requirements.")
        
        low_accuracy_results = [r for r in self.results if r.validation_accuracy < 0.7]
        if len(low_accuracy_results) > 0:
            recommendations.append("Multiple tests show low validation accuracy. Consider improving validation criteria and scoring mechanisms.")
        
        human_input_failures = [r for r in self.results if hasattr(r, 'human_input_correctly_detected') and not r.human_input_correctly_detected]
        if len(human_input_failures) > 0:
            recommendations.append("Human input detection needs improvement. Review validation criteria for determining when human input is required.")
        
        # Check for specific patterns
        format_failures = [r for r in self.results if "format" in r.test_name or "invalid" in r.test_name and not r.passed]
        if len(format_failures) > 0:
            recommendations.append("Format validation needs strengthening. Review field format validators and error handling.")
        
        return recommendations


# Test runner and CLI interface
async def main():
    """Main test runner for validation agent evaluation"""
    evaluator = ValidationAgentEvaluator()
    
    print("🔬 Validation Agent Evaluation Framework")
    print("=" * 60)
    
    # Run evaluations
    report = await evaluator.run_all_validation_evaluations()
    
    # Print summary
    summary = report["summary"]
    print(f"\n📊 VALIDATION EVALUATION SUMMARY")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌") 
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"Average Score: {summary['average_score']:.3f}")
    print(f"Average Validation Accuracy: {summary['average_validation_accuracy']:.3f}")
    print(f"Human Input Detection Accuracy: {summary['human_input_detection_accuracy']:.1f}%")
    print(f"Average Execution Time: {summary['average_execution_time']:.2f}s")
    
    # Print validation metrics
    if "validation_metrics" in report:
        print(f"\n📈 VALIDATION METRICS:")
        for category, accuracy in report["validation_metrics"]["accuracy_by_category"].items():
            print(f"  {category.replace('_', ' ').title()}: {accuracy:.3f}")
    
    # Print recommendations
    if report["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"validation_agent_eval_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=datetime_serializer)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())