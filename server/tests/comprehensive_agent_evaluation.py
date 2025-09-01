#!/usr/bin/env python3
"""
Comprehensive Agent Evaluation Suite

Runs both validation agent evaluations and orchestration pipeline tests.
Provides unified reporting and metrics across all agent evaluations.
"""

import asyncio
import json
import sys
from typing import Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path

# Import evaluation modules
from tests.validation_agent_evals import ValidationAgentEvaluator
from tests.orchestrator_evals_updated import EnhancedOrchestratorEvaluator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveAgentEvaluationSuite:
    """
    Comprehensive evaluation suite for all agents in the invoice processing pipeline.
    
    Runs validation agent tests and orchestration pipeline tests, providing
    unified metrics and recommendations.
    """
    
    def __init__(self):
        self.validation_evaluator = ValidationAgentEvaluator()
        self.orchestration_evaluator = EnhancedOrchestratorEvaluator()
        self.results = {}
        
    async def run_all_evaluations(self) -> Dict[str, Any]:
        """Run all agent evaluations and generate comprehensive report"""
        
        print("🚀 Comprehensive Agent Evaluation Suite")
        print("=" * 80)
        print("🔬 Testing validation agent and orchestration pipeline")
        print("=" * 80)
        
        # Run validation agent evaluations
        print("\n📋 Running Validation Agent Evaluations...")
        validation_results = await self.validation_evaluator.run_all_validation_evaluations()
        
        # Run orchestration pipeline evaluations
        print("\n🎯 Running Orchestration Pipeline Evaluations...")
        orchestration_results = await self.orchestration_evaluator.run_all_orchestration_evaluations()
        
        # Generate comprehensive report
        comprehensive_report = self._generate_comprehensive_report(
            validation_results, orchestration_results
        )
        
        return comprehensive_report
    
    def _generate_comprehensive_report(self, 
                                     validation_report: Dict[str, Any], 
                                     orchestration_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate unified comprehensive report"""
        
        # Extract key metrics
        validation_summary = validation_report["summary"]
        orchestration_summary = orchestration_report["summary"]
        
        # Calculate overall system metrics
        overall_pass_rate = (
            (validation_summary["passed"] + orchestration_summary["passed"]) /
            (validation_summary["total_tests"] + orchestration_summary["total_tests"])
        ) * 100 if (validation_summary["total_tests"] + orchestration_summary["total_tests"]) > 0 else 0
        
        overall_avg_score = (
            validation_summary["average_score"] + orchestration_summary["average_score"]
        ) / 2
        
        comprehensive_report = {
            "evaluation_metadata": {
                "evaluation_timestamp": datetime.now().isoformat(),
                "evaluation_type": "comprehensive_agent_evaluation",
                "components_tested": ["validation_agent", "orchestration_pipeline"],
                "total_test_suites": 2
            },
            
            "overall_summary": {
                "total_tests": validation_summary["total_tests"] + orchestration_summary["total_tests"],
                "total_passed": validation_summary["passed"] + orchestration_summary["passed"],
                "total_failed": validation_summary["failed"] + orchestration_summary["failed"],
                "overall_pass_rate": overall_pass_rate,
                "overall_average_score": overall_avg_score,
                "total_execution_time": validation_summary.get("average_execution_time", 0) + orchestration_summary.get("average_execution_time", 0),
                "system_readiness_score": self._calculate_system_readiness_score(validation_summary, orchestration_summary)
            },
            
            "component_summaries": {
                "validation_agent": {
                    "status": "PASSED" if validation_summary["pass_rate"] >= 70 else "FAILED",
                    "pass_rate": validation_summary["pass_rate"],
                    "average_score": validation_summary["average_score"],
                    "validation_accuracy": validation_summary["average_validation_accuracy"],
                    "human_input_detection_accuracy": validation_summary["human_input_detection_accuracy"],
                    "key_capabilities": [
                        "Required field validation",
                        "Format validation", 
                        "Business logic validation",
                        "Human-in-the-loop detection",
                        "Data quality scoring"
                    ]
                },
                
                "orchestration_pipeline": {
                    "status": "PASSED" if orchestration_summary["pass_rate"] >= 70 else "FAILED",
                    "pass_rate": orchestration_summary["pass_rate"],
                    "average_score": orchestration_summary["average_score"],
                    "workflow_completion_rate": orchestration_summary["workflow_completion_rate"],
                    "validation_integration_rate": orchestration_summary["validation_success_rate"],
                    "human_input_handling_rate": orchestration_summary["human_input_handling_rate"],
                    "key_capabilities": [
                        "Workflow routing",
                        "Agent coordination",
                        "Validation integration",
                        "Error handling",
                        "Human input workflow management"
                    ]
                }
            },
            
            "detailed_reports": {
                "validation_agent": validation_report,
                "orchestration_pipeline": orchestration_report
            },
            
            "integration_analysis": self._analyze_agent_integration(validation_report, orchestration_report),
            
            "system_capabilities_matrix": self._create_capabilities_matrix(validation_report, orchestration_report),
            
            "comprehensive_recommendations": self._generate_comprehensive_recommendations(
                validation_report, orchestration_report
            ),
            
            "quality_gates": self._evaluate_quality_gates(validation_summary, orchestration_summary)
        }
        
        return comprehensive_report
    
    def _calculate_system_readiness_score(self, validation_summary: Dict, orchestration_summary: Dict) -> Dict[str, Any]:
        """Calculate overall system readiness score"""
        
        # Weight different components
        weights = {
            "validation_accuracy": 0.3,
            "orchestration_reliability": 0.3,
            "human_input_handling": 0.2,
            "error_handling": 0.2
        }
        
        # Calculate component scores
        validation_score = validation_summary["average_validation_accuracy"]
        orchestration_score = orchestration_summary["average_score"]
        human_input_score = validation_summary["human_input_detection_accuracy"] / 100
        workflow_completion_score = orchestration_summary["workflow_completion_rate"] / 100
        
        # Calculate weighted score
        readiness_score = (
            validation_score * weights["validation_accuracy"] +
            orchestration_score * weights["orchestration_reliability"] +
            human_input_score * weights["human_input_handling"] +
            workflow_completion_score * weights["error_handling"]
        )
        
        # Determine readiness level
        if readiness_score >= 0.9:
            readiness_level = "PRODUCTION_READY"
        elif readiness_score >= 0.8:
            readiness_level = "NEAR_PRODUCTION_READY"
        elif readiness_score >= 0.7:
            readiness_level = "DEVELOPMENT_READY"
        else:
            readiness_level = "REQUIRES_IMPROVEMENT"
        
        return {
            "score": readiness_score,
            "level": readiness_level,
            "component_scores": {
                "validation_accuracy": validation_score,
                "orchestration_reliability": orchestration_score,
                "human_input_handling": human_input_score,
                "error_handling": workflow_completion_score
            }
        }
    
    def _analyze_agent_integration(self, validation_report: Dict, orchestration_report: Dict) -> Dict[str, Any]:
        """Analyze how well agents integrate with each other"""
        
        # Look for validation-related tests in orchestration
        orchestration_results = orchestration_report["detailed_results"]
        validation_integration_tests = [
            r for r in orchestration_results 
            if "validation" in r["test_name"]
        ]
        
        validation_integration_success = sum(1 for r in validation_integration_tests if r["passed"])
        integration_success_rate = (
            validation_integration_success / len(validation_integration_tests) 
            if validation_integration_tests else 0
        ) * 100
        
        return {
            "validation_orchestration_integration": {
                "success_rate": integration_success_rate,
                "tests_run": len(validation_integration_tests),
                "tests_passed": validation_integration_success,
                "status": "GOOD" if integration_success_rate >= 80 else "NEEDS_IMPROVEMENT"
            },
            
            "human_input_workflow_integration": {
                "validation_detection_accuracy": validation_report["summary"]["human_input_detection_accuracy"],
                "orchestration_handling_rate": orchestration_report["summary"]["human_input_handling_rate"],
                "integration_effectiveness": min(
                    validation_report["summary"]["human_input_detection_accuracy"],
                    orchestration_report["summary"]["human_input_handling_rate"]
                ),
                "status": "GOOD" if min(
                    validation_report["summary"]["human_input_detection_accuracy"],
                    orchestration_report["summary"]["human_input_handling_rate"]
                ) >= 70 else "NEEDS_IMPROVEMENT"
            },
            
            "error_handling_coordination": {
                "validation_error_detection": len([
                    r for r in validation_report["detailed_results"] 
                    if not r["passed"] and r.get("error")
                ]),
                "orchestration_error_handling": len([
                    r for r in orchestration_report["detailed_results"] 
                    if "error" in r["test_name"] and r["passed"]
                ])
            }
        }
    
    def _create_capabilities_matrix(self, validation_report: Dict, orchestration_report: Dict) -> Dict[str, Dict[str, str]]:
        """Create a matrix of system capabilities and their status"""
        
        capabilities = {
            "Data Validation": {
                "Required Field Detection": "GOOD" if validation_report["summary"]["average_validation_accuracy"] >= 0.8 else "NEEDS_WORK",
                "Format Validation": "GOOD" if validation_report["summary"]["average_validation_accuracy"] >= 0.7 else "NEEDS_WORK", 
                "Business Logic Validation": "GOOD" if validation_report["summary"]["average_score"] >= 0.7 else "NEEDS_WORK"
            },
            
            "Human-in-the-Loop": {
                "Requirement Detection": "GOOD" if validation_report["summary"]["human_input_detection_accuracy"] >= 80 else "NEEDS_WORK",
                "Workflow Integration": "GOOD" if orchestration_report["summary"]["human_input_handling_rate"] >= 70 else "NEEDS_WORK",
                "Input Processing": "GOOD" if validation_report["summary"]["pass_rate"] >= 70 else "NEEDS_WORK"
            },
            
            "Workflow Orchestration": {
                "Agent Routing": "GOOD" if orchestration_report["summary"]["pass_rate"] >= 80 else "NEEDS_WORK",
                "Validation Integration": "GOOD" if orchestration_report["summary"]["validation_success_rate"] >= 70 else "NEEDS_WORK",
                "Error Handling": "GOOD" if orchestration_report["summary"]["workflow_completion_rate"] >= 80 else "NEEDS_WORK",
                "State Management": "GOOD" if orchestration_report["summary"]["average_score"] >= 0.7 else "NEEDS_WORK"
            },
            
            "Quality Assurance": {
                "Data Quality Scoring": "GOOD" if validation_report["summary"]["average_validation_accuracy"] >= 0.8 else "NEEDS_WORK",
                "Confidence Assessment": "GOOD" if validation_report["summary"]["average_score"] >= 0.7 else "NEEDS_WORK",
                "Issue Detection": "GOOD" if validation_report["summary"]["pass_rate"] >= 75 else "NEEDS_WORK"
            }
        }
        
        return capabilities
    
    def _generate_comprehensive_recommendations(self, validation_report: Dict, orchestration_report: Dict) -> List[str]:
        """Generate comprehensive system improvement recommendations"""
        
        recommendations = []
        
        # Add component-specific recommendations
        recommendations.extend(validation_report.get("recommendations", []))
        recommendations.extend(orchestration_report.get("recommendations", []))
        
        # Add integration recommendations
        validation_pass_rate = validation_report["summary"]["pass_rate"]
        orchestration_pass_rate = orchestration_report["summary"]["pass_rate"]
        
        if validation_pass_rate < 80 or orchestration_pass_rate < 80:
            recommendations.append(
                "System readiness below optimal levels. Consider stabilizing individual components before integration testing."
            )
        
        human_input_detection = validation_report["summary"]["human_input_detection_accuracy"]
        human_input_handling = orchestration_report["summary"]["human_input_handling_rate"]
        
        if abs(human_input_detection - human_input_handling) > 20:
            recommendations.append(
                "Gap detected between validation agent's human input detection and orchestrator's handling capabilities. Align validation criteria with orchestration logic."
            )
        
        # System-level recommendations
        overall_score = (validation_report["summary"]["average_score"] + orchestration_report["summary"]["average_score"]) / 2
        
        if overall_score < 0.8:
            recommendations.append(
                "Overall system performance below production readiness threshold. Focus on critical path improvements and error reduction."
            )
        
        # Add specific improvement areas
        if validation_report["summary"]["average_validation_accuracy"] < 0.8:
            recommendations.append(
                "Validation accuracy needs improvement. Review field validation logic and business rules."
            )
        
        if orchestration_report["summary"]["workflow_completion_rate"] < 85:
            recommendations.append(
                "Workflow completion rate is suboptimal. Review orchestration decision logic and error handling."
            )
        
        return list(set(recommendations))  # Remove duplicates
    
    def _evaluate_quality_gates(self, validation_summary: Dict, orchestration_summary: Dict) -> Dict[str, Dict[str, Any]]:
        """Evaluate system against quality gates"""
        
        quality_gates = {
            "validation_accuracy_gate": {
                "threshold": 80,
                "actual": validation_summary["average_validation_accuracy"] * 100,
                "passed": validation_summary["average_validation_accuracy"] >= 0.8,
                "description": "Validation agent must achieve 80%+ accuracy"
            },
            
            "human_input_detection_gate": {
                "threshold": 75,
                "actual": validation_summary["human_input_detection_accuracy"],
                "passed": validation_summary["human_input_detection_accuracy"] >= 75,
                "description": "Human input detection must be 75%+ accurate"
            },
            
            "orchestration_reliability_gate": {
                "threshold": 80,
                "actual": orchestration_summary["pass_rate"],
                "passed": orchestration_summary["pass_rate"] >= 80,
                "description": "Orchestration pipeline must pass 80%+ of tests"
            },
            
            "workflow_completion_gate": {
                "threshold": 85,
                "actual": orchestration_summary["workflow_completion_rate"],
                "passed": orchestration_summary["workflow_completion_rate"] >= 85,
                "description": "Workflows must complete successfully 85%+ of the time"
            },
            
            "overall_system_readiness_gate": {
                "threshold": 75,
                "actual": (validation_summary["pass_rate"] + orchestration_summary["pass_rate"]) / 2,
                "passed": (validation_summary["pass_rate"] + orchestration_summary["pass_rate"]) / 2 >= 75,
                "description": "Overall system must pass 75%+ of all tests"
            }
        }
        
        return quality_gates
    
    def print_comprehensive_summary(self, report: Dict[str, Any]):
        """Print comprehensive evaluation summary"""
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE EVALUATION SUMMARY")
        print("=" * 80)
        
        overall_summary = report["overall_summary"]
        print(f"Total Tests: {overall_summary['total_tests']}")
        print(f"Total Passed: {overall_summary['total_passed']} ✅")
        print(f"Total Failed: {overall_summary['total_failed']} ❌")
        print(f"Overall Pass Rate: {overall_summary['overall_pass_rate']:.1f}%")
        print(f"Overall Average Score: {overall_summary['overall_average_score']:.3f}")
        
        # System readiness
        readiness = overall_summary["system_readiness_score"]
        print(f"\n🎯 System Readiness: {readiness['level']} ({readiness['score']:.3f})")
        
        # Component status
        print(f"\n📋 Component Status:")
        for component, details in report["component_summaries"].items():
            status_emoji = "✅" if details["status"] == "PASSED" else "❌"
            print(f"  {component.replace('_', ' ').title()}: {details['status']} {status_emoji} ({details['pass_rate']:.1f}%)")
        
        # Quality gates
        print(f"\n🚪 Quality Gates:")
        quality_gates = report["quality_gates"]
        for gate_name, gate_info in quality_gates.items():
            gate_emoji = "✅" if gate_info["passed"] else "❌"
            print(f"  {gate_name.replace('_', ' ').title()}: {gate_emoji} ({gate_info['actual']:.1f}% / {gate_info['threshold']}%)")
        
        # Integration analysis
        print(f"\n🔗 Integration Analysis:")
        integration = report["integration_analysis"]
        for integration_type, details in integration.items():
            if isinstance(details, dict) and "status" in details:
                status_emoji = "✅" if details["status"] == "GOOD" else "⚠️"
                print(f"  {integration_type.replace('_', ' ').title()}: {details['status']} {status_emoji}")
        
        # Recommendations
        if report["comprehensive_recommendations"]:
            print(f"\n💡 COMPREHENSIVE RECOMMENDATIONS:")
            for i, rec in enumerate(report["comprehensive_recommendations"], 1):
                print(f"{i}. {rec}")
    
    def save_comprehensive_report(self, report: Dict[str, Any]) -> str:
        """Save comprehensive report to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"comprehensive_agent_eval_report_{timestamp}.json"
        
        # Clean datetime objects for JSON serialization
        def clean_for_json(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            else:
                return obj
        
        with open(report_file, 'w') as f:
            json.dump(clean_for_json(report), f, indent=2)
        
        return report_file


async def main():
    """Main entry point for comprehensive evaluation"""
    
    # Initialize evaluation suite
    eval_suite = ComprehensiveAgentEvaluationSuite()
    
    try:
        # Run all evaluations
        comprehensive_report = await eval_suite.run_all_evaluations()
        
        # Print summary
        eval_suite.print_comprehensive_summary(comprehensive_report)
        
        # Save report
        report_file = eval_suite.save_comprehensive_report(comprehensive_report)
        print(f"\n📄 Comprehensive report saved to: {report_file}")
        
        # Determine exit code based on overall results
        overall_pass_rate = comprehensive_report["overall_summary"]["overall_pass_rate"]
        system_readiness = comprehensive_report["overall_summary"]["system_readiness_score"]["level"]
        
        if overall_pass_rate >= 80 and system_readiness in ["PRODUCTION_READY", "NEAR_PRODUCTION_READY"]:
            print(f"\n✅ System evaluation PASSED - Ready for deployment")
            return 0
        else:
            print(f"\n❌ System evaluation FAILED - Requires improvement before deployment")
            return 1
        
    except Exception as e:
        logger.error(f"Comprehensive evaluation failed: {str(e)}")
        print(f"\n❌ Evaluation suite encountered an error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())