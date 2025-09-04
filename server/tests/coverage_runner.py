#!/usr/bin/env python3
"""
Coverage-enabled test runner for orchestrator agent testing

Provides test execution with code coverage reporting in the terminal.
"""

import os
import sys
import subprocess
import argparse
import asyncio
import unittest

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all modules at top level
from tests.test_pipeline import TestPipeline
from tests.test_orchestrator_with_mocks import TestOrchestratorWithMocks
from agents.orchestrator_agent import OrchestratorAgent
from workflows.invoice_workflow import run_invoice_workflow, initialize_workflow_state
from tests.mock_llm import MockLLMFactory
from tests.orchestrator_evals import OrchestratorEvalRunner

# Try to import design evaluations (optional)
try:
    from tests.invoice_design_evals import InvoiceDesignEvalRunner
    DESIGN_EVALS_AVAILABLE = True
except ImportError:
    DESIGN_EVALS_AVAILABLE = False

# Try to import coverage
try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    coverage = None
    COVERAGE_AVAILABLE = False

def install_coverage():
    """Install coverage package if not available"""
    global coverage, COVERAGE_AVAILABLE
    if COVERAGE_AVAILABLE:
        return True
    
    print("📦 Installing coverage package...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])
        import coverage
        COVERAGE_AVAILABLE = True
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install coverage package")
        return False

def run_with_coverage(test_command, source_dirs=None):
    """Run tests with coverage reporting"""
    if not install_coverage():
        return 1
    
    # Default source directories
    if source_dirs is None:
        source_dirs = ['agents', 'workflows', 'services', 'schemas', 'utils']
    
    # Initialize coverage
    cov = coverage.Coverage(
        source=source_dirs,
        omit=[
            'tests/*',
            '*/__pycache__/*',
            '*/venv/*',
            '*/.venv/*',
            '*/node_modules/*'
        ]
    )
    
    print("📊 Starting coverage measurement...")
    cov.start()
    
    try:
        # Run the test command
        exit_code = test_command()
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        exit_code = 1
    finally:
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\n" + "="*60)
        print("📊 CODE COVERAGE REPORT")
        print("="*60)
        
        # Terminal report
        cov.report(show_missing=True, skip_covered=False)
        
        # Generate HTML report
        html_dir = os.path.join(os.path.dirname(__file__), 'htmlcov')
        try:
            cov.html_report(directory=html_dir)
            print(f"\n📄 HTML coverage report: {html_dir}/index.html")
        except Exception as e:
            print(f"⚠️  Could not generate HTML report: {str(e)}")
        
        # Coverage summary
        total_coverage = cov.report(show_missing=False, file=None)
        print(f"\n🎯 Total Coverage: {total_coverage:.1f}%")
        
        if total_coverage < 50:
            print("🚨 Coverage is below 50% - consider adding more tests")
        elif total_coverage < 70:
            print("⚠️  Coverage is below 70% - good, but room for improvement")  
        elif total_coverage < 90:
            print("✅ Good coverage above 70%")
        else:
            print("🌟 Excellent coverage above 90%!")
    
    return exit_code

def run_evaluations_with_coverage():
    """Run evaluations with coverage"""
    def test_command():
        # Run orchestrator evaluations
        print("🎯 Running Orchestrator Evaluations with Coverage...")
        
        orchestrator_runner = OrchestratorEvalRunner()
        orchestrator_results = orchestrator_runner.run_comprehensive_evaluation()
        
        orchestrator_success = orchestrator_results.get('overall_success', False)
        print(f"📊 Orchestrator Results: {'✅ PASSED' if orchestrator_success else '❌ FAILED'}")
        
        # Run invoice design evaluations
        design_success = True
        if DESIGN_EVALS_AVAILABLE:
            try:
                print("🎨 Running Invoice Design Evaluations with Coverage...")
                
                design_runner = InvoiceDesignEvalRunner()
                design_results = design_runner.run_comprehensive_evaluation()
                
                design_success = design_results['evaluation_summary']['success_rate'] >= 0.8
                print(f"📊 Design Agent Results: {'✅ PASSED' if design_success else '❌ FAILED'}")
                
            except Exception as e:
                print(f"❌ Invoice design evaluations failed: {str(e)}")
                design_success = False
        else:
            print("⚠️  Invoice design evaluations skipped: Module not available")
        
        overall_success = orchestrator_success and design_success
        return 0 if overall_success else 1
    
    return run_with_coverage(test_command)

def run_unit_tests_with_coverage():
    """Run unit tests with coverage"""
    def test_command():
        print("🧪 Running Unit Tests with Coverage...")
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestOrchestratorWithMocks)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        success = result.wasSuccessful()
        print(f"📊 Unit Test Results: {'✅ PASSED' if success else '❌ FAILED'}")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        return 0 if success else 1
    
    return run_with_coverage(test_command)

def run_pipeline_with_coverage():
    """Run full pipeline with coverage"""
    def test_command():
        print("🚀 Running Full Pipeline with Coverage...")
        
        async def run_pipeline():
            pipeline = TestPipeline()
            results = await pipeline.run_complete_pipeline()
            
            success = (results["overall_status"] == "completed" and 
                      len(results["errors"]) == 0)
            
            print(f"📊 Pipeline Results: {'✅ PASSED' if success else '❌ FAILED'}")
            return 0 if success else 1
        
        return asyncio.run(run_pipeline())
    
    return run_with_coverage(test_command, source_dirs=['agents', 'workflows', 'services', 'schemas', 'utils', 'controller'])

def run_quick_tests_with_coverage():
    """Run quick tests with coverage"""
    def test_command():
        print("⚡ Running Quick Tests with Coverage...")
        
        try:
            # Basic functionality test
            orchestrator = OrchestratorAgent()
            # Test workflow function exists
            assert callable(run_invoice_workflow)
            mock_llm = MockLLMFactory.create_reliable_llm()
            
            # Test orchestrator
            state = initialize_workflow_state("test", "test.pdf", "Test Contract")
            result_state = orchestrator.process(state)
            
            assert "orchestrator_decision" in result_state
            assert result_state["current_agent"] == "orchestrator"
            
            # Test mock LLM
            response = mock_llm.invoke("test input")
            assert response.content is not None
            
            print("✅ All quick tests passed")
            return 0
            
        except Exception as e:
            print(f"❌ Quick tests failed: {str(e)}")
            return 1
    
    return run_with_coverage(test_command)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run tests with code coverage reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/coverage_runner.py eval        # Run evaluations with coverage
  python tests/coverage_runner.py unit        # Run unit tests with coverage  
  python tests/coverage_runner.py pipeline    # Run full pipeline with coverage
  python tests/coverage_runner.py quick       # Run quick tests with coverage
        """
    )
    
    parser.add_argument(
        'test_type',
        choices=['eval', 'unit', 'pipeline', 'quick'],
        help='Type of test to run with coverage'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Starting {args.test_type} tests with coverage...")
    
    # Run selected test type with coverage
    if args.test_type == 'eval':
        exit_code = run_evaluations_with_coverage()
    elif args.test_type == 'unit':
        exit_code = run_unit_tests_with_coverage()
    elif args.test_type == 'pipeline':
        exit_code = run_pipeline_with_coverage()
    elif args.test_type == 'quick':
        exit_code = run_quick_tests_with_coverage()
    else:
        print(f"❌ Unknown test type: {args.test_type}")
        exit_code = 1
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())