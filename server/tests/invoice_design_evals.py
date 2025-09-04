#!/usr/bin/env python3
"""
Comprehensive evaluation suite for InvoiceDesignAgent

This module provides detailed evaluation capabilities for the invoice design generation
functionality, including design quality assessment, component validation, and error handling.
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, AsyncMock

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.invoice_design_agent import InvoiceDesignAgent
from schemas.workflow_schemas import WorkflowState, ProcessingStatus, AgentType
from tests.mock_llm import MockLLMFactory, MockVertexAIModel
from services.database_service import DatabaseService

class InvoiceDesignEvaluator:
    """Comprehensive evaluator for InvoiceDesignAgent performance"""
    
    def __init__(self):
        self.agent = InvoiceDesignAgent()
        self.test_results = []
        self.performance_metrics = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "average_response_time": 0,
            "design_quality_scores": [],
            "component_completeness_scores": []
        }
    
    def create_test_invoice_data(self, scenario: str = "default") -> Dict[str, Any]:
        """Create test invoice data for different scenarios"""
        
        scenarios = {
            "default": {
                "invoice_header": {
                    "invoice_number": "INV-2024-001",
                    "invoice_date": "2024-01-15",
                    "due_date": "2024-02-15"
                },
                "parties": {
                    "client": {
                        "name": "Acme Corporation",
                        "email": "billing@acme.com",
                        "address": "123 Business Ave\nNew York, NY 10001"
                    },
                    "service_provider": {
                        "name": "Design Studio Pro",
                        "email": "hello@designstudio.com",
                        "address": "456 Creative Blvd\nLos Angeles, CA 90210"
                    }
                },
                "payment_terms": {
                    "amount": 2500,
                    "currency": "USD",
                    "frequency": "one-time"
                },
                "contract_title": "Brand Identity Design Package",
                "services": [
                    {
                        "description": "Logo Design",
                        "quantity": 1,
                        "unit_price": 1500,
                        "total_amount": 1500
                    },
                    {
                        "description": "Brand Guidelines",
                        "quantity": 1,
                        "unit_price": 1000,
                        "total_amount": 1000
                    }
                ]
            },
            "complex": {
                "invoice_header": {
                    "invoice_number": "INV-2024-COMP-007",
                    "invoice_date": "2024-01-20",
                    "due_date": "2024-03-01"
                },
                "parties": {
                    "client": {
                        "name": "Global Tech Solutions International Ltd.",
                        "email": "procurement@globaltech.enterprise.com",
                        "address": "Level 45, Corporate Tower\n100 Business District\nNew York, NY 10001\nUSA"
                    },
                    "service_provider": {
                        "name": "Advanced Software Engineering Consultancy LLC",
                        "email": "invoicing@advancedsoftware.com",
                        "address": "Suite 1200, Innovation Hub\n789 Technology Boulevard\nSan Francisco, CA 94107\nUSA"
                    }
                },
                "payment_terms": {
                    "amount": 75000,
                    "currency": "USD",
                    "frequency": "quarterly"
                },
                "contract_title": "Enterprise Software Development & Consulting Services",
                "services": [
                    {
                        "description": "Full-Stack Development Services",
                        "quantity": 3,
                        "unit_price": 15000,
                        "total_amount": 45000
                    },
                    {
                        "description": "DevOps & Cloud Infrastructure Setup",
                        "quantity": 1,
                        "unit_price": 20000,
                        "total_amount": 20000
                    },
                    {
                        "description": "Code Review & Quality Assurance",
                        "quantity": 2,
                        "unit_price": 5000,
                        "total_amount": 10000
                    }
                ]
            },
            "minimal": {
                "invoice_header": {
                    "invoice_number": "INV-MIN-001",
                    "invoice_date": "2024-01-01"
                },
                "parties": {
                    "client": {
                        "name": "Jane Doe"
                    },
                    "service_provider": {
                        "name": "Freelancer Services"
                    }
                },
                "payment_terms": {
                    "amount": 500,
                    "currency": "USD"
                },
                "contract_title": "Consultation Services",
                "services": [
                    {
                        "description": "1-hour consultation",
                        "quantity": 1,
                        "unit_price": 500,
                        "total_amount": 500
                    }
                ]
            }
        }
        
        return scenarios.get(scenario, scenarios["default"])
    
    def create_test_state(self, invoice_data: Dict[str, Any], scenario: str = "default") -> WorkflowState:
        """Create test workflow state"""
        return {
            "workflow_id": f"eval-test-{scenario}-{int(time.time())}",
            "user_id": f"eval-user-{scenario}",
            "contract_name": f"Test Contract - {scenario.title()}",
            "invoice_created": True,
            "invoice_id": f"eval-invoice-{scenario}-{int(time.time())}",
            "processing_status": ProcessingStatus.IN_PROGRESS.value,
            "attempt_count": 1,
            "max_attempts": 3,
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "invoice_data": invoice_data
        }
    
    async def evaluate_basic_functionality(self) -> Dict[str, Any]:
        """Test basic design generation functionality"""
        print("🧪 Evaluating basic design generation functionality...")
        
        test_result = {
            "test_name": "basic_functionality",
            "passed": False,
            "details": {},
            "errors": []
        }
        
        try:
            # Create test data
            invoice_data = self.create_test_invoice_data("default")
            state = self.create_test_state(invoice_data)
            
            # Mock dependencies
            with patch('agents.invoice_design_agent.get_model') as mock_get_model, \
                 patch('agents.invoice_design_agent.get_database_service') as mock_db_service:
                
                # Setup mocks
                mock_llm = self._create_comprehensive_mock_llm()
                mock_get_model.return_value = mock_llm
                
                mock_db = Mock()
                mock_invoice = Mock()
                mock_invoice.invoice_data = invoice_data
                mock_db.get_invoice_by_id.return_value = mock_invoice
                mock_db_service.return_value = mock_db
                
                agent = InvoiceDesignAgent()
                
                # Execute
                start_time = time.time()
                result_state = await agent.process(state)
                end_time = time.time()
                
                # Evaluate results
                test_result["details"]["response_time"] = end_time - start_time
                test_result["details"]["processing_status"] = result_state.get("processing_status")
                test_result["details"]["design_generation_completed"] = result_state.get("design_generation_completed")
                
                if (result_state.get("processing_status") == ProcessingStatus.SUCCESS.value and
                    result_state.get("design_generation_completed") and
                    "invoice_designs" in result_state):
                    
                    designs = result_state["invoice_designs"]
                    test_result["details"]["design_count"] = len(designs.get("designs", []))
                    test_result["details"]["designs_generated"] = [d.get("design_name") for d in designs.get("designs", [])]
                    
                    # Verify all 3 expected designs are present
                    expected_designs = ["Modern & Clean", "Classic & Professional", "Bold & Creative"]
                    actual_designs = [d.get("design_name") for d in designs.get("designs", [])]
                    
                    test_result["details"]["all_designs_present"] = all(design in actual_designs for design in expected_designs)
                    test_result["passed"] = test_result["details"]["all_designs_present"] and len(designs.get("designs", [])) == 3
                else:
                    test_result["errors"].append("Design generation failed or incomplete")
                    
        except Exception as e:
            test_result["errors"].append(f"Exception during basic functionality test: {str(e)}")
        
        return test_result
    
    async def evaluate_design_quality(self) -> Dict[str, Any]:
        """Evaluate the quality and completeness of generated designs"""
        print("🎨 Evaluating design quality and completeness...")
        
        test_result = {
            "test_name": "design_quality",
            "passed": False,
            "details": {},
            "errors": []
        }
        
        try:
            invoice_data = self.create_test_invoice_data("complex")
            state = self.create_test_state(invoice_data, "complex")
            
            # Mock dependencies
            with patch('agents.invoice_design_agent.get_model') as mock_get_model, \
                 patch('agents.invoice_design_agent.get_database_service') as mock_db_service:
                
                mock_llm = self._create_comprehensive_mock_llm()
                mock_get_model.return_value = mock_llm
                
                mock_db = Mock()
                mock_invoice = Mock()
                mock_invoice.invoice_data = invoice_data
                mock_db.get_invoice_by_id.return_value = mock_invoice
                mock_db_service.return_value = mock_db
                
                agent = InvoiceDesignAgent()
                result_state = await agent.process(state)
                
                if result_state.get("processing_status") == ProcessingStatus.SUCCESS.value:
                    designs = result_state["invoice_designs"]["designs"]
                    
                    quality_scores = []
                    component_scores = []
                    
                    for design in designs:
                        # Evaluate design structure
                        design_quality = self._evaluate_design_structure(design)
                        component_completeness = self._evaluate_component_completeness(design)
                        
                        quality_scores.append(design_quality)
                        component_scores.append(component_completeness)
                        
                        test_result["details"][f"{design.get('design_name', 'Unknown')}_quality"] = design_quality
                        test_result["details"][f"{design.get('design_name', 'Unknown')}_completeness"] = component_completeness
                    
                    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
                    avg_completeness = sum(component_scores) / len(component_scores) if component_scores else 0
                    
                    test_result["details"]["average_quality_score"] = avg_quality
                    test_result["details"]["average_completeness_score"] = avg_completeness
                    
                    # Pass if both averages are above 0.7 (70%)
                    test_result["passed"] = avg_quality >= 0.7 and avg_completeness >= 0.7
                    
                    # Store for performance metrics
                    self.performance_metrics["design_quality_scores"].extend(quality_scores)
                    self.performance_metrics["component_completeness_scores"].extend(component_scores)
                else:
                    test_result["errors"].append("Design generation failed")
                    
        except Exception as e:
            test_result["errors"].append(f"Exception during design quality test: {str(e)}")
        
        return test_result
    
    async def evaluate_error_handling(self) -> Dict[str, Any]:
        """Test error handling capabilities"""
        print("🚨 Evaluating error handling capabilities...")
        
        test_result = {
            "test_name": "error_handling",
            "passed": False,
            "details": {},
            "errors": []
        }
        
        try:
            # Test 1: No invoice data
            with patch('agents.invoice_design_agent.get_model') as mock_get_model, \
                 patch('agents.invoice_design_agent.get_database_service') as mock_db_service:
                
                mock_get_model.return_value = MockLLMFactory.create_reliable_llm()
                
                mock_db = Mock()
                mock_db.get_invoice_by_id.return_value = None
                mock_db.get_invoice_by_workflow_id.return_value = None
                mock_db_service.return_value = mock_db
                
                agent = InvoiceDesignAgent()
                state = self.create_test_state({}, "no_data")
                
                result = await agent.process(state)
                
                test_result["details"]["no_data_handling"] = {
                    "status": result.get("processing_status"),
                    "has_errors": len(result.get("errors", [])) > 0,
                    "error_message": result.get("errors", [{}])[-1].get("error", "") if result.get("errors") else ""
                }
            
            # Test 2: LLM failure
            with patch('agents.invoice_design_agent.get_model') as mock_get_model, \
                 patch('agents.invoice_design_agent.get_database_service') as mock_db_service:
                
                mock_llm = Mock()
                mock_llm.generate_content_async = AsyncMock(side_effect=Exception("Mock LLM Failure"))
                mock_get_model.return_value = mock_llm
                
                mock_db = Mock()
                mock_invoice = Mock()
                mock_invoice.invoice_data = self.create_test_invoice_data("default")
                mock_db.get_invoice_by_id.return_value = mock_invoice
                mock_db_service.return_value = mock_db
                
                agent = InvoiceDesignAgent()
                state = self.create_test_state(self.create_test_invoice_data("default"), "llm_failure")
                
                result = await agent.process(state)
                
                test_result["details"]["llm_failure_handling"] = {
                    "status": result.get("processing_status"),
                    "has_errors": len(result.get("errors", [])) > 0,
                    "error_message": result.get("errors", [{}])[-1].get("error", "") if result.get("errors") else ""
                }
            
            # Test 3: Invalid JSON response
            with patch('agents.invoice_design_agent.get_model') as mock_get_model, \
                 patch('agents.invoice_design_agent.get_database_service') as mock_db_service:
                
                mock_llm = Mock()
                mock_response = Mock()
                mock_response.text = "This is not valid JSON"
                mock_llm.generate_content_async = AsyncMock(return_value=mock_response)
                mock_get_model.return_value = mock_llm
                
                mock_db = Mock()
                mock_invoice = Mock()
                mock_invoice.invoice_data = self.create_test_invoice_data("default")
                mock_db.get_invoice_by_id.return_value = mock_invoice
                mock_db_service.return_value = mock_db
                
                agent = InvoiceDesignAgent()
                state = self.create_test_state(self.create_test_invoice_data("default"), "invalid_json")
                
                result = await agent.process(state)
                
                test_result["details"]["invalid_json_handling"] = {
                    "status": result.get("processing_status"),
                    "has_errors": len(result.get("errors", [])) > 0,
                    "error_message": result.get("errors", [{}])[-1].get("error", "") if result.get("errors") else ""
                }
            
            # Evaluate if all error cases were handled properly
            error_tests = [
                test_result["details"]["no_data_handling"]["status"] == ProcessingStatus.FAILED.value,
                test_result["details"]["llm_failure_handling"]["status"] == ProcessingStatus.FAILED.value,
                test_result["details"]["invalid_json_handling"]["status"] == ProcessingStatus.FAILED.value,
                all([
                    test_result["details"]["no_data_handling"]["has_errors"],
                    test_result["details"]["llm_failure_handling"]["has_errors"],
                    test_result["details"]["invalid_json_handling"]["has_errors"]
                ])
            ]
            
            test_result["passed"] = all(error_tests)
            test_result["details"]["all_error_cases_handled"] = test_result["passed"]
            
        except Exception as e:
            test_result["errors"].append(f"Exception during error handling test: {str(e)}")
        
        return test_result
    
    async def evaluate_performance(self) -> Dict[str, Any]:
        """Evaluate performance under various load conditions"""
        print("⚡ Evaluating performance metrics...")
        
        test_result = {
            "test_name": "performance",
            "passed": False,
            "details": {},
            "errors": []
        }
        
        try:
            # Test multiple concurrent requests
            scenarios = ["default", "complex", "minimal"]
            tasks = []
            
            with patch('agents.invoice_design_agent.get_model') as mock_get_model, \
                 patch('agents.invoice_design_agent.get_database_service') as mock_db_service:
                
                mock_llm = self._create_comprehensive_mock_llm()
                mock_get_model.return_value = mock_llm
                
                mock_db = Mock()
                mock_invoice = Mock()
                mock_db.get_invoice_by_id.return_value = mock_invoice
                mock_db.get_invoice_by_workflow_id.return_value = mock_invoice
                mock_db_service.return_value = mock_db
                
                # Create multiple agent instances for concurrent testing
                for i in range(5):  # 5 concurrent requests
                    for scenario in scenarios:
                        invoice_data = self.create_test_invoice_data(scenario)
                        mock_invoice.invoice_data = invoice_data
                        state = self.create_test_state(invoice_data, f"{scenario}_{i}")
                        
                        agent = InvoiceDesignAgent()
                        tasks.append(self._timed_process(agent, state))
                
                # Execute all tasks concurrently
                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # Analyze results
                successful_results = [r for r in results if not isinstance(r, Exception) and r[0].get("processing_status") == ProcessingStatus.SUCCESS.value]
                failed_results = [r for r in results if isinstance(r, Exception) or (hasattr(r, "__len__") and len(r) > 0 and r[0].get("processing_status") != ProcessingStatus.SUCCESS.value)]
                
                response_times = [r[1] for r in successful_results]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                test_result["details"]["total_requests"] = len(tasks)
                test_result["details"]["successful_requests"] = len(successful_results)
                test_result["details"]["failed_requests"] = len(failed_results)
                test_result["details"]["success_rate"] = len(successful_results) / len(tasks) if tasks else 0
                test_result["details"]["average_response_time"] = avg_response_time
                test_result["details"]["total_execution_time"] = total_time
                test_result["details"]["requests_per_second"] = len(tasks) / total_time if total_time > 0 else 0
                
                # Pass if success rate > 90% and average response time < 5 seconds
                test_result["passed"] = (
                    test_result["details"]["success_rate"] > 0.9 and
                    test_result["details"]["average_response_time"] < 5.0
                )
                
                # Update performance metrics
                self.performance_metrics["average_response_time"] = avg_response_time
                
        except Exception as e:
            test_result["errors"].append(f"Exception during performance test: {str(e)}")
        
        return test_result
    
    async def _timed_process(self, agent: InvoiceDesignAgent, state: WorkflowState):
        """Execute agent process with timing"""
        start_time = time.time()
        try:
            result = await agent.process(state)
            end_time = time.time()
            return result, end_time - start_time
        except Exception as e:
            end_time = time.time()
            return {"processing_status": ProcessingStatus.FAILED.value, "errors": [{"error": str(e)}]}, end_time - start_time
    
    def _evaluate_design_structure(self, design: Dict[str, Any]) -> float:
        """Evaluate the structure and quality of a single design"""
        score = 0.0
        max_score = 7.0
        
        # Check required fields
        if design.get("design_name"):
            score += 1.0
        if design.get("design_id"):
            score += 1.0
        if design.get("style_theme"):
            score += 1.0
        if design.get("components") and isinstance(design["components"], list):
            score += 1.0
            
            # Check component structure
            components = design["components"]
            if len(components) > 0:
                score += 0.5
                
                # Check for essential component types
                component_types = [comp.get("type") for comp in components]
                if "header" in component_types:
                    score += 0.5
                if any(comp_type in component_types for comp_type in ["client_info", "line_items", "summary"]):
                    score += 0.5
                
                # Check component completeness
                valid_components = 0
                for comp in components:
                    if (comp.get("type") and 
                        comp.get("props") and isinstance(comp["props"], dict) and
                        comp.get("styling") and isinstance(comp["styling"], dict)):
                        valid_components += 1
                
                if valid_components == len(components):
                    score += 0.5
        
        return min(score / max_score, 1.0)
    
    def _evaluate_component_completeness(self, design: Dict[str, Any]) -> float:
        """Evaluate completeness of components within a design"""
        if not design.get("components"):
            return 0.0
        
        components = design["components"]
        if not components:
            return 0.0
        
        essential_types = {"header", "client_info", "line_items", "summary"}
        present_types = {comp.get("type") for comp in components}
        
        # Score based on essential components present
        essential_score = len(essential_types.intersection(present_types)) / len(essential_types)
        
        # Score based on component data quality
        quality_scores = []
        for comp in components:
            comp_score = 0.0
            if comp.get("type"):
                comp_score += 0.25
            if comp.get("props") and isinstance(comp["props"], dict) and comp["props"]:
                comp_score += 0.25
            if comp.get("styling") and isinstance(comp["styling"], dict) and comp["styling"]:
                comp_score += 0.25
            if comp.get("props") and self._has_relevant_props(comp["type"], comp["props"]):
                comp_score += 0.25
            
            quality_scores.append(comp_score)
        
        quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Return weighted average
        return (essential_score * 0.6) + (quality_score * 0.4)
    
    def _has_relevant_props(self, component_type: str, props: Dict[str, Any]) -> bool:
        """Check if component has relevant props for its type"""
        type_requirements = {
            "header": ["title", "companyName"],
            "client_info": ["clientName", "providerName"], 
            "line_items": ["items"],
            "summary": ["total"]
        }
        
        required_props = type_requirements.get(component_type, [])
        return any(prop in props for prop in required_props)
    
    def _create_comprehensive_mock_llm(self):
        """Create a comprehensive mock LLM for testing"""
        mock_llm = Mock()
        
        # Create realistic design response
        design_response = {
            "designs": [
                {
                    "design_name": "Modern & Clean",
                    "design_id": "modern_clean",
                    "style_theme": "minimalist",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "Service Provider",
                                "invoiceNumber": "INV-001",
                                "date": "2024-01-15"
                            },
                            "styling": {
                                "backgroundColor": "#ffffff",
                                "fontFamily": "Arial, sans-serif",
                                "fontSize": "24px"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Client Name",
                                "providerName": "Provider Name"
                            },
                            "styling": {
                                "display": "grid",
                                "gridTemplateColumns": "1fr 1fr"
                            }
                        },
                        {
                            "type": "line_items",
                            "props": {
                                "items": []
                            },
                            "styling": {
                                "width": "100%"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "total": 1000,
                                "currency": "USD"
                            },
                            "styling": {
                                "textAlign": "right"
                            }
                        }
                    ]
                },
                {
                    "design_name": "Classic & Professional",
                    "design_id": "classic_professional",
                    "style_theme": "classic",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "INVOICE",
                                "companyName": "Service Provider"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "textAlign": "center"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Client Name",
                                "providerName": "Provider Name"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "total": 1000,
                                "currency": "USD"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "textAlign": "right"
                            }
                        }
                    ]
                },
                {
                    "design_name": "Bold & Creative",
                    "design_id": "bold_creative",
                    "style_theme": "creative",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "Service Provider"
                            },
                            "styling": {
                                "backgroundColor": "#3182ce",
                                "color": "#ffffff"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Client Name",
                                "providerName": "Provider Name"
                            },
                            "styling": {
                                "borderLeft": "4px solid #3182ce"
                            }
                        }
                    ]
                }
            ]
        }
        
        mock_response = Mock()
        mock_response.text = json.dumps(design_response)
        
        mock_llm.generate_content_async = AsyncMock(return_value=mock_response)
        
        return mock_llm
    
    async def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run all evaluation tests and generate comprehensive report"""
        print("🚀 Starting comprehensive InvoiceDesignAgent evaluation...")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all evaluation tests
        tests = [
            self.evaluate_basic_functionality(),
            self.evaluate_design_quality(),
            self.evaluate_error_handling(),
            self.evaluate_performance()
        ]
        
        results = await asyncio.gather(*tests)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Compile results
        passed_tests = sum(1 for result in results if result["passed"])
        total_tests = len(results)
        
        # Update performance metrics
        self.performance_metrics["total_tests"] = total_tests
        self.performance_metrics["passed_tests"] = passed_tests
        self.performance_metrics["failed_tests"] = total_tests - passed_tests
        
        # Generate comprehensive report
        evaluation_report = {
            "evaluation_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_evaluation_time": total_time,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": {result["test_name"]: result for result in results},
            "performance_metrics": self.performance_metrics,
            "overall_assessment": self._generate_overall_assessment(results),
            "recommendations": self._generate_recommendations(results)
        }
        
        self._print_evaluation_report(evaluation_report)
        
        return evaluation_report
    
    def _generate_overall_assessment(self, results: List[Dict[str, Any]]) -> str:
        """Generate overall assessment based on test results"""
        passed_tests = [r for r in results if r["passed"]]
        failed_tests = [r for r in results if not r["passed"]]
        
        if len(failed_tests) == 0:
            return "EXCELLENT: All tests passed. InvoiceDesignAgent is performing optimally."
        elif len(failed_tests) == 1:
            failed_test = failed_tests[0]["test_name"]
            return f"GOOD: Minor issues detected in {failed_test}. Overall performance is solid."
        elif len(failed_tests) == 2:
            failed_tests_names = [t["test_name"] for t in failed_tests]
            return f"NEEDS ATTENTION: Multiple issues detected in {', '.join(failed_tests_names)}."
        else:
            return "CRITICAL: Multiple system failures detected. Immediate attention required."
    
    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for result in results:
            if not result["passed"]:
                if result["test_name"] == "basic_functionality":
                    recommendations.append("Review core design generation logic and LLM integration")
                elif result["test_name"] == "design_quality":
                    recommendations.append("Improve design structure validation and component completeness")
                elif result["test_name"] == "error_handling":
                    recommendations.append("Strengthen error handling and recovery mechanisms")
                elif result["test_name"] == "performance":
                    recommendations.append("Optimize performance for concurrent requests and reduce response times")
        
        # Performance-based recommendations
        if self.performance_metrics["average_response_time"] > 3.0:
            recommendations.append("Consider optimizing LLM calls or implementing response caching")
        
        if not recommendations:
            recommendations.append("System is performing well. Consider monitoring for continued optimal performance.")
        
        return recommendations
    
    def _print_evaluation_report(self, report: Dict[str, Any]):
        """Print comprehensive evaluation report"""
        print("\n" + "=" * 80)
        print("🏆 INVOICE DESIGN AGENT EVALUATION REPORT")
        print("=" * 80)
        
        summary = report["evaluation_summary"]
        print(f"📊 Overall Results:")
        print(f"   Tests Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['success_rate']:.1%})")
        print(f"   Evaluation Time: {summary['total_evaluation_time']:.2f}s")
        print(f"   Timestamp: {summary['timestamp']}")
        
        print(f"\n📈 Performance Metrics:")
        metrics = report["performance_metrics"]
        if metrics["design_quality_scores"]:
            avg_quality = sum(metrics["design_quality_scores"]) / len(metrics["design_quality_scores"])
            print(f"   Average Design Quality: {avg_quality:.2f}")
        if metrics["component_completeness_scores"]:
            avg_completeness = sum(metrics["component_completeness_scores"]) / len(metrics["component_completeness_scores"])
            print(f"   Average Component Completeness: {avg_completeness:.2f}")
        if metrics["average_response_time"]:
            print(f"   Average Response Time: {metrics['average_response_time']:.2f}s")
        
        print(f"\n📋 Test Details:")
        for test_name, result in report["test_results"].items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"   {test_name}: {status}")
            if result["errors"]:
                for error in result["errors"]:
                    print(f"     - Error: {error}")
        
        print(f"\n🎯 Overall Assessment:")
        print(f"   {report['overall_assessment']}")
        
        print(f"\n💡 Recommendations:")
        for recommendation in report["recommendations"]:
            print(f"   - {recommendation}")
        
        print("=" * 80)


class InvoiceDesignEvalRunner:
    """Main evaluation runner for InvoiceDesignAgent"""
    
    @staticmethod
    async def run_comprehensive_evaluation_async() -> Dict[str, Any]:
        """Run comprehensive evaluation asynchronously and return results"""
        evaluator = InvoiceDesignEvaluator()
        return await evaluator.run_comprehensive_evaluation()
    
    @staticmethod
    def run_comprehensive_evaluation() -> Dict[str, Any]:
        """Run comprehensive evaluation and return results"""
        try:
            loop = asyncio.get_running_loop()
            # We're already in an event loop, so we need to run this differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(InvoiceDesignEvaluator().run_comprehensive_evaluation()))
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            evaluator = InvoiceDesignEvaluator()
            return asyncio.run(evaluator.run_comprehensive_evaluation())


if __name__ == "__main__":
    runner = InvoiceDesignEvalRunner()
    results = runner.run_comprehensive_evaluation()
    
    # Exit with appropriate code
    success_rate = results["evaluation_summary"]["success_rate"]
    exit_code = 0 if success_rate >= 0.8 else 1
    
    print(f"\n🏁 Evaluation completed with exit code: {exit_code}")
    exit(exit_code)