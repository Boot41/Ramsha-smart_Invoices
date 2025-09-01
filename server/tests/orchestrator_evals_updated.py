#!/usr/bin/env python3
"""
Enhanced Orchestrator Agent Evaluation Framework

Updated to include validation agent testing and comprehensive workflow scenarios.
Tests the full orchestration pipeline including validation and human-in-the-loop.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
from copy import deepcopy

from agents.orchestrator_agent import OrchestratorAgent
from schemas.workflow_schemas import WorkflowState, ProcessingStatus
from workflows.invoice_workflow import run_invoice_workflow, initialize_workflow_state

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OrchestratorEvaluationResult:
    """Result of a single orchestrator evaluation"""
    test_name: str
    passed: bool
    score: float
    details: Dict[str, Any]
    execution_time: float
    workflow_completed: bool = False
    validation_passed: bool = False
    human_input_handled: bool = False
    error_message: Optional[str] = None

@dataclass
class OrchestrationTestCase:
    """Test case for orchestrator evaluation"""
    name: str
    description: str
    initial_state_overrides: Dict[str, Any]
    expected_workflow_path: List[str]  # Expected sequence of agents
    expected_final_status: str
    validation_scenario: str = "none"  # "none", "pass", "fail", "human_input_required"
    test_human_input: Optional[Dict[str, Any]] = None
    max_execution_steps: int = 15

class EnhancedOrchestratorEvaluator:
    """Comprehensive evaluator for orchestrator agent with validation integration"""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.results: List[OrchestratorEvaluationResult] = []
        
    def create_orchestration_test_cases(self) -> List[OrchestrationTestCase]:
        """Create comprehensive test cases for orchestrator evaluation including validation"""
        
        return [
            # Test Case 1: Perfect workflow - contract processing → validation → completion
            OrchestrationTestCase(
                name="perfect_workflow_with_validation",
                description="Perfect workflow: contract processing → validation → completion",
                initial_state_overrides={
                    "processing_status": ProcessingStatus.PENDING.value,
                    "contract_data": None,
                    "validation_results": None,
                    "attempt_count": 0
                },
                expected_workflow_path=["contract_processing", "validation", "complete_success"],
                expected_final_status="complete_success",
                validation_scenario="pass"
            ),
            
            # Test Case 2: Workflow with validation failure requiring human input
            OrchestrationTestCase(
                name="workflow_with_human_input_required",
                description="Workflow requiring human input during validation",
                initial_state_overrides={
                    "processing_status": ProcessingStatus.PENDING.value,
                    "contract_data": None,
                    "validation_results": None,
                    "attempt_count": 0
                },
                expected_workflow_path=["contract_processing", "validation", "complete_with_errors"],
                expected_final_status="complete_with_errors",
                validation_scenario="human_input_required",
                test_human_input={
                    "client.name": "Corrected Client Name",
                    "payment_terms.amount": 1500.00,
                    "payment_terms.currency": "USD"
                }
            ),
            
            # Test Case 3: Initial workflow start
            OrchestrationTestCase(
                name="initial_workflow_start",
                description="New workflow should start with contract processing",
                initial_state_overrides={
                    "processing_status": ProcessingStatus.PENDING.value,
                    "contract_data": None,
                    "attempt_count": 0
                },
                expected_workflow_path=["contract_processing"],
                expected_final_status="in_progress",
                max_execution_steps=2
            ),
            
            # Test Case 4: Contract processed, should proceed to validation
            OrchestrationTestCase(
                name="contract_to_validation_routing",
                description="After contract processing, should route to validation",
                initial_state_overrides={
                    "contract_data": {"extracted": True, "confidence": 0.8},
                    "invoice_data": {
                        "invoice_response": {"invoice_data": {"client": {"name": "Test Client"}}},
                        "confidence": 0.8
                    },
                    "validation_results": None,
                    "attempt_count": 1
                },
                expected_workflow_path=["validation"],
                expected_final_status="in_progress",
                validation_scenario="pass",
                max_execution_steps=3
            ),
            
            # Test Case 5: Validation passes, workflow should complete
            OrchestrationTestCase(
                name="validation_pass_completion",
                description="Successful validation should complete workflow",
                initial_state_overrides={
                    "contract_data": {"extracted": True},
                    "invoice_data": {"confidence": 0.8},
                    "validation_results": {
                        "is_valid": True,
                        "human_input_required": False,
                        "validation_score": 0.9,
                        "confidence_score": 0.8
                    },
                    "attempt_count": 1
                },
                expected_workflow_path=["complete_success"],
                expected_final_status="complete_success",
                max_execution_steps=2
            ),
            
            # Test Case 6: Validation requires human input
            OrchestrationTestCase(
                name="validation_human_input_pause",
                description="Validation requiring human input should pause workflow",
                initial_state_overrides={
                    "contract_data": {"extracted": True},
                    "invoice_data": {"confidence": 0.6},
                    "validation_results": {
                        "is_valid": False,
                        "human_input_required": True,
                        "validation_score": 0.4,
                        "missing_required_fields": ["client.name", "payment_terms.amount"]
                    },
                    "processing_status": ProcessingStatus.NEEDS_HUMAN_INPUT.value,
                    "attempt_count": 1
                },
                expected_workflow_path=["complete_with_errors"],
                expected_final_status="complete_with_errors",
                validation_scenario="human_input_required",
                max_execution_steps=2
            ),
            
            # Test Case 7: Human input provided, re-validation
            OrchestrationTestCase(
                name="human_input_revalidation",
                description="After human input, should re-validate data",
                initial_state_overrides={
                    "contract_data": {"extracted": True},
                    "invoice_data": {"confidence": 0.7},
                    "validation_results": {
                        "is_valid": False,
                        "human_input_required": True,
                        "validation_score": 0.5
                    },
                    "human_input_resolved": True,
                    "processing_status": ProcessingStatus.SUCCESS.value,
                    "attempt_count": 1
                },
                expected_workflow_path=["validation", "complete_success"],
                expected_final_status="complete_success",
                validation_scenario="pass",
                max_execution_steps=4
            ),
            
            # Test Case 8: Max attempts exceeded
            OrchestrationTestCase(
                name="max_attempts_exceeded",
                description="Max attempts should trigger workflow termination",
                initial_state_overrides={
                    "attempt_count": 3,
                    "max_attempts": 3,
                    "errors": [
                        {"error": "processing failed", "agent": "contract_processing"},
                        {"error": "processing failed again", "agent": "contract_processing"},
                        {"error": "processing failed third time", "agent": "contract_processing"}
                    ]
                },
                expected_workflow_path=["complete_with_errors"],
                expected_final_status="complete_with_errors",
                max_execution_steps=2
            ),
            
            # Test Case 9: Critical errors detected
            OrchestrationTestCase(
                name="critical_errors_recovery",
                description="Critical errors should route to error recovery",
                initial_state_overrides={
                    "errors": [
                        {"error": "database connection failed", "agent": "contract_processing"},
                        {"error": "authentication error", "agent": "validation"},
                        {"error": "file_not_found", "agent": "contract_processing"},
                        {"error": "permission denied", "agent": "orchestrator"}
                    ],
                    "attempt_count": 1
                },
                expected_workflow_path=["error_recovery"],
                expected_final_status="failed",
                max_execution_steps=3
            ),
            
            # Test Case 10: Retry after error recovery
            OrchestrationTestCase(
                name="retry_after_error_recovery",
                description="Should retry processing after error recovery",
                initial_state_overrides={
                    "processing_status": ProcessingStatus.NEEDS_RETRY.value,
                    "attempt_count": 1,
                    "max_attempts": 3,
                    "errors": [{"error": "recoverable error", "agent": "contract_processing"}]
                },
                expected_workflow_path=["contract_processing"],
                expected_final_status="in_progress",
                max_execution_steps=3
            ),
            
            # Test Case 11: Orchestrator decision loop prevention
            OrchestrationTestCase(
                name="prevent_orchestrator_loops",
                description="Should prevent infinite orchestrator decision loops",
                initial_state_overrides={
                    "orchestrator_decision_count": 18,  # Close to limit
                    "processing_status": ProcessingStatus.IN_PROGRESS.value,
                    "attempt_count": 1
                },
                expected_workflow_path=["complete_with_errors"],
                expected_final_status="complete_with_errors",
                max_execution_steps=3
            ),
            
            # Test Case 12: Complex workflow with multiple validation cycles
            OrchestrationTestCase(
                name="complex_multi_validation_workflow",
                description="Complex workflow with multiple validation attempts",
                initial_state_overrides={
                    "processing_status": ProcessingStatus.PENDING.value,
                    "contract_data": None,
                    "validation_results": None,
                    "attempt_count": 0,
                    "max_attempts": 5
                },
                expected_workflow_path=["contract_processing", "validation"],
                expected_final_status="in_progress",
                validation_scenario="fail_then_pass",
                max_execution_steps=8
            )
        ]
    
    def create_base_workflow_state(self, test_case: OrchestrationTestCase) -> WorkflowState:
        """Create base workflow state for testing"""
        base_state = initialize_workflow_state(
            user_id="test-user-orchestrator",
            contract_file="test-contract.pdf", 
            contract_name=f"test-{test_case.name}",
            max_attempts=3
        )
        
        # Apply test case specific overrides
        base_state.update(test_case.initial_state_overrides)
        
        return base_state
    
    async def evaluate_single_orchestration_test(self, test_case: OrchestrationTestCase) -> OrchestratorEvaluationResult:
        """Evaluate a single orchestration test case"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🧪 Running orchestration test: {test_case.name}")
            
            # Create initial workflow state
            initial_state = self.create_base_workflow_state(test_case)
            
            # Simulate workflow execution with orchestrator decisions
            execution_path = []
            current_state = deepcopy(initial_state)
            workflow_completed = False
            validation_passed = False
            human_input_handled = False
            
            # Execute workflow with step-by-step orchestrator decisions
            for step in range(test_case.max_execution_steps):
                logger.info(f"📍 Step {step + 1}: Current agent = {current_state.get('current_agent')}")
                
                # Run orchestrator decision
                decision_result = self.orchestrator.execute(current_state)
                current_agent = decision_result.get("current_agent")
                
                logger.info(f"🎯 Orchestrator decision: {current_agent}")
                execution_path.append(current_agent)
                
                # Check for completion states
                if current_agent in ["complete_success", "complete_with_errors", "__end__"]:
                    workflow_completed = True
                    break
                elif current_agent == "error_recovery":
                    current_state["processing_status"] = ProcessingStatus.FAILED.value
                    break
                
                # Simulate agent execution based on validation scenario
                if current_agent == "contract_processing":
                    current_state = self._simulate_contract_processing(current_state, test_case)
                elif current_agent == "validation":
                    current_state, validation_passed = self._simulate_validation(current_state, test_case)
                    if test_case.validation_scenario == "human_input_required" and not human_input_handled:
                        current_state["processing_status"] = ProcessingStatus.NEEDS_HUMAN_INPUT.value
                        human_input_handled = True
                
                # Prevent infinite loops
                current_state["orchestrator_decision_count"] = current_state.get("orchestrator_decision_count", 0) + 1
                if current_state["orchestrator_decision_count"] > 20:
                    break
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate results
            score, evaluation_details = self._evaluate_orchestration_results(
                test_case, execution_path, current_state, workflow_completed, validation_passed
            )
            
            # Determine if test passed
            passed = (
                score >= 0.7 and
                self._check_expected_workflow_path(execution_path, test_case.expected_workflow_path) and
                (workflow_completed or test_case.expected_final_status != "complete_success")
            )
            
            return OrchestratorEvaluationResult(
                test_name=test_case.name,
                passed=passed,
                score=score,
                details={
                    **evaluation_details,
                    "execution_path": execution_path,
                    "expected_path": test_case.expected_workflow_path,
                    "final_state_status": current_state.get("processing_status"),
                    "test_description": test_case.description
                },
                execution_time=execution_time,
                workflow_completed=workflow_completed,
                validation_passed=validation_passed,
                human_input_handled=human_input_handled
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Orchestration test {test_case.name} failed with error: {str(e)}")
            
            return OrchestratorEvaluationResult(
                test_name=test_case.name,
                passed=False,
                score=0.0,
                details={"error": str(e)},
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _simulate_contract_processing(self, state: WorkflowState, test_case: OrchestrationTestCase) -> WorkflowState:
        """Simulate contract processing agent execution"""
        state["attempt_count"] += 1
        
        # Simulate successful contract processing
        if not state.get("contract_data"):
            state["contract_data"] = {
                "extracted": True,
                "confidence": 0.8,
                "client": {"name": "Simulated Client"},
                "service_provider": {"name": "Simulated Provider"},
                "payment_terms": {"amount": 1000.0, "currency": "USD", "frequency": "monthly"}
            }
        
        if not state.get("invoice_data"):
            state["invoice_data"] = {
                "invoice_response": {
                    "invoice_data": state["contract_data"],
                    "confidence_score": 0.8
                },
                "confidence": 0.8
            }
        
        state["processing_status"] = ProcessingStatus.SUCCESS.value
        return state
    
    def _simulate_validation(self, state: WorkflowState, test_case: OrchestrationTestCase) -> tuple[WorkflowState, bool]:
        """Simulate validation agent execution"""
        validation_passed = False
        
        if test_case.validation_scenario == "pass":
            state["validation_results"] = {
                "is_valid": True,
                "human_input_required": False,
                "validation_score": 0.9,
                "confidence_score": 0.8,
                "issues_count": 0,
                "missing_required_fields_count": 0
            }
            validation_passed = True
            state["processing_status"] = ProcessingStatus.SUCCESS.value
            
        elif test_case.validation_scenario == "human_input_required":
            state["validation_results"] = {
                "is_valid": False,
                "human_input_required": True,
                "validation_score": 0.4,
                "confidence_score": 0.3,
                "issues_count": 3,
                "missing_required_fields_count": 2,
                "missing_required_fields": ["client.email", "payment_terms.due_days"]
            }
            state["processing_status"] = ProcessingStatus.NEEDS_HUMAN_INPUT.value
            state["human_input_request"] = {
                "required_actions": [
                    {"action_type": "provide_missing_fields", "fields": ["client.email", "payment_terms.due_days"]}
                ]
            }
            
        elif test_case.validation_scenario == "fail":
            state["validation_results"] = {
                "is_valid": False,
                "human_input_required": False,
                "validation_score": 0.3,
                "confidence_score": 0.2,
                "issues_count": 5
            }
            state["processing_status"] = ProcessingStatus.FAILED.value
            
        elif test_case.validation_scenario == "fail_then_pass":
            # Simulate improvement on retry
            attempt = state.get("attempt_count", 1)
            if attempt <= 1:
                state["validation_results"] = {
                    "is_valid": False,
                    "human_input_required": False,
                    "validation_score": 0.4,
                    "confidence_score": 0.3
                }
                state["processing_status"] = ProcessingStatus.NEEDS_RETRY.value
            else:
                state["validation_results"] = {
                    "is_valid": True,
                    "human_input_required": False,
                    "validation_score": 0.8,
                    "confidence_score": 0.7
                }
                validation_passed = True
                state["processing_status"] = ProcessingStatus.SUCCESS.value
        
        return state, validation_passed
    
    def _evaluate_orchestration_results(self, test_case: OrchestrationTestCase, 
                                      execution_path: List[str], 
                                      final_state: WorkflowState,
                                      workflow_completed: bool,
                                      validation_passed: bool) -> tuple[float, Dict[str, Any]]:
        """Evaluate orchestration results against expectations"""
        
        score = 0.0
        total_checks = 0
        details = {
            "path_accuracy": 0.0,
            "status_accuracy": 0.0,
            "validation_handling": 0.0,
            "workflow_completion": 0.0
        }
        
        # Check execution path accuracy
        total_checks += 1
        path_score = self._calculate_path_similarity(execution_path, test_case.expected_workflow_path)
        details["path_accuracy"] = path_score
        score += path_score
        
        # Check final status
        total_checks += 1
        final_status = final_state.get("processing_status", "unknown")
        if test_case.expected_final_status in ["complete_success", "complete_with_errors"]:
            # For completion states, check if workflow actually completed
            if workflow_completed:
                score += 1
                details["status_accuracy"] = 1.0
            else:
                details["status_accuracy"] = 0.0
        else:
            # For intermediate states, check status match
            if final_status == test_case.expected_final_status:
                score += 1
                details["status_accuracy"] = 1.0
            else:
                details["status_accuracy"] = 0.0
        
        # Check validation handling
        total_checks += 1
        if test_case.validation_scenario != "none":
            if test_case.validation_scenario == "pass" and validation_passed:
                score += 1
                details["validation_handling"] = 1.0
            elif test_case.validation_scenario == "human_input_required" and final_state.get("human_input_request"):
                score += 0.8  # Partial credit for detecting human input need
                details["validation_handling"] = 0.8
            elif test_case.validation_scenario in ["fail", "fail_then_pass"]:
                score += 0.6  # Partial credit for handling validation failure
                details["validation_handling"] = 0.6
            else:
                details["validation_handling"] = 0.0
        else:
            score += 1  # Full credit if no validation scenario
            details["validation_handling"] = 1.0
        
        # Check workflow completion appropriateness
        total_checks += 1
        expected_completion = test_case.expected_final_status in ["complete_success", "complete_with_errors"]
        if expected_completion == workflow_completed:
            score += 1
            details["workflow_completion"] = 1.0
        else:
            details["workflow_completion"] = 0.0
        
        # Calculate final score
        final_score = score / total_checks if total_checks > 0 else 0
        details["overall_score"] = final_score
        details["total_checks"] = total_checks
        
        return final_score, details
    
    def _check_expected_workflow_path(self, actual_path: List[str], expected_path: List[str]) -> bool:
        """Check if actual execution path matches expected path reasonably"""
        if not expected_path:
            return True
        
        # Check if all expected steps are present in order (allowing extra steps)
        expected_index = 0
        for step in actual_path:
            if expected_index < len(expected_path) and step == expected_path[expected_index]:
                expected_index += 1
        
        return expected_index == len(expected_path)
    
    def _calculate_path_similarity(self, actual_path: List[str], expected_path: List[str]) -> float:
        """Calculate similarity between actual and expected execution paths"""
        if not expected_path:
            return 1.0
        
        if not actual_path:
            return 0.0
        
        # Calculate how many expected steps were executed in order
        expected_index = 0
        matched_steps = 0
        
        for step in actual_path:
            if expected_index < len(expected_path) and step == expected_path[expected_index]:
                matched_steps += 1
                expected_index += 1
        
        return matched_steps / len(expected_path)
    
    async def run_all_orchestration_evaluations(self) -> Dict[str, Any]:
        """Run all orchestration evaluation test cases"""
        test_cases = self.create_orchestration_test_cases()
        self.results = []
        
        logger.info(f"🚀 Starting orchestration evaluation with {len(test_cases)} test cases...")
        
        for test_case in test_cases:
            logger.info(f"📝 Running orchestration test: {test_case.name}")
            result = await self.evaluate_single_orchestration_test(test_case)
            self.results.append(result)
            
            # Log result
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"{status} {test_case.name} - Score: {result.score:.2f}")
        
        # Generate summary report
        return self._generate_orchestration_summary_report()
    
    def _generate_orchestration_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report for orchestration evaluation"""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        avg_score = sum(r.score for r in self.results) / total_tests if total_tests > 0 else 0
        avg_execution_time = sum(r.execution_time for r in self.results) / total_tests if total_tests > 0 else 0
        
        # Specific orchestration metrics
        workflow_completion_rate = sum(1 for r in self.results if r.workflow_completed) / total_tests if total_tests > 0 else 0
        validation_success_rate = sum(1 for r in self.results if r.validation_passed) / total_tests if total_tests > 0 else 0
        human_input_handling_rate = sum(1 for r in self.results if r.human_input_handled) / total_tests if total_tests > 0 else 0
        
        def clean_for_json(obj):
            """Recursively clean objects for JSON serialization"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            else:
                return obj
        
        report = {
            "summary": {
                "evaluation_type": "orchestrator_agent_with_validation",
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0,
                "average_score": avg_score,
                "average_execution_time": avg_execution_time,
                "workflow_completion_rate": workflow_completion_rate * 100,
                "validation_success_rate": validation_success_rate * 100,
                "human_input_handling_rate": human_input_handling_rate * 100
            },
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "score": r.score,
                    "execution_time": r.execution_time,
                    "workflow_completed": r.workflow_completed,
                    "validation_passed": r.validation_passed,
                    "human_input_handled": r.human_input_handled,
                    "error": r.error_message,
                    "details": clean_for_json(r.details)
                }
                for r in self.results
            ],
            "orchestration_metrics": {
                "routing_accuracy": self._calculate_routing_accuracy(),
                "validation_integration": self._analyze_validation_integration(),
                "error_handling_effectiveness": self._analyze_error_handling(),
                "workflow_patterns": self._analyze_workflow_patterns()
            },
            "recommendations": self._generate_orchestration_recommendations()
        }
        
        return report
    
    def _calculate_routing_accuracy(self) -> Dict[str, float]:
        """Calculate routing accuracy by different scenarios"""
        routing_scenarios = {
            "initial_workflow": [],
            "validation_routing": [],
            "completion_routing": [],
            "error_recovery": []
        }
        
        for result in self.results:
            if "initial" in result.test_name:
                routing_scenarios["initial_workflow"].append(result.score)
            elif "validation" in result.test_name:
                routing_scenarios["validation_routing"].append(result.score)
            elif "completion" in result.test_name or "complete" in result.test_name:
                routing_scenarios["completion_routing"].append(result.score)
            elif "error" in result.test_name or "recovery" in result.test_name:
                routing_scenarios["error_recovery"].append(result.score)
        
        return {
            scenario: sum(scores) / len(scores) if scores else 0.0
            for scenario, scores in routing_scenarios.items()
        }
    
    def _analyze_validation_integration(self) -> Dict[str, Any]:
        """Analyze how well orchestrator integrates with validation"""
        validation_tests = [r for r in self.results if "validation" in r.test_name]
        
        if not validation_tests:
            return {"status": "no_validation_tests"}
        
        validation_success = sum(1 for r in validation_tests if r.validation_passed)
        human_input_handled = sum(1 for r in validation_tests if r.human_input_handled)
        
        return {
            "validation_routing_accuracy": sum(r.score for r in validation_tests) / len(validation_tests),
            "validation_success_rate": validation_success / len(validation_tests) if validation_tests else 0,
            "human_input_handling_rate": human_input_handled / len(validation_tests) if validation_tests else 0,
            "total_validation_tests": len(validation_tests)
        }
    
    def _analyze_error_handling(self) -> Dict[str, Any]:
        """Analyze error handling effectiveness"""
        error_tests = [r for r in self.results if "error" in r.test_name or "attempts" in r.test_name]
        
        if not error_tests:
            return {"status": "no_error_tests"}
        
        return {
            "error_detection_accuracy": sum(r.score for r in error_tests) / len(error_tests),
            "appropriate_termination_rate": sum(1 for r in error_tests if not r.workflow_completed) / len(error_tests),
            "total_error_tests": len(error_tests)
        }
    
    def _analyze_workflow_patterns(self) -> List[str]:
        """Analyze common workflow execution patterns"""
        patterns = []
        
        for result in self.results:
            execution_path = result.details.get("execution_path", [])
            if execution_path:
                pattern = " → ".join(execution_path[:5])  # First 5 steps
                patterns.append(f"{result.test_name}: {pattern}")
        
        return patterns
    
    def _generate_orchestration_recommendations(self) -> List[str]:
        """Generate improvement recommendations for orchestration"""
        recommendations = []
        
        failed_results = [r for r in self.results if not r.passed]
        
        if len(failed_results) > len(self.results) * 0.3:
            recommendations.append("High orchestration failure rate detected. Review core routing logic and decision-making criteria.")
        
        validation_failures = [r for r in failed_results if "validation" in r.test_name]
        if validation_failures:
            recommendations.append("Validation integration issues detected. Review orchestrator's handling of validation results and human input requirements.")
        
        completion_issues = [r for r in self.results if not r.workflow_completed and "complete" in r.details.get("expected_path", [])]
        if completion_issues:
            recommendations.append("Workflow completion issues detected. Review completion criteria and termination conditions.")
        
        error_handling_issues = [r for r in failed_results if "error" in r.test_name]
        if error_handling_issues:
            recommendations.append("Error handling needs improvement. Review error detection and recovery mechanisms.")
        
        return recommendations


