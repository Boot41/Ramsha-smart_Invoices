#!/usr/bin/env python3
"""
Coverage-enabled test runner for orchestrator agent testing

Provides test execution with code coverage reporting in the terminal.
"""

import os
import sys
import subprocess
import argparse

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def install_coverage():
    """Install coverage package if not available"""
    try:
        import coverage
        return True
    except ImportError:
        print("📦 Installing coverage package...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install coverage package")
            return False

def run_with_coverage(test_command, source_dirs=None):
    """Run tests with coverage reporting"""
    if not install_coverage():
        return 1
    
    import coverage
    
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
        from tests.orchestrator_evals import OrchestratorEvalRunner
        print("🎯 Running Orchestrator Evaluations with Coverage...")
        
        runner = OrchestratorEvalRunner()
        results = runner.run_comprehensive_evaluation()
        
        success = results.get('overall_success', False)
        print(f"📊 Evaluation Results: {'✅ PASSED' if success else '❌ FAILED'}")
        
        return 0 if success else 1
    
    return run_with_coverage(test_command)

def run_unit_tests_with_coverage():
    """Run unit tests with coverage"""
    def test_command():
        import unittest
        from tests.test_orchestrator_with_mocks import TestOrchestratorWithMocks
        
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
        import asyncio
        from tests.test_pipeline import TestPipeline
        
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
            # Import tests
            from agents.orchestrator_agent import OrchestratorAgent
            from workflows.invoice_workflow import InvoiceWorkflow, initialize_workflow_state
            from tests.mock_llm import MockLLMFactory
            
            # Basic functionality test
            orchestrator = OrchestratorAgent()
            workflow = InvoiceWorkflow()
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