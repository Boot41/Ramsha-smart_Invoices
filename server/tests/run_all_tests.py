#!/usr/bin/env python3
"""
Master test runner for the complete smart-invoice-scheduler agentic pipeline

This comprehensive test runner executes all test suites:
- InvoiceDesignAgent unit tests and evaluations
- OrchestratorAgent evaluations and unit tests
- End-to-end pipeline integration tests
- API integration tests
- Performance tests

Usage:
    python tests/run_all_tests.py                    # Run all tests
    python tests/run_all_tests.py --coverage         # Run with coverage
    python tests/run_all_tests.py --verbose          # Verbose output
    python tests/run_all_tests.py --fast             # Skip long-running tests
    python tests/run_all_tests.py --agents-only      # Test agents only
"""

import os
import sys
import argparse
import asyncio
import time
import unittest
import subprocess
from datetime import datetime
from typing import Dict, Any, List

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all test modules at top level
from tests.test_invoice_design_agent import TestInvoiceDesignAgent, TestInvoiceDesignAgentIntegration
from tests.invoice_design_evals import InvoiceDesignEvalRunner
from tests.orchestrator_evals import OrchestratorEvalRunner
from tests.test_orchestrator_with_mocks import TestOrchestratorWithMocks, TestOrchestratorPerformance
from tests.test_api_integration import TestInvoiceDesignAPI, TestInvoiceDesignAPIIntegration
from tests.test_pipeline import TestPipeline

# Try to import coverage
try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    coverage = None
    COVERAGE_AVAILABLE = False