# Test runner and CLI interface
async def main():
    """Main test runner for orchestration evaluation"""
    evaluator = EnhancedOrchestratorEvaluator()
    
    print("🔬 Enhanced Orchestrator Agent Evaluation Framework")
    print("=" * 70)
    
    # Run evaluations
    report = await evaluator.run_all_orchestration_evaluations()
    
    # Print summary
    summary = report["summary"]
    print(f"\n📊 ORCHESTRATION EVALUATION SUMMARY")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"Average Score: {summary['average_score']:.3f}")
    print(f"Workflow Completion Rate: {summary['workflow_completion_rate']:.1f}%")
    print(f"Validation Success Rate: {summary['validation_success_rate']:.1f}%")
    print(f"Human Input Handling Rate: {summary['human_input_handling_rate']:.1f}%")
    print(f"Average Execution Time: {summary['average_execution_time']:.2f}s")
    
    # Print orchestration metrics
    if "orchestration_metrics" in report:
        print(f"\n📈 ORCHESTRATION METRICS:")
        routing_accuracy = report["orchestration_metrics"]["routing_accuracy"]
        for scenario, accuracy in routing_accuracy.items():
            print(f"  {scenario.replace('_', ' ').title()}: {accuracy:.3f}")
    
    # Print recommendations
    if report["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"orchestrator_eval_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())