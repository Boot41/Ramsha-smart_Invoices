#!/usr/bin/env python3
"""
Quick test runner script for orchestrator agent testing with coverage

This script provides easy commands to run different test suites:
- run_tests.py eval        # Run orchestrator evaluations only
- run_tests.py unit        # Run unit tests only  
- run_tests.py pipeline    # Run full test pipeline with LangSmith
- run_tests.py quick       # Run quick smoke tests

Usage examples:
    python tests/run_tests.py eval --coverage
    python tests/run_tests.py pipeline --coverage
    python tests/run_tests.py --help
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\'"')  # Remove quotes
                        os.environ[key] = value
            print(f"✅ Loaded environment variables from .env file")
        except Exception as e:
            print(f"⚠️  Warning: Could not load .env file: {str(e)}")

# Load .env file at startup
load_env_file()

def run_evaluations():
    """Run orchestrator evaluations only"""
    print("🎯 Running Orchestrator Evaluations...")
    
    from tests.orchestrator_evals import OrchestratorEvalRunner
    
    runner = OrchestratorEvalRunner()
    results = runner.run_comprehensive_evaluation()
    
    print(f"\n📊 Results Summary:")
    print(f"   Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
    
    return 0 if results['overall_success'] else 1

def run_unit_tests():
    """Run unit tests only"""
    print("🧪 Running Unit Tests...")
    
    import unittest
    from tests.test_orchestrator_with_mocks import TestOrchestratorWithMocks
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestOrchestratorWithMocks)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    success = result.wasSuccessful()
    print(f"\n📊 Unit Tests: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return 0 if success else 1

async def run_full_pipeline():
    """Run complete test pipeline"""
    print("🚀 Running Full Test Pipeline...")
    
    from tests.test_pipeline import TestPipeline
    
    pipeline = TestPipeline()
    results = await pipeline.run_complete_pipeline()
    
    success = (results["overall_status"] == "completed" and 
              len(results["errors"]) == 0)
    
    return 0 if success else 1

def run_quick_tests():
    """Run quick smoke tests"""
    print("⚡ Running Quick Smoke Tests...")
    
    try:
        # Test 1: Import all modules
        print("📦 Testing imports...")
        from agents.orchestrator_agent import OrchestratorAgent
        from workflows.invoice_workflow import InvoiceWorkflow
        from services.orchestrator_service import OrchestratorService
        from tests.mock_llm import MockLLMFactory
        print("✅ All imports successful")
        
        # Test 2: Create instances
        print("🏗️  Testing instance creation...")
        orchestrator = OrchestratorAgent()
        workflow = InvoiceWorkflow()
        mock_llm = MockLLMFactory.create_reliable_llm()
        print("✅ All instances created successfully")
        
        # Test 3: Basic functionality
        print("⚙️  Testing basic functionality...")
        from workflows.invoice_workflow import initialize_workflow_state
        state = initialize_workflow_state("test", "test.pdf", "Test Contract")
        
        # Test orchestrator decision
        result_state = orchestrator.process(state)
        assert "orchestrator_decision" in result_state
        print("✅ Orchestrator decision making works")
        
        # Test mock LLM
        response = mock_llm.invoke("test input")
        assert response.content is not None
        print("✅ Mock LLM works")
        
        print("\n🎉 All quick tests PASSED!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Quick tests FAILED: {str(e)}")
        return 1

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test runner for orchestrator agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py eval        # Run evaluations
  python tests/run_tests.py unit        # Run unit tests
  python tests/run_tests.py pipeline    # Run full pipeline
  python tests/run_tests.py quick       # Run quick tests
        """
    )
    
    parser.add_argument(
        'test_type',
        choices=['eval', 'unit', 'pipeline', 'quick'],
        help='Type of test to run'
    )
    
    parser.add_argument(
        '--langsmith',
        action='store_true',
        help='Enable LangSmith tracing (requires API key)'
    )
    
    args = parser.parse_args()
    
    # Set LangSmith environment if requested
    if args.langsmith:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if not os.getenv("LANGCHAIN_API_KEY"):
            print("⚠️  Warning: LANGCHAIN_API_KEY not set. LangSmith tracing may not work.")
    
    print(f"🚀 Starting {args.test_type} tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run selected test type
    if args.test_type == 'eval':
        exit_code = run_evaluations()
    elif args.test_type == 'unit':
        exit_code = run_unit_tests()
    elif args.test_type == 'pipeline':
        exit_code = asyncio.run(run_full_pipeline())
    elif args.test_type == 'quick':
        exit_code = run_quick_tests()
    else:
        print(f"❌ Unknown test type: {args.test_type}")
        exit_code = 1
    
    print(f"\n🏁 Tests completed with exit code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())