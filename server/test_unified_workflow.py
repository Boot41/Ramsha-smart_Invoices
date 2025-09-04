#!/usr/bin/env python3
"""
Test script to verify the unified JSON structure workflow
"""
import asyncio
import json
import sys
from datetime import datetime, date
import logging

# Add server to path
sys.path.append('.')

from schemas.unified_invoice_schemas import (
    UnifiedInvoiceData, UnifiedParty, UnifiedPaymentTerms, 
    PartyRole, CurrencyCode, InvoiceStatus
)
from schemas.workflow_schemas import WorkflowState, ProcessingStatus
from agents.contract_processing_agent import ContractProcessingAgent
from agents.correction_agent import CorrectionAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_unified_data() -> UnifiedInvoiceData:
    """Create test unified invoice data"""
    
    client = UnifiedParty(
        name="Test Client Inc.",
        email="client@test.com",
        address="123 Client St, City, State 12345",
        phone="+1-555-0123",
        role=PartyRole.CLIENT
    )
    
    service_provider = UnifiedParty(
        name="Service Provider LLC",
        email="provider@service.com", 
        address="456 Provider Ave, City, State 67890",
        phone="+1-555-0456",
        role=PartyRole.SERVICE_PROVIDER
    )
    
    payment_terms = UnifiedPaymentTerms(
        amount=1500.00,
        currency=CurrencyCode.USD,
        due_days=30,
        payment_method="bank_transfer"
    )
    
    unified_data = UnifiedInvoiceData(
        invoice_id="TEST-001",
        invoice_date=date.today().isoformat(),
        contract_title="Test Service Agreement",
        client=client,
        service_provider=service_provider,
        payment_terms=payment_terms,
        notes="Test unified invoice data structure"
    )
    
    return unified_data

def test_unified_data_conversions():
    """Test conversions between unified and legacy formats"""
    
    logger.info("🧪 Testing unified data conversions...")
    
    # Create test unified data
    unified_data = create_test_unified_data()
    
    # Test conversion to legacy format
    legacy_data = unified_data.to_legacy_contract_invoice_data()
    logger.info(f"✅ Legacy conversion - keys: {list(legacy_data.keys())}")
    
    # Test conversion to correction agent format
    correction_format = unified_data.to_correction_agent_format()
    logger.info(f"✅ Correction agent format - keys: {list(correction_format.keys())}")
    
    # Test conversion to database format
    database_format = unified_data.to_database_format()
    logger.info(f"✅ Database format - keys: {list(database_format.keys())}")
    
    # Test round-trip conversion
    reconstructed = UnifiedInvoiceData.from_legacy_format(legacy_data)
    logger.info(f"✅ Round-trip conversion successful")
    
    return True

def test_human_corrections():
    """Test applying human corrections to unified data"""
    
    logger.info("🧪 Testing human corrections on unified data...")
    
    unified_data = create_test_unified_data()
    
    # Simulate human corrections
    corrections = {
        "client.name": "Corrected Client Name Inc.",
        "client.email": "corrected@client.com",
        "payment_terms.amount": 2000.00,
        "contract_title": "Corrected Service Agreement",
        "notes": "Updated notes after human review"
    }
    
    # Apply corrections
    corrected_data = unified_data.apply_manual_corrections(corrections)
    
    # Verify corrections were applied
    assert corrected_data.client.name == "Corrected Client Name Inc."
    assert corrected_data.client.email == "corrected@client.com"
    assert float(corrected_data.payment_terms.amount) == 2000.00
    assert corrected_data.contract_title == "Corrected Service Agreement"
    assert corrected_data.notes == "Updated notes after human review"
    assert corrected_data.metadata.human_input_applied == True
    assert corrected_data.metadata.human_reviewed == True
    
    logger.info("✅ Human corrections applied successfully")
    return True

