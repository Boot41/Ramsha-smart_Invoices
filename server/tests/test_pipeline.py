#!/usr/bin/env python3
"""
Test Pipeline with LangSmith Integration for Orchestrator Agent

This pipeline runs comprehensive tests on the agentic orchestrator with:
- LangSmith tracing and monitoring
- Mock LLM implementations
- Evaluation test cases
- Performance testing
- Integration testing

Usage:
    python tests/test_pipeline.py
"""

import os
import sys
import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import patch

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.orchestrator_evals import OrchestratorEvalRunner
from tests.test_orchestrator_with_mocks import TestOrchestratorWithMocks, TestOrchestratorPerformance
from tests.mock_llm import MockLLMFactory, create_mock_model_function
from utils.langsmith_config import get_langsmith_config, trace_workflow_step
from unittest.mock import Mock
from workflows.invoice_workflow import run_invoice_workflow, initialize_workflow_state
from services.orchestrator_service import OrchestratorService
from schemas.workflow_schemas import WorkflowRequest

class TestPipeline:
    """Main test pipeline with LangSmith integration"""
    
    def __init__(self):
        self.langsmith_config = get_langsmith_config()
        self.results = {
            "pipeline_start": datetime.now().isoformat(),
            "tests_completed": {},
            "overall_status": "running",
            "errors": []
        }
        
        print("🚀 Initializing Test Pipeline with LangSmith Integration")
        print(f"📊 LangSmith enabled: {self.langsmith_config.is_enabled()}")
        
    @trace_workflow_step("test_pipeline_execution")
    async def run_complete_pipeline(self) -> Dict[str, Any]:
        """Run the complete test pipeline with LangSmith tracing"""
        
        try:
            print("\n" + "="*60)
            print("🧪 STARTING ORCHESTRATOR AGENT TEST PIPELINE")
            print("="*60)
            
            # Step 1: Run Orchestrator Evaluations
            await self._run_orchestrator_evaluations()
            
            # Step 2: Run Unit Tests
            await self._run_unit_tests()
            
            # Step 3: Run Integration Tests
            await self._run_integration_tests()
            
            # Step 4: Run Invoice Design Agent Tests
            await self._run_invoice_design_tests()
            
            # Step 5: Run Performance Tests  
            await self._run_performance_tests()
            
            # Step 6: Run End-to-End Workflow Test (with design generation)
            await self._run_e2e_workflow_test()
            
            # Step 7: Run API Integration Tests
            await self._run_api_integration_tests()
            
            # Step 8: Generate Summary Report
            self._generate_summary_report()
            
            self.results["overall_status"] = "completed"
            self.results["pipeline_end"] = datetime.now().isoformat()
            
        except Exception as e:
            self.results["overall_status"] = "failed"
            self.results["errors"].append(str(e))
            print(f"❌ Pipeline failed: {str(e)}")
            
        return self.results
    
    @trace_workflow_step("orchestrator_evaluations")
    async def _run_orchestrator_evaluations(self):
        """Run LangSmith evaluations for orchestrator agent"""
        print("\n🎯 Step 1: Running Orchestrator Evaluations...")
        
        try:
            eval_runner = OrchestratorEvalRunner()
            eval_results = eval_runner.run_comprehensive_evaluation()
            
            self.results["tests_completed"]["orchestrator_evaluations"] = {
                "status": "passed" if eval_results["overall_success"] else "failed",
                "details": eval_results,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log to LangSmith
            if self.langsmith_config.is_enabled():
                self.langsmith_config.log_agent_execution(
                    "orchestrator_evaluation_pipeline",
                    {"evaluation_type": "comprehensive"},
                    eval_results
                )
            
            print(f"✅ Orchestrator Evaluations: {'PASSED' if eval_results['overall_success'] else 'FAILED'}")
            
        except Exception as e:
            print(f"❌ Orchestrator evaluations failed: {str(e)}")
            self.results["errors"].append(f"Orchestrator evaluations: {str(e)}")
    
    @trace_workflow_step("unit_tests")
    async def _run_unit_tests(self):
        """Run unittest suite with mocks"""
        print("\n🧪 Step 2: Running Unit Tests...")
        
        try:
            import unittest
            from io import StringIO
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(TestOrchestratorWithMocks)
            
            # Run tests with captured output
            stream = StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            
            with patch('models.llm.base.get_model') as mock_get_model:
                mock_llm = MockLLMFactory.create_reliable_llm()
                mock_get_model.return_value = mock_llm
                
                test_result = runner.run(suite)
            
            # Parse results
            success = test_result.wasSuccessful()
            tests_run = test_result.testsRun
            failures = len(test_result.failures)
            errors = len(test_result.errors)
            
            self.results["tests_completed"]["unit_tests"] = {
                "status": "passed" if success else "failed",
                "tests_run": tests_run,
                "failures": failures,
                "errors": errors,
                "details": stream.getvalue(),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ Unit Tests: {tests_run} tests run, {'PASSED' if success else 'FAILED'}")
            
        except Exception as e:
            print(f"❌ Unit tests failed: {str(e)}")
            self.results["errors"].append(f"Unit tests: {str(e)}")
    
    @trace_workflow_step("integration_tests")
    async def _run_integration_tests(self):
        """Run integration tests with mocked external services"""
        print("\n🔗 Step 3: Running Integration Tests...")
        
        try:
            # Test 1: Orchestrator + Workflow integration
            await self._test_orchestrator_workflow_integration()
            
            # Test 2: Service layer integration
            await self._test_service_layer_integration()
            
            # Test 3: API endpoint integration
            await self._test_api_integration()
            
            self.results["tests_completed"]["integration_tests"] = {
                "status": "passed",
                "timestamp": datetime.now().isoformat()
            }
            
            print("✅ Integration Tests: PASSED")
            
        except Exception as e:
            print(f"❌ Integration tests failed: {str(e)}")
            self.results["errors"].append(f"Integration tests: {str(e)}")
    
    @trace_workflow_step("invoice_design_tests")
    async def _run_invoice_design_tests(self):
        """Run comprehensive InvoiceDesignAgent tests"""
        print("\n🎨 Step 4: Running Invoice Design Agent Tests...")
        
        try:
            from tests.invoice_design_evals import InvoiceDesignEvalRunner
            
            # Run the comprehensive design evaluation
            eval_runner = InvoiceDesignEvalRunner()
            design_results = eval_runner.run_comprehensive_evaluation()
            
            self.results["tests_completed"]["invoice_design_tests"] = {
                "status": "passed" if design_results["evaluation_summary"]["success_rate"] >= 0.8 else "failed",
                "details": design_results,
                "timestamp": datetime.now().isoformat()
            }
            
            success_rate = design_results["evaluation_summary"]["success_rate"]
            passed_tests = design_results["evaluation_summary"]["passed_tests"]
            total_tests = design_results["evaluation_summary"]["total_tests"]
            
            print(f"   ✅ Design Generation: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
            
            # Also run unit tests for InvoiceDesignAgent
            import unittest
            from tests.test_invoice_design_agent import TestInvoiceDesignAgent, TestInvoiceDesignAgentIntegration
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAgent))
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAgentIntegration))
            
            # Run tests with custom result handler
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0)
            unit_result = runner.run(suite)
            
            unit_success = unit_result.wasSuccessful()
            print(f"   ✅ Unit Tests: {unit_result.testsRun - len(unit_result.failures) - len(unit_result.errors)}/{unit_result.testsRun} tests passed")
            
            if unit_result.failures:
                print(f"   ⚠️  Failures: {len(unit_result.failures)}")
            if unit_result.errors:
                print(f"   🚨 Errors: {len(unit_result.errors)}")
            
            # Overall status for design tests
            overall_design_success = success_rate >= 0.8 and unit_success
            self.results["tests_completed"]["invoice_design_tests"]["status"] = "passed" if overall_design_success else "failed"
            
        except ImportError as e:
            print(f"   ⚠️  Skipping design tests - import error: {str(e)}")
            self.results["tests_completed"]["invoice_design_tests"] = {
                "status": "skipped",
                "reason": f"Import error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Invoice design tests failed: {str(e)}")
            self.results["errors"].append(f"Invoice design tests: {str(e)}")
            self.results["tests_completed"]["invoice_design_tests"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @trace_workflow_step("api_integration_tests") 
    async def _run_api_integration_tests(self):
        """Run API integration tests"""
        print("\n🌐 Step 7: Running API Integration Tests...")
        
        try:
            import unittest
            from tests.test_api_integration import TestInvoiceDesignAPI, TestInvoiceDesignAPIIntegration
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAPI))
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAPIIntegration))
            
            # Run tests
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0)
            result = runner.run(suite)
            
            success = result.wasSuccessful()
            
            self.results["tests_completed"]["api_integration_tests"] = {
                "status": "passed" if success else "failed",
                "details": {
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ✅ API Tests: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} tests passed")
            
            if result.failures:
                print(f"   ⚠️  Failures: {len(result.failures)}")
            if result.errors:
                print(f"   🚨 Errors: {len(result.errors)}")
                
        except ImportError as e:
            print(f"   ⚠️  Skipping API tests - import error: {str(e)}")
            self.results["tests_completed"]["api_integration_tests"] = {
                "status": "skipped", 
                "reason": f"Import error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ API integration tests failed: {str(e)}")
            self.results["errors"].append(f"API integration tests: {str(e)}")
            self.results["tests_completed"]["api_integration_tests"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _test_orchestrator_workflow_integration(self):
        """Test orchestrator integration with workflow"""
        with patch('models.llm.base.get_model') as mock_get_model:
            mock_llm = MockLLMFactory.create_reliable_llm()
            mock_get_model.return_value = mock_llm
            
            state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
            
            # Test workflow execution
            result_state = await run_invoice_workflow(state)
            assert "orchestrator_decision" in result_state or "processing_status" in result_state
            assert result_state["current_agent"] == "orchestrator"
    
    async def _test_service_layer_integration(self):
        """Test service layer with mocked dependencies"""
        with patch('models.llm.base.get_model') as mock_get_model, \
             patch('services.contract_rag_service.get_contract_rag_service') as mock_rag:
            
            mock_llm = MockLLMFactory.create_reliable_llm()
            mock_get_model.return_value = mock_llm
            
            # Mock RAG service
            mock_rag_instance = type('MockRag', (), {
                '_retrieve_contract_context': lambda *args: "Mock contract content",
                'generate_invoice_data': lambda *args: type('MockResponse', (), {
                    'confidence_score': 0.85,
                    'model_dump': lambda: {"mock": "data"}
                })()
            })()
            mock_rag.return_value = mock_rag_instance
            
            service = OrchestratorService()
            request = WorkflowRequest(
                user_id="test_user",
                contract_file="test.pdf",
                contract_name="Test Contract"
            )
            
            # This should work with mocks
            mock_background_tasks = Mock()
            response = await service.start_invoice_workflow(request, mock_background_tasks)
            assert response.workflow_id is not None
    
    async def _test_api_integration(self):
        """Test API endpoints with mocked services"""
        # This would test FastAPI endpoints with mocked services
        # For now, just validate the structure exists
        from controller.orchestrator_controller import get_orchestrator_controller
        controller = get_orchestrator_controller()
        assert controller is not None
    
    @trace_workflow_step("performance_tests")
    async def _run_performance_tests(self):
        """Run performance tests"""
        print("\n⚡ Step 4: Running Performance Tests...")
        
        try:
            import unittest
            from io import StringIO
            
            # Create performance test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(TestOrchestratorPerformance)
            
            # Run performance tests
            stream = StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            
            with patch('models.llm.base.get_model') as mock_get_model:
                mock_llm = MockLLMFactory.create_reliable_llm()
                mock_get_model.return_value = mock_llm
                
                start_time = time.time()
                test_result = runner.run(suite)
                end_time = time.time()
            
            success = test_result.wasSuccessful()
            execution_time = end_time - start_time
            
            self.results["tests_completed"]["performance_tests"] = {
                "status": "passed" if success else "failed",
                "execution_time": execution_time,
                "details": stream.getvalue(),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ Performance Tests: {'PASSED' if success else 'FAILED'} ({execution_time:.2f}s)")
            
        except Exception as e:
            print(f"❌ Performance tests failed: {str(e)}")
            self.results["errors"].append(f"Performance tests: {str(e)}")
    
    @trace_workflow_step("e2e_workflow_test")
    async def _run_e2e_workflow_test(self):
        """Run end-to-end workflow test with full tracing"""
        print("\n🌐 Step 5: Running End-to-End Workflow Test...")
        
        try:
            with patch('models.llm.base.get_model') as mock_get_model, \
                 patch('services.contract_rag_service.get_contract_rag_service') as mock_rag, \
                 patch('db.db.get_pinecone_client') as mock_pinecone:
                
                # Setup all mocks
                mock_llm = MockLLMFactory.create_reliable_llm()
                mock_get_model.return_value = mock_llm
                
                mock_rag_instance = type('MockRag', (), {
                    '_retrieve_contract_context': lambda *args: "Sample rental agreement with monthly rent $1200",
                    'generate_invoice_data': lambda *args: type('MockResponse', (), {
                        'confidence_score': 0.85,
                        'model_dump': lambda: {"contract_type": "rental_lease", "amount": 1200}
                    })()
                })()
                mock_rag.return_value = mock_rag_instance
                
                mock_pinecone_instance = type('MockPinecone', (), {
                    'query': lambda *args, **kwargs: type('MockResult', (), {
                        'matches': [type('MockMatch', (), {
                            'metadata': {"text": "Sample contract text"}
                        })()]
                    })()
                })()
                mock_pinecone.return_value = mock_pinecone_instance
                
                # Run full workflow
                service = OrchestratorService()
                request = WorkflowRequest(
                    user_id="e2e_test_user",
                    contract_file="e2e_test_contract.pdf", 
                    contract_name="E2E Test Rental Agreement",
                    max_attempts=2
                )
                
                # Execute workflow
                start_time = time.time()
                mock_background_tasks = Mock()
                response = await service.start_invoice_workflow(request, mock_background_tasks)
                end_time = time.time()
                
                # Validate results
                success = response.status in ["success", "completed"]
                execution_time = end_time - start_time
                
                self.results["tests_completed"]["e2e_workflow"] = {
                    "status": "passed" if success else "failed",
                    "workflow_id": response.workflow_id,
                    "execution_time": execution_time,
                    "response_status": response.status,
                    "attempt_count": response.attempt_count,
                    "quality_score": response.quality_score,
                    "llm_calls": mock_llm.get_call_count(),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Log detailed workflow trace to LangSmith
                if self.langsmith_config.is_enabled():
                    self.langsmith_config.log_workflow_start(
                        response.workflow_id, request.user_id, request.contract_name
                    )
                
                print(f"✅ E2E Workflow: {'PASSED' if success else 'FAILED'} ({execution_time:.2f}s)")
                print(f"   - Workflow ID: {response.workflow_id}")
                print(f"   - Status: {response.status}")
                print(f"   - LLM Calls: {mock_llm.get_call_count()}")
                print(f"   - Quality Score: {response.quality_score:.2f}")
                
        except Exception as e:
            print(f"❌ E2E workflow test failed: {str(e)}")
            self.results["errors"].append(f"E2E workflow: {str(e)}")
    
    def _generate_summary_report(self):
        """Generate comprehensive test summary report"""
        print("\n" + "="*60)
        print("📊 TEST PIPELINE SUMMARY REPORT")
        print("="*60)
        
        total_tests = len(self.results["tests_completed"])
        passed_tests = sum(1 for test in self.results["tests_completed"].values() 
                          if test.get("status") == "passed")
        
        print(f"📋 Total Test Suites: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"🚨 Errors: {len(self.results['errors'])}")
        
        print(f"\n⏱️  Pipeline Duration: {self._calculate_duration()}")
        
        if self.langsmith_config.is_enabled():
            print("📊 LangSmith Tracing: ENABLED")
            print(f"   - Project: {self.langsmith_config.project_name}")
        else:
            print("📊 LangSmith Tracing: DISABLED")
        
        # Detailed results
        print("\n📝 Detailed Results:")
        for test_name, test_result in self.results["tests_completed"].items():
            status_icon = "✅" if test_result["status"] == "passed" else "❌"
            print(f"   {status_icon} {test_name}: {test_result['status'].upper()}")
        
        if self.results["errors"]:
            print("\n🚨 Errors:")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        # Success criteria
        overall_success = (passed_tests == total_tests and len(self.results["errors"]) == 0)
        print(f"\n🎯 Overall Pipeline: {'SUCCESS' if overall_success else 'FAILED'}")
        
        # Save results to file
        self._save_results_to_file()
    
    def _calculate_duration(self) -> str:
        """Calculate pipeline execution duration"""
        if "pipeline_end" in self.results:
            start = datetime.fromisoformat(self.results["pipeline_start"])
            end = datetime.fromisoformat(self.results["pipeline_end"])
            duration = (end - start).total_seconds()
            return f"{duration:.2f} seconds"
        return "Still running..."
    
    def _save_results_to_file(self):
        """Save test results to JSON file"""
        try:
            results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_path = os.path.join(os.path.dirname(__file__), results_file)
            
            with open(results_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"\n💾 Results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️  Failed to save results: {str(e)}")


async def main():
    """Main entry point for test pipeline"""
    print("🚀 Starting Orchestrator Agent Test Pipeline with LangSmith Integration")
    
    # Check if LangSmith environment variables are set
    langsmith_env_vars = ["LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY"]
    missing_vars = [var for var in langsmith_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing LangSmith environment variables: {missing_vars}")
        print("   Set these variables to enable LangSmith tracing:")
        print("   export LANGCHAIN_TRACING_V2=true")
        print("   export LANGCHAIN_API_KEY=your_api_key")
        print("   Continuing without LangSmith tracing...")
    
    # Run test pipeline
    pipeline = TestPipeline()
    results = await pipeline.run_complete_pipeline()
    
    # Return exit code based on results
    success = (results["overall_status"] == "completed" and 
              len(results["errors"]) == 0)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())