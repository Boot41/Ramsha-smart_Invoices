#!/usr/bin/env python3
"""
Agent Evaluation Test Runner

Quick runner script for all agent evaluations.
Usage:
  python run_agent_evaluations.py --validation-only
  python run_agent_evaluations.py --orchestration-only
  python run_agent_evaluations.py --comprehensive (default)
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the server directory to the path
sys.path.insert(0, str(Path(__file__).parent))

async def run_validation_only():
    """Run only validation agent evaluations"""
    from tests.validation_agent_evals import main as validation_main
    print("🔬 Running Validation Agent Evaluations Only")
    return await validation_main()

async def run_orchestration_only():
    """Run only orchestration pipeline evaluations"""
    from tests.orchestrator_evals_updated import main as orchestration_main
    print("🎯 Running Orchestration Pipeline Evaluations Only")
    return await orchestration_main()

async def run_comprehensive():
    """Run comprehensive evaluation suite"""
    from tests.comprehensive_agent_evaluation import main as comprehensive_main
    print("🚀 Running Comprehensive Agent Evaluation Suite")
    return await comprehensive_main()

async def main():
    parser = argparse.ArgumentParser(description="Run agent evaluations")
    parser.add_argument(
        "--validation-only", 
        action="store_true", 
        help="Run only validation agent evaluations"
    )
    parser.add_argument(
        "--orchestration-only", 
        action="store_true", 
        help="Run only orchestration pipeline evaluations"
    )
    parser.add_argument(
        "--comprehensive", 
        action="store_true", 
        default=True,
        help="Run comprehensive evaluation suite (default)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.validation_only:
            await run_validation_only()
        elif args.orchestration_only:
            await run_orchestration_only()
        else:
            # Run comprehensive by default
            exit_code = await run_comprehensive()
            sys.exit(exit_code if exit_code is not None else 0)
            
    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Evaluation failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())