def test_workflow_state_integration():
    """Test integration with workflow state"""
    
    logger.info("🧪 Testing workflow state integration...")
    
    # Create mock workflow state with unified data
    unified_data = create_test_unified_data()
    
    state: WorkflowState = {
        "workflow_id": "test-workflow-001",
        "user_id": "test-user",
        "contract_name": "Test Contract",
        "unified_invoice_data": unified_data.model_dump(),
        "processing_status": ProcessingStatus.SUCCESS.value,
        "current_agent": "test",
        "attempt_count": 1,
        "max_attempts": 3,
        "errors": [],
        "feedback_history": [],
        "quality_score": 0.9,
        "confidence_level": 0.85,
        "retry_reasons": [],
        "learned_patterns": {},
        "improvement_suggestions": [],
        "success_metrics": {},
        "started_at": datetime.now().isoformat(),
        "last_updated_at": datetime.now().isoformat(),
        "contract_file": None,
        "contract_data": None,
        "validation_results": None,
        "invoice_data": None,
        "schedule_data": None,
        "final_invoice": None
    }
    
    # Test extracting unified data from state
    extracted_data = state.get("unified_invoice_data")
    if extracted_data:
        reconstructed = UnifiedInvoiceData(**extracted_data)
        logger.info(f"✅ Successfully extracted unified data from workflow state")
        logger.info(f"   - Client: {reconstructed.client.name if reconstructed.client else 'None'}")
        logger.info(f"   - Amount: ${reconstructed.payment_terms.amount if reconstructed.payment_terms else '0'}")
        logger.info(f"   - Workflow ID: {reconstructed.metadata.workflow_id}")
    
    return True

async def test_correction_agent_integration():
    """Test correction agent with unified data"""
    
    logger.info("🧪 Testing correction agent integration...")
    
    try:
        # Create workflow state with unified data
        unified_data = create_test_unified_data()
        
        state: WorkflowState = {
            "workflow_id": "test-workflow-002",
            "user_id": "test-user",
            "contract_name": "Test Contract for Correction",
            "unified_invoice_data": unified_data.model_dump(),
            "human_input_resolved": True,  # Simulate human input completion
            "human_input_completed": True,
            "processing_status": ProcessingStatus.IN_PROGRESS.value,
            "current_agent": "correction",
            "attempt_count": 1,
            "max_attempts": 3,
            "errors": [],
            "feedback_history": [],
            "quality_score": 0.9,
            "confidence_level": 0.85,
            "retry_reasons": [],
            "learned_patterns": {},
            "improvement_suggestions": [],
            "success_metrics": {},
            "started_at": datetime.now().isoformat(),
            "last_updated_at": datetime.now().isoformat(),
            "contract_file": None,
            "contract_data": None,
            "validation_results": {"is_valid": True, "validation_score": 0.9},
            "invoice_data": None,
            "schedule_data": None,
            "final_invoice": None
        }
        
        # Test correction agent processing
        correction_agent = CorrectionAgent()
        result_state = await correction_agent.process(state)
        
        if result_state.get("processing_status") == ProcessingStatus.SUCCESS.value:
            logger.info("✅ Correction agent processed unified data successfully")
            
            # Check if unified data was preserved and enhanced
            final_unified = result_state.get("unified_invoice_data_final")
            if final_unified:
                logger.info("✅ Final unified data generated")
                logger.info(f"   - Status: {result_state.get('processing_status')}")
                logger.info(f"   - Correction completed: {result_state.get('correction_completed')}")
            
            return True
        else:
            logger.error(f"❌ Correction agent failed: {result_state.get('processing_status')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Correction agent test failed: {e}")
        return False

def print_test_summary(results: dict):
    """Print test results summary"""
    
    logger.info("\n" + "="*60)
    logger.info("🧪 UNIFIED JSON STRUCTURE WORKFLOW TEST RESULTS")
    logger.info("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("-"*60)
    logger.info(f"📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Unified workflow is ready.")
    else:
        logger.info("⚠️ Some tests failed. Review implementation.")

async def main():
    """Run all tests"""
    
    logger.info("🚀 Starting Unified JSON Structure Workflow Tests")
    logger.info("="*60)
    
    results = {}
    
    # Test 1: Basic unified data conversions
    try:
        results["Unified Data Conversions"] = test_unified_data_conversions()
    except Exception as e:
        logger.error(f"❌ Unified data conversions test failed: {e}")
        results["Unified Data Conversions"] = False
    
    # Test 2: Human corrections
    try:
        results["Human Corrections"] = test_human_corrections()
    except Exception as e:
        logger.error(f"❌ Human corrections test failed: {e}")
        results["Human Corrections"] = False
    
    # Test 3: Workflow state integration  
    try:
        results["Workflow State Integration"] = test_workflow_state_integration()
    except Exception as e:
        logger.error(f"❌ Workflow state integration test failed: {e}")
        results["Workflow State Integration"] = False
    
    # Test 4: Correction agent integration
    try:
        results["Correction Agent Integration"] = await test_correction_agent_integration()
    except Exception as e:
        logger.error(f"❌ Correction agent integration test failed: {e}")
        results["Correction Agent Integration"] = False
    
    # Print summary
    print_test_summary(results)
    
    return all(results.values())

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)