class MasterTestRunner:
    """Comprehensive test runner for all agentic components"""
    
    def __init__(self, args):
        self.args = args
        self.results = {
            "start_time": datetime.now().isoformat(),
            "test_suites": {},
            "summary": {
                "total_suites": 0,
                "passed_suites": 0,
                "failed_suites": 0,
                "skipped_suites": 0,
                "errors": []
            }
        }
        
        # Configure test suites based on arguments
        self.test_suites = self._configure_test_suites()
    
    def _configure_test_suites(self) -> List[Dict[str, Any]]:
        """Configure test suites based on command line arguments"""
        suites = []
        
        if not self.args.agents_only:
            # Full test suite including infrastructure tests
            suites = [
                {
                    "name": "invoice_design_unit_tests",
                    "description": "InvoiceDesignAgent Unit Tests",
                    "runner": self._run_invoice_design_unit_tests,
                    "required": True
                },
                {
                    "name": "invoice_design_evaluations", 
                    "description": "InvoiceDesignAgent Evaluations",
                    "runner": self._run_invoice_design_evaluations,
                    "required": True
                },
                {
                    "name": "orchestrator_evaluations",
                    "description": "OrchestratorAgent Evaluations", 
                    "runner": self._run_orchestrator_evaluations,
                    "required": True
                },
                {
                    "name": "orchestrator_unit_tests",
                    "description": "OrchestratorAgent Unit Tests",
                    "runner": self._run_orchestrator_unit_tests,
                    "required": True
                },
                {
                    "name": "api_integration_tests",
                    "description": "API Integration Tests",
                    "runner": self._run_api_integration_tests,
                    "required": False
                }
            ]
            
            if not self.args.fast:
                # Add long-running tests
                suites.extend([
                    {
                        "name": "performance_tests",
                        "description": "Performance & Load Tests",
                        "runner": self._run_performance_tests,
                        "required": False
                    },
                    {
                        "name": "end_to_end_pipeline",
                        "description": "End-to-End Pipeline Tests",
                        "runner": self._run_e2e_pipeline_tests,
                        "required": False
                    }
                ])
        else:
            # Agents-only test suite
            suites = [
                {
                    "name": "invoice_design_agents",
                    "description": "Complete InvoiceDesignAgent Tests",
                    "runner": self._run_complete_invoice_design_tests,
                    "required": True
                },
                {
                    "name": "orchestrator_agents",
                    "description": "Complete OrchestratorAgent Tests",
                    "runner": self._run_complete_orchestrator_tests,
                    "required": True
                }
            ]
        
        return suites
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all configured test suites"""
        print("🚀 Starting Master Test Runner for Smart Invoice Scheduler")
        print("=" * 80)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Test Configuration:")
        print(f"   - Coverage: {'✅ Enabled' if self.args.coverage else '❌ Disabled'}")
        print(f"   - Verbose: {'✅ Enabled' if self.args.verbose else '❌ Disabled'}")
        print(f"   - Fast Mode: {'✅ Enabled' if self.args.fast else '❌ Disabled'}")
        print(f"   - Agents Only: {'✅ Enabled' if self.args.agents_only else '❌ Disabled'}")
        print(f"📋 Test Suites: {len(self.test_suites)}")
        print("=" * 80)
        
        self.results["summary"]["total_suites"] = len(self.test_suites)
        
        # Run each test suite
        for i, suite in enumerate(self.test_suites, 1):
            suite_name = suite["name"]
            description = suite["description"]
            runner_func = suite["runner"]
            required = suite["required"]
            
            print(f"\n🧪 [{i}/{len(self.test_suites)}] Running {description}")
            print("-" * 60)
            
            try:
                start_time = time.time()
                
                # Run the test suite
                suite_result = await runner_func()
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Store results
                suite_result["execution_time"] = execution_time
                suite_result["required"] = required
                self.results["test_suites"][suite_name] = suite_result
                
                # Update summary
                if suite_result["status"] == "passed":
                    self.results["summary"]["passed_suites"] += 1
                    status_icon = "✅"
                elif suite_result["status"] == "failed":
                    self.results["summary"]["failed_suites"] += 1
                    status_icon = "❌"
                    if required:
                        self.results["summary"]["errors"].append(f"Required suite '{description}' failed")
                else:  # skipped
                    self.results["summary"]["skipped_suites"] += 1
                    status_icon = "⏭️"
                
                print(f"{status_icon} {description}: {suite_result['status'].upper()} ({execution_time:.2f}s)")
                
                if self.args.verbose and "details" in suite_result:
                    print(f"   Details: {suite_result['details']}")
                
            except Exception as e:
                print(f"❌ {description}: CRASHED")
                print(f"   Error: {str(e)}")
                
                self.results["test_suites"][suite_name] = {
                    "status": "crashed",
                    "error": str(e),
                    "execution_time": 0,
                    "required": required
                }
                
                self.results["summary"]["failed_suites"] += 1
                if required:
                    self.results["summary"]["errors"].append(f"Required suite '{description}' crashed: {str(e)}")
        
        # Generate final report
        self.results["end_time"] = datetime.now().isoformat()
        self._generate_final_report()
        
        return self.results
    
    async def _run_invoice_design_unit_tests(self) -> Dict[str, Any]:
        """Run InvoiceDesignAgent unit tests"""
        try:
            
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAgent))
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAgentIntegration))
            
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0)
            result = runner.run(suite)
            
            success = result.wasSuccessful()
            
            return {
                "status": "passed" if success else "failed",
                "details": {
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors)
                }
            }
            
        except ImportError as e:
            return {"status": "skipped", "reason": f"Import error: {str(e)}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _run_invoice_design_evaluations(self) -> Dict[str, Any]:
        """Run InvoiceDesignAgent comprehensive evaluations"""
        try:
            
            runner = InvoiceDesignEvalRunner()
            results = runner.run_comprehensive_evaluation()
            
            success_rate = results["evaluation_summary"]["success_rate"]
            
            return {
                "status": "passed" if success_rate >= 0.8 else "failed",
                "details": {
                    "success_rate": success_rate,
                    "passed_tests": results["evaluation_summary"]["passed_tests"],
                    "total_tests": results["evaluation_summary"]["total_tests"]
                }
            }
            
        except ImportError as e:
            return {"status": "skipped", "reason": f"Import error: {str(e)}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _run_orchestrator_evaluations(self) -> Dict[str, Any]:
        """Run OrchestratorAgent evaluations"""
        try:
            
            runner = OrchestratorEvalRunner()
            results = runner.run_comprehensive_evaluation()
            
            success = results.get("overall_success", False)
            
            return {
                "status": "passed" if success else "failed",
                "details": {
                    "overall_success": success,
                    "orchestrator_tests": results.get("orchestrator_evaluation", {}).get("passed", 0),
                    "routing_tests": results.get("routing_function_tests", {}).get("passed", 0)
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _run_orchestrator_unit_tests(self) -> Dict[str, Any]:
        """Run OrchestratorAgent unit tests"""
        try:
            
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(TestOrchestratorWithMocks)
            
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0)
            result = runner.run(suite)
            
            success = result.wasSuccessful()
            
            return {
                "status": "passed" if success else "failed",
                "details": {
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors)
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _run_api_integration_tests(self) -> Dict[str, Any]:
        """Run API integration tests"""
        try:
            
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAPI))
            suite.addTest(loader.loadTestsFromTestCase(TestInvoiceDesignAPIIntegration))
            
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0)
            result = runner.run(suite)
            
            success = result.wasSuccessful()
            
            return {
                "status": "passed" if success else "failed",
                "details": {
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors)
                }
            }
            
        except ImportError as e:
            return {"status": "skipped", "reason": f"FastAPI not available: {str(e)}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        try:
            
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(TestOrchestratorPerformance)
            
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0)
            result = runner.run(suite)
            
            success = result.wasSuccessful()
            
            return {
                "status": "passed" if success else "failed",
                "details": {
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors)
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _run_e2e_pipeline_tests(self) -> Dict[str, Any]:
        """Run end-to-end pipeline tests"""
        try:
            
            pipeline = TestPipeline()
            results = await pipeline.run_complete_pipeline()
            
            success = (results["overall_status"] == "completed" and 
                      len(results["errors"]) == 0)
            
            return {
                "status": "passed" if success else "failed",
                "details": {
                    "overall_status": results["overall_status"],
                    "completed_tests": len(results["tests_completed"]),
                    "errors": len(results["errors"])
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _run_complete_invoice_design_tests(self) -> Dict[str, Any]:
        """Run complete InvoiceDesignAgent test suite"""
        unit_result = await self._run_invoice_design_unit_tests()
        eval_result = await self._run_invoice_design_evaluations()
        
        # Combine results
        unit_success = unit_result["status"] == "passed"
        eval_success = eval_result["status"] == "passed"
        overall_success = unit_success and eval_success
        
        return {
            "status": "passed" if overall_success else "failed",
            "details": {
                "unit_tests": unit_result,
                "evaluations": eval_result
            }
        }
    
    async def _run_complete_orchestrator_tests(self) -> Dict[str, Any]:
        """Run complete OrchestratorAgent test suite"""
        unit_result = await self._run_orchestrator_unit_tests()
        eval_result = await self._run_orchestrator_evaluations()
        
        # Combine results
        unit_success = unit_result["status"] == "passed"
        eval_success = eval_result["status"] == "passed"
        overall_success = unit_success and eval_success
        
        return {
            "status": "passed" if overall_success else "failed",
            "details": {
                "unit_tests": unit_result,
                "evaluations": eval_result
            }
        }
    
    def _generate_final_report(self):
        """Generate comprehensive final report"""
        summary = self.results["summary"]
        
        print("\n" + "=" * 80)
        print("🏆 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Calculate durations
        start_time = datetime.fromisoformat(self.results["start_time"])
        end_time = datetime.fromisoformat(self.results["end_time"])
        total_duration = (end_time - start_time).total_seconds()
        
        print(f"⏱️  Total Execution Time: {total_duration:.2f} seconds")
        print(f"📊 Test Suite Results:")
        print(f"   Total Suites: {summary['total_suites']}")
        print(f"   ✅ Passed: {summary['passed_suites']}")
        print(f"   ❌ Failed: {summary['failed_suites']}")
        print(f"   ⏭️  Skipped: {summary['skipped_suites']}")
        
        # Success rate
        if summary['total_suites'] > 0:
            success_rate = summary['passed_suites'] / summary['total_suites']
            print(f"   📈 Success Rate: {success_rate:.1%}")
        
        # Detailed results
        print(f"\n📋 Detailed Test Suite Results:")
        for suite_name, result in self.results["test_suites"].items():
            status_icon = {
                "passed": "✅",
                "failed": "❌", 
                "skipped": "⏭️",
                "crashed": "💥"
            }.get(result["status"], "❓")
            
            execution_time = result.get("execution_time", 0)
            print(f"   {status_icon} {suite_name}: {result['status'].upper()} ({execution_time:.2f}s)")
            
            if result["status"] in ["failed", "crashed"] and "error" in result:
                print(f"      Error: {result['error']}")
        
        # Critical errors
        if summary["errors"]:
            print(f"\n🚨 Critical Issues:")
            for error in summary["errors"]:
                print(f"   - {error}")
        
        # Overall assessment
        required_suites = [name for name, result in self.results["test_suites"].items() 
                          if result.get("required", False)]
        required_passed = [name for name in required_suites 
                          if self.results["test_suites"][name]["status"] == "passed"]
        
        all_required_passed = len(required_passed) == len(required_suites)
        overall_success = all_required_passed and len(summary["errors"]) == 0
        
        print(f"\n🎯 Overall Assessment: {'🎉 SUCCESS' if overall_success else '⚠️  ATTENTION REQUIRED'}")
        
        if not overall_success:
            print("   Issues detected that require attention:")
            if not all_required_passed:
                failed_required = [name for name in required_suites if name not in required_passed]
                print(f"   - Required test suites failed: {', '.join(failed_required)}")
            if summary["errors"]:
                print(f"   - Critical errors: {len(summary['errors'])}")
        
        print("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Master test runner for smart-invoice-scheduler agentic pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_all_tests.py                    # Run all tests
  python tests/run_all_tests.py --coverage         # Run with coverage
  python tests/run_all_tests.py --verbose          # Verbose output
  python tests/run_all_tests.py --fast             # Skip long-running tests
  python tests/run_all_tests.py --agents-only      # Test agents only
        """
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with code coverage analysis'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Skip long-running tests (performance, E2E)'
    )
    
    parser.add_argument(
        '--agents-only',
        action='store_true',
        help='Run only agent tests (skip infrastructure tests)'
    )
    
    args = parser.parse_args()
    
    async def run_tests():
        runner = MasterTestRunner(args)
        
        if args.coverage:
            # Run with coverage
            if not COVERAGE_AVAILABLE:
                print("⚠️  Coverage not available. Installing...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])
                print("✅ Please run again with coverage installed.")
                return 1
            
            try:
                
                cov = coverage.Coverage(
                    source=['agents', 'services', 'workflows', 'schemas'],
                    omit=['tests/*', '*/__pycache__/*']
                )
                
                cov.start()
                results = await runner.run_all_tests()
                cov.stop()
                cov.save()
                
                print("\n📊 Coverage Report:")
                cov.report(show_missing=True)
                
                # HTML report
                html_dir = os.path.join(os.path.dirname(__file__), 'htmlcov')
                cov.html_report(directory=html_dir)
                print(f"📄 HTML Coverage Report: {html_dir}/index.html")
                
            except Exception as e:
                print(f"❌ Coverage error: {str(e)}")
                return 1
        else:
            results = await runner.run_all_tests()
        
        # Determine exit code
        summary = results["summary"]
        required_failed = [name for name, result in results["test_suites"].items() 
                          if result.get("required", False) and result["status"] != "passed"]
        
        if required_failed or summary["errors"]:
            return 1
        else:
            return 0
    
    # Run the tests
    exit_code = asyncio.run(run_tests())
    
    print(f"\n🏁 Master test runner completed with exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())