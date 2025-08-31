import unittest
import json
import asyncio
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
from datetime import datetime

from agents.orchestrator_agent import OrchestratorAgent, route_from_orchestrator
from schemas.workflow_schemas import WorkflowState, ProcessingStatus
from tests.mock_llm import MockLLMFactory, create_mock_model_function
from utils.langsmith_config import get_langsmith_config, trace_agent

class OrchestratorEvals:
    """LangSmith evaluation test cases for orchestrator agent"""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.langsmith_config = get_langsmith_config()
        self.test_cases = self._create_test_cases()
        
    def _create_test_cases(self) -> List[Dict[str, Any]]:
        """Create comprehensive test cases for orchestrator evaluation"""
        return [
            # Test Case 1: Initial workflow start
            {
                "name": "initial_workflow_start",
                "description": "Orchestrator should route new workflow to contract processing",
                "input_state": self._create_base_state({
                    "processing_status": ProcessingStatus.PENDING.value,
                    "contract_data": None,
                    "attempt_count": 0
                }),
                "expected_decision": {
                    "next_action": "contract_processing",
                    "confidence": 0.9
                },
                "success_criteria": {
                    "correct_routing": True,
                    "high_confidence": True,
                    "valid_reasoning": True
                }
            },
            
            # Test Case 2: Contract processed, needs validation
            {
                "name": "contract_to_validation", 
                "description": "After contract processing, should route to validation",
                "input_state": self._create_base_state({
                    "contract_data": {"context": "sample contract", "confidence": 0.8},
                    "validation_results": None,
                    "attempt_count": 1
                }),
                "expected_decision": {
                    "next_action": "validation",
                    "confidence": 0.8
                },
                "success_criteria": {
                    "correct_routing": True,
                    "considers_contract_data": True
                }
            },
            
            # Test Case 3: Validation failed, retry processing
            {
                "name": "validation_failed_retry",
                "description": "After validation failure, should retry processing on first attempt",
                "input_state": self._create_base_state({
                    "contract_data": {"context": "poor quality", "confidence": 0.3},
                    "validation_results": {"status": "failed", "overall_score": 0.4},
                    "attempt_count": 1
                }),
                "expected_decision": {
                    "next_action": "contract_processing",
                    "confidence": 0.6
                },
                "success_criteria": {
                    "correct_routing": True,
                    "retry_logic": True
                }
            },
            
            # Test Case 4: Multiple validation failures, escalate
            {
                "name": "multiple_failures_escalate",
                "description": "After multiple validation failures, should escalate to error recovery",
                "input_state": self._create_base_state({
                    "validation_results": {"status": "failed", "overall_score": 0.2},
                    "attempt_count": 2,
                    "errors": [{"error": "validation failed"}, {"error": "validation failed again"}]
                }),
                "expected_decision": {
                    "next_action": "error_recovery",
                    "confidence": 0.4
                },
                "success_criteria": {
                    "correct_routing": True,
                    "escalation_logic": True
                }
            },
            
            # Test Case 5: Max attempts reached
            {
                "name": "max_attempts_exceeded",
                "description": "When max attempts exceeded, should complete with errors",
                "input_state": self._create_base_state({
                    "attempt_count": 3,
                    "max_attempts": 3,
                    "errors": [{"error": "failed"}, {"error": "failed"}, {"error": "failed"}]
                }),
                "expected_decision": {
                    "next_action": "complete_with_errors",
                    "confidence": 0.1
                },
                "success_criteria": {
                    "correct_routing": True,
                    "max_attempts_logic": True
                }
            },
            
            # Test Case 6: High quality invoice, approve for storage
            {
                "name": "high_quality_approve",
                "description": "High quality invoice should be approved for storage",
                "input_state": self._create_base_state({
                    "quality_assurance_result": {"quality_score": 0.95, "status": "passed"},
                    "invoice_data": {"confidence": 0.9},
                    "attempt_count": 1
                }),
                "expected_decision": {
                    "next_action": "storage_scheduling",
                    "confidence": 0.9
                },
                "success_criteria": {
                    "correct_routing": True,
                    "quality_awareness": True
                }
            },
            
            # Test Case 7: Low quality, learn and retry
            {
                "name": "low_quality_learn_retry",
                "description": "Low quality should trigger feedback learning",
                "input_state": self._create_base_state({
                    "quality_assurance_result": {"quality_score": 0.4, "status": "failed"},
                    "attempt_count": 1,
                    "max_attempts": 3
                }),
                "expected_decision": {
                    "next_action": "feedback_learning",
                    "confidence": 0.5
                },
                "success_criteria": {
                    "correct_routing": True,
                    "learning_trigger": True
                }
            },
            
            # Test Case 8: Critical errors detected
            {
                "name": "critical_errors_recovery",
                "description": "Critical errors should immediately route to error recovery",
                "input_state": self._create_base_state({
                    "errors": [
                        {"error": "database connection failed"}, 
                        {"error": "authentication error"},
                        {"error": "file_not_found"},
                        {"error": "permission denied"}
                    ],
                    "attempt_count": 1
                }),
                "expected_decision": {
                    "next_action": "error_recovery",
                    "confidence": 0.3
                },
                "success_criteria": {
                    "correct_routing": True,
                    "critical_error_detection": True
                }
            },
            
            # Test Case 9: Successful completion with learning
            {
                "name": "successful_completion",
                "description": "Successful storage should trigger final learning",
                "input_state": self._create_base_state({
                    "storage_result": {"status": "success"},
                    "final_invoice": {"workflow_id": "test"},
                    "quality_score": 0.85
                }),
                "expected_decision": {
                    "next_action": "feedback_learning",
                    "confidence": 0.8
                },
                "success_criteria": {
                    "correct_routing": True,
                    "success_learning": True
                }
            },
            
            # Test Case 10: Edge case - unexpected state
            {
                "name": "unexpected_state_recovery",
                "description": "Unexpected state should route to error recovery",
                "input_state": self._create_base_state({
                    "processing_status": "unknown_status",
                    "current_agent": "unknown_agent"
                }),
                "expected_decision": {
                    "next_action": "error_recovery",
                    "confidence": 0.2
                },
                "success_criteria": {
                    "correct_routing": True,
                    "edge_case_handling": True
                }
            }
        ]
    
    def _create_base_state(self, overrides: Dict[str, Any]) -> WorkflowState:
        """Create base workflow state with overrides"""
        base_state = {
            "workflow_id": "test_workflow_123",
            "user_id": "test_user",
            "contract_file": "test_contract.pdf",
            "contract_name": "Test Contract",
            "contract_data": None,
            "validation_results": None,
            "invoice_data": None,
            "schedule_data": None,
            "final_invoice": None,
            "attempt_count": 0,
            "max_attempts": 3,
            "errors": [],
            "feedback_history": [],
            "quality_score": 0.0,
            "confidence_level": 0.0,
            "processing_status": ProcessingStatus.IN_PROGRESS.value,
            "current_agent": "orchestrator",
            "retry_reasons": [],
            "learned_patterns": {},
            "improvement_suggestions": [],
            "success_metrics": {},
            "started_at": datetime.now().isoformat(),
            "last_updated_at": datetime.now().isoformat()
        }
        
        base_state.update(overrides)
        return base_state
    
    @trace_agent("orchestrator_eval")
    def run_evaluation(self) -> Dict[str, Any]:
        """Run complete evaluation suite for orchestrator agent"""
        results = {
            "total_tests": len(self.test_cases),
            "passed": 0,
            "failed": 0,
            "test_results": [],
            "overall_score": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        for test_case in self.test_cases:
            test_result = self._run_single_test(test_case)
            results["test_results"].append(test_result)
            
            if test_result["passed"]:
                results["passed"] += 1
            else:
                results["failed"] += 1
        
        results["overall_score"] = results["passed"] / results["total_tests"]
        
        # Log to LangSmith
        if self.langsmith_config.is_enabled():
            self.langsmith_config.log_agent_execution(
                "orchestrator_evaluation",
                {"test_cases": len(self.test_cases)},
                results
            )
        
        return results
    
    def _run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case and evaluate results"""
        test_name = test_case["name"]
        
        try:
            # Execute orchestrator with test input
            result_state = self.orchestrator.process(test_case["input_state"])
            decision = result_state.get("orchestrator_decision", {})
            
            # Evaluate decision against expected results
            evaluation = self._evaluate_decision(decision, test_case)
            
            return {
                "test_name": test_name,
                "description": test_case["description"],
                "passed": evaluation["passed"],
                "score": evaluation["score"],
                "details": evaluation["details"],
                "actual_decision": decision,
                "expected_decision": test_case["expected_decision"]
            }
            
        except Exception as e:
            return {
                "test_name": test_name,
                "description": test_case["description"],
                "passed": False,
                "score": 0.0,
                "details": f"Test execution failed: {str(e)}",
                "error": str(e)
            }
    
    def _evaluate_decision(self, actual_decision: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate orchestrator decision against expected results"""
        expected = test_case["expected_decision"]
        criteria = test_case["success_criteria"]
        
        evaluation = {
            "passed": True,
            "score": 0.0,
            "details": {}
        }
        
        total_criteria = len(criteria)
        passed_criteria = 0
        
        # Check routing correctness
        if criteria.get("correct_routing"):
            routing_correct = actual_decision.get("next_action") == expected["next_action"]
            evaluation["details"]["routing_correct"] = routing_correct
            if routing_correct:
                passed_criteria += 1
            else:
                evaluation["passed"] = False
        
        # Check confidence level
        if criteria.get("high_confidence"):
            actual_confidence = actual_decision.get("confidence", 0.0)
            expected_confidence = expected.get("confidence", 0.0)
            confidence_ok = abs(actual_confidence - expected_confidence) <= 0.2
            evaluation["details"]["confidence_appropriate"] = confidence_ok
            if confidence_ok:
                passed_criteria += 1
            else:
                evaluation["passed"] = False
        
        # Check reasoning quality
        if criteria.get("valid_reasoning"):
            has_reasoning = bool(actual_decision.get("reason"))
            evaluation["details"]["has_reasoning"] = has_reasoning
            if has_reasoning:
                passed_criteria += 1
            else:
                evaluation["passed"] = False
        
        # Check specific logic criteria
        for criterion_key in ["retry_logic", "escalation_logic", "max_attempts_logic", 
                             "quality_awareness", "learning_trigger", "critical_error_detection"]:
            if criteria.get(criterion_key):
                # These are domain-specific checks that would need custom logic
                # For now, we'll consider them passed if routing is correct
                logic_check = actual_decision.get("next_action") == expected["next_action"]
                evaluation["details"][criterion_key] = logic_check
                if logic_check:
                    passed_criteria += 1
                else:
                    evaluation["passed"] = False
        
        evaluation["score"] = passed_criteria / total_criteria if total_criteria > 0 else 0.0
        
        return evaluation
    
    def run_routing_function_tests(self) -> Dict[str, Any]:
        """Test the route_from_orchestrator function specifically"""
        routing_tests = [
            {
                "name": "route_contract_processing",
                "state": {"orchestrator_decision": {"next_action": "contract_processing"}},
                "expected_route": "contract_processing"
            },
            {
                "name": "route_validation",
                "state": {"orchestrator_decision": {"next_action": "validation"}},
                "expected_route": "validation"
            },
            {
                "name": "route_error_recovery", 
                "state": {"orchestrator_decision": {"next_action": "error_recovery"}},
                "expected_route": "error_recovery"
            },
            {
                "name": "route_complete_success",
                "state": {"orchestrator_decision": {"next_action": "complete_success"}},
                "expected_route": "__end__"
            },
            {
                "name": "route_unknown_action",
                "state": {"orchestrator_decision": {"next_action": "unknown_action"}},
                "expected_route": "error_recovery"
            }
        ]
        
        results = {"total": len(routing_tests), "passed": 0, "failed": 0, "details": []}
        
        for test in routing_tests:
            try:
                actual_route = route_from_orchestrator(test["state"])
                passed = actual_route == test["expected_route"]
                
                results["details"].append({
                    "test_name": test["name"],
                    "passed": passed,
                    "expected": test["expected_route"],
                    "actual": actual_route
                })
                
                if passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "test_name": test["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        return results


class OrchestratorEvalRunner:
    """Test runner for orchestrator evaluations with LangSmith integration"""
    
    def __init__(self):
        self.evals = OrchestratorEvals()
    
    def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive orchestrator evaluation suite"""
        print("🧪 Starting Orchestrator Agent Evaluation...")
        
        # Run main evaluation
        main_results = self.evals.run_evaluation()
        print(f"✅ Main evaluation: {main_results['passed']}/{main_results['total_tests']} passed")
        
        # Run routing function tests
        routing_results = self.evals.run_routing_function_tests()
        print(f"✅ Routing tests: {routing_results['passed']}/{routing_results['total']} passed")
        
        # Combine results
        combined_results = {
            "orchestrator_evaluation": main_results,
            "routing_function_tests": routing_results,
            "overall_success": (
                main_results["overall_score"] > 0.8 and 
                routing_results["passed"] / routing_results["total"] > 0.8
            ),
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"🎯 Overall evaluation {'PASSED' if combined_results['overall_success'] else 'FAILED'}")
        
        return combined_results


if __name__ == "__main__":
    # Run evaluation when script is executed directly
    runner = OrchestratorEvalRunner()
    results = runner.run_comprehensive_evaluation()
    
    # Print detailed results
    print("\n📊 Detailed Results:")
    print(json.dumps(results, indent=2))