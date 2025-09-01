"""
Evaluation endpoint for contract processing agent testing and invoice data extraction
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import json
from datetime import datetime, date

def datetime_serializer(obj):
    """JSON serializer for datetime and date objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

from schemas.workflow_schemas import WorkflowState
from tests.contract_processing_evals import ContractProcessingEvaluator
from agents.contract_processing_agent import ContractProcessingAgent
from services.contract_rag_service import get_contract_rag_service

router = APIRouter(prefix="/eval", tags=["evaluation"])

# Pydantic models for request bodies
class SingleContractTestRequest(BaseModel):
    contract_content: str
    expected_fields: Optional[Dict[str, Any]] = None

# Initialize services
contract_agent = ContractProcessingAgent()
contract_rag_service = get_contract_rag_service()

@router.post("/contract-processing/run-evals")
async def run_contract_processing_evals():
    """
    Run comprehensive evaluation tests on the contract processing agent
    
    Returns:
        Detailed evaluation report with scores, metrics, and recommendations
    """
    try:
        evaluator = ContractProcessingEvaluator()
        report = await evaluator.run_all_evaluations()
        
        return {
            "status": "success",
            "message": "Contract processing evaluation completed",
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )

@router.post("/contract-processing/test-single")
async def test_single_contract(request: SingleContractTestRequest):
    """
    Test contract processing on a single contract with optional expected results
    
    Args:
        contract_content: Raw contract text to process
        expected_fields: Optional dict of expected extraction results for comparison
        
    Returns:
        Processing results with extracted invoice data and evaluation metrics
    """
    try:
        # Create test workflow state
        test_state: WorkflowState = {
            "workflow_id": f"test-single-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": "test-user",
            "contract_file": request.contract_content,
            "contract_name": "single-test-contract",
            "contract_data": {
                "context": request.contract_content,
                "extracted_at": datetime.now().isoformat()
            },
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
            "processing_status": "pending",
            "current_agent": "contract_processing",
            "retry_reasons": [],
            "learned_patterns": {},
            "improvement_suggestions": [],
            "success_metrics": {},
            "orchestrator_decision_count": 0,
            "workflow_completed": False,
            "started_at": datetime.now().isoformat(),
            "last_updated_at": datetime.now().isoformat()
        }
        
        # Execute contract processing
        start_time = datetime.now()
        result_state = contract_agent.execute(test_state)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract invoice data
        invoice_data = result_state.get("invoice_data", {})
        extracted_data = {}
        
        if isinstance(invoice_data, dict):
            invoice_response = invoice_data.get("invoice_response", {})
            if isinstance(invoice_response, dict):
                extracted_data = invoice_response.get("invoice_data", {})
        
        # Prepare response
        response = {
            "processing_results": {
                "workflow_id": result_state.get("workflow_id"),
                "processing_status": result_state.get("processing_status"),
                "confidence_level": result_state.get("confidence_level"),
                "quality_score": result_state.get("quality_score"),
                "execution_time_seconds": execution_time,
                "errors": result_state.get("errors", [])
            },
            "extracted_invoice_data": extracted_data,
            "raw_invoice_response": invoice_data,
            "contract_analysis": {
                "text_length": len(request.contract_content),
                "processing_timestamp": datetime.now().isoformat()
            }
        }
        
        # Add evaluation if expected fields provided
        if request.expected_fields:
            evaluation = _evaluate_extraction_results(extracted_data, request.expected_fields)
            response["evaluation"] = evaluation
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contract processing test failed: {str(e)}"
        )

@router.get("/contract-processing/extract-invoice/{user_id}/{contract_name}")
async def extract_invoice_data(user_id: str, contract_name: str):
    """
    Extract invoice data for a specific contract using RAG service
    
    Args:
        user_id: User identifier
        contract_name: Name of the contract to process
        
    Returns:
        Extracted invoice data with metadata
    """
    try:
        # Generate invoice data using existing RAG service
        invoice_response = contract_rag_service.generate_invoice_data(user_id, contract_name)
        
        return {
            "status": "success",
            "user_id": user_id,
            "contract_name": contract_name,
            "invoice_data": invoice_response.model_dump(),
            "confidence_score": invoice_response.confidence_score,
            "extracted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invoice extraction failed: {str(e)}"
        )

@router.post("/contract-processing/batch-test")
async def batch_test_contracts(
    contracts: List[Dict[str, Any]]
):
    """
    Run batch testing on multiple contracts
    
    Args:
        contracts: List of contract test cases with structure:
                  {"name": str, "content": str, "expected": Dict[str, Any]}
    
    Returns:
        Batch processing results with individual test outcomes
    """
    try:
        results = []
        
        for i, contract in enumerate(contracts):
            contract_name = contract.get("name", f"test-contract-{i+1}")
            contract_content = contract.get("content", "")
            expected_fields = contract.get("expected", {})
            
            if not contract_content:
                results.append({
                    "contract_name": contract_name,
                    "status": "skipped",
                    "error": "No contract content provided"
                })
                continue
            
            try:
                # Process individual contract
                test_state: WorkflowState = {
                    "workflow_id": f"batch-test-{i+1}-{datetime.now().strftime('%H%M%S')}",
                    "user_id": "batch-test-user",
                    "contract_file": f"{contract_name}.txt",
                    "contract_name": contract_name,
                    "contract_data": {
                        "context": contract_content,
                        "extracted_at": datetime.now().isoformat()
                    },
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
                    "processing_status": "pending",
                    "current_agent": "contract_processing",
                    "retry_reasons": [],
                    "learned_patterns": {},
                    "improvement_suggestions": [],
                    "success_metrics": {},
                    "orchestrator_decision_count": 0,
                    "workflow_completed": False,
                    "started_at": datetime.now().isoformat(),
                    "last_updated_at": datetime.now().isoformat()
                }
                
                start_time = datetime.now()
                result_state = contract_agent.execute(test_state)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Extract invoice data
                invoice_data = result_state.get("invoice_data", {})
                extracted_data = {}
                
                if isinstance(invoice_data, dict):
                    invoice_response = invoice_data.get("invoice_response", {})
                    if isinstance(invoice_response, dict):
                        extracted_data = invoice_response.get("invoice_data", {})
                
                # Evaluate if expected fields provided
                evaluation = None
                if expected_fields:
                    evaluation = _evaluate_extraction_results(extracted_data, expected_fields)
                
                results.append({
                    "contract_name": contract_name,
                    "status": "completed",
                    "processing_status": result_state.get("processing_status"),
                    "confidence_level": result_state.get("confidence_level"),
                    "execution_time": execution_time,
                    "extracted_data": extracted_data,
                    "evaluation": evaluation,
                    "errors": result_state.get("errors", [])
                })
                
            except Exception as e:
                results.append({
                    "contract_name": contract_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Generate batch summary
        total_tests = len(results)
        completed_tests = len([r for r in results if r["status"] == "completed"])
        failed_tests = len([r for r in results if r["status"] == "failed"])
        
        summary = {
            "total_contracts": total_tests,
            "completed": completed_tests,
            "failed": failed_tests,
            "success_rate": (completed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        return {
            "status": "success",
            "summary": summary,
            "results": results,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch testing failed: {str(e)}"
        )

def _evaluate_extraction_results(extracted: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to evaluate extraction results against expected values
    
    Args:
        extracted: Actually extracted data
        expected: Expected extraction results
        
    Returns:
        Evaluation metrics and details
    """
    evaluation = {
        "field_scores": {},
        "missing_fields": [],
        "extra_fields": [],
        "overall_score": 0.0,
        "match_details": {}
    }
    
    total_score = 0.0
    max_possible_score = len(expected)
    
    # Evaluate each expected field
    for field, expected_value in expected.items():
        actual_value = extracted.get(field)
        
        if actual_value is None:
            evaluation["missing_fields"].append(field)
            evaluation["field_scores"][field] = 0.0
            evaluation["match_details"][field] = {
                "expected": expected_value,
                "actual": None,
                "match_type": "missing"
            }
        else:
            # Calculate field score
            if expected_value == actual_value:
                field_score = 1.0
                match_type = "exact"
            elif isinstance(expected_value, str) and isinstance(actual_value, str):
                if expected_value.lower().strip() == actual_value.lower().strip():
                    field_score = 0.9
                    match_type = "case_insensitive"
                elif expected_value.lower() in actual_value.lower() or actual_value.lower() in expected_value.lower():
                    field_score = 0.7
                    match_type = "partial"
                else:
                    field_score = 0.1
                    match_type = "no_match"
            elif isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                tolerance = 0.01 * abs(expected_value) if expected_value != 0 else 0.01
                if abs(expected_value - actual_value) <= tolerance:
                    field_score = 1.0
                    match_type = "numeric_exact"
                elif abs(expected_value - actual_value) <= tolerance * 10:
                    field_score = 0.6
                    match_type = "numeric_close"
                else:
                    field_score = 0.0
                    match_type = "numeric_mismatch"
            else:
                field_score = 0.3
                match_type = "type_mismatch"
            
            evaluation["field_scores"][field] = field_score
            evaluation["match_details"][field] = {
                "expected": expected_value,
                "actual": actual_value,
                "match_type": match_type,
                "score": field_score
            }
            total_score += field_score
    
    # Check for extra fields
    for field in extracted.keys():
        if field not in expected:
            evaluation["extra_fields"].append(field)
    
    # Calculate overall score
    evaluation["overall_score"] = total_score / max_possible_score if max_possible_score > 0 else 0.0
    
    return evaluation