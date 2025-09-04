#!/usr/bin/env python3
"""
End-to-end test for unified JSON structure validation flow
"""
import asyncio
import json
import sys
from datetime import datetime
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
from agents.invoice_generator_agent import InvoiceGeneratorAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_client_validation_request(unified_data: UnifiedInvoiceData):
    """Simulate what the client sends for validation"""
    
    # Client flattens the unified structure for form display
    flattened_data = {
        # Contract info
        "contract_title": unified_data.contract_title,
        "contract_type": unified_data.contract_type if unified_data.contract_type else None,
        "invoice_date": str(unified_data.invoice_date) if unified_data.invoice_date else None,
        "due_date": str(unified_data.due_date) if unified_data.due_date else None,
        
        # Client info (flattened from unified format)
        "client.name": unified_data.client.name if unified_data.client else None,
        "client.email": unified_data.client.email if unified_data.client else None,
        "client.address": unified_data.client.address if unified_data.client else None,
        "client.phone": unified_data.client.phone if unified_data.client else None,
        
        # Service provider info (flattened from unified format)
        "service_provider.name": unified_data.service_provider.name if unified_data.service_provider else None,
        "service_provider.email": unified_data.service_provider.email if unified_data.service_provider else None,
        "service_provider.address": unified_data.service_provider.address if unified_data.service_provider else None,
        "service_provider.phone": unified_data.service_provider.phone if unified_data.service_provider else None,
        
        # Payment terms (flattened from unified format)
        "payment_terms.amount": float(unified_data.payment_terms.amount) if unified_data.payment_terms and unified_data.payment_terms.amount else None,
        "payment_terms.currency": unified_data.payment_terms.currency if unified_data.payment_terms else None,
        "payment_terms.due_days": unified_data.payment_terms.due_days if unified_data.payment_terms else None,
        "payment_terms.frequency": unified_data.payment_terms.frequency if unified_data.payment_terms and unified_data.payment_terms.frequency else None,
        
        # Additional fields
        "notes": unified_data.notes,
        "special_terms": unified_data.special_terms,
    }
    
    return flattened_data

def simulate_human_corrections(flattened_data: dict):
    """Simulate human corrections applied by the client"""
    
    corrections = {
        "client.name": "Corrected Client Company Ltd.",
        "client.email": "corrected@client.com",
        "payment_terms.amount": 2500.00,
        "contract_title": "Corrected Service Agreement Title",
        "notes": "Updated notes after human validation"
    }
    
    # Apply corrections to flattened data
    corrected_flat = {**flattened_data, **corrections}
    
    # Convert flat structure back to unified format (like client does)
    def convert_flat_to_unified(flat_data: dict):
        unified = {}
        
        for key, value in flat_data.items():
            if '.' in key:
                # Handle nested paths (e.g., "client.name" -> {client: {name: value}})
                keys = key.split('.')
                current = unified
                for i in range(len(keys) - 1):
                    if keys[i] not in current:
                        current[keys[i]] = {}
                    current = current[keys[i]]
                current[keys[-1]] = value
            else:
                # Handle direct properties
                unified[key] = value
        
        # Add required role fields for parties (client would preserve these)
        if 'client' in unified and unified['client']:
            unified['client']['role'] = 'client'
        if 'service_provider' in unified and unified['service_provider']:
            unified['service_provider']['role'] = 'service_provider'
                
        return unified
    
    return convert_flat_to_unified(corrected_flat)

async def test_complete_validation_flow():
    """Test the complete validation flow from contract processing to database save"""
    
    logger.info("🧪 Testing complete validation flow with unified JSON structure")
    logger.info("="*80)
    
    try:
        # Step 1: Create initial unified data (simulates contract processing)
        logger.info("📋 Step 1: Creating initial unified invoice data...")
        
        client = UnifiedParty(
            name="Original Client Inc.",
            email="client@original.com",
            address="123 Original St, City, State 12345",
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
            invoice_id="TEST-E2E-001",
            invoice_date="2024-01-15",
            contract_title="Original Service Agreement",
            client=client,
            service_provider=service_provider,
            payment_terms=payment_terms,
            notes="Original notes from contract processing"
        )
        
        logger.info(f"✅ Created unified data: {unified_data.contract_title}")
        
        # Step 2: Simulate client validation request
        logger.info("🖥️ Step 2: Simulating client validation request...")
        
        flattened_for_client = simulate_client_validation_request(unified_data)
        logger.info(f"✅ Client receives flattened data with {len(flattened_for_client)} fields")
        
        # Step 3: Simulate human corrections
        logger.info("👤 Step 3: Simulating human corrections...")
        
        corrected_unified_data = simulate_human_corrections(flattened_for_client)
        logger.info(f"✅ Human corrections applied: {list(corrected_unified_data.keys())}")
        
        # Step 4: Test validation/resume endpoint workflow
        logger.info("🔄 Step 4: Testing server-side validation workflow...")
        
        # Create workflow state with corrected unified data
        state: WorkflowState = {
            "workflow_id": "test-e2e-validation",
            "user_id": "test-user",
            "contract_name": "E2E Test Contract",
            "unified_invoice_data": corrected_unified_data,
            "human_input_resolved": True,
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
        
        # Step 5: Test correction agent
        logger.info("🔧 Step 5: Testing correction agent with human corrections...")
        
        correction_agent = CorrectionAgent()
        corrected_state = await correction_agent.process(state)
        
        if corrected_state.get("processing_status") == ProcessingStatus.SUCCESS.value:
            logger.info("✅ Correction agent processed successfully")
            
            # Step 6: Test invoice generator agent
            logger.info("💾 Step 6: Testing invoice generator agent...")
            
            invoice_generator = InvoiceGeneratorAgent()
            final_state = await invoice_generator.process(corrected_state)
            
            if final_state.get("processing_status") == ProcessingStatus.SUCCESS.value:
                logger.info("✅ Invoice generator agent processed successfully")
                logger.info(f"📄 Invoice created: {final_state.get('invoice_number')}")
                logger.info(f"🆔 Invoice ID: {final_state.get('invoice_id')}")
                
                # Verify data integrity
                logger.info("🔍 Step 7: Verifying data integrity...")
                
                final_unified = final_state.get("unified_invoice_data_final")
                if final_unified:
                    final_obj = UnifiedInvoiceData(**final_unified)
                    logger.info(f"✅ Final client name: {final_obj.client.name if final_obj.client else 'None'}")
                    logger.info(f"✅ Final amount: ${final_obj.payment_terms.amount if final_obj.payment_terms else '0'}")
                    logger.info(f"✅ Human corrections preserved: {final_obj.metadata.human_input_applied}")
                    
                    # Verify human corrections were preserved
                    if (final_obj.client and final_obj.client.name == "Corrected Client Company Ltd." and
                        final_obj.payment_terms and float(final_obj.payment_terms.amount) == 2500.00 and
                        final_obj.contract_title == "Corrected Service Agreement Title"):
                        logger.info("🎉 SUCCESS: Human corrections preserved through entire workflow!")
                        return True
                    else:
                        logger.error("❌ FAIL: Human corrections were lost")
                        return False
                        
                else:
                    logger.error("❌ FAIL: No final unified data found")
                    return False
                    
            else:
                logger.error("❌ FAIL: Invoice generator failed")
                return False
                
        else:
            logger.error("❌ FAIL: Correction agent failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_test_summary(success: bool):
    """Print test results summary"""
    
    logger.info("\n" + "="*80)
    logger.info("🧪 END-TO-END UNIFIED VALIDATION FLOW TEST RESULTS")
    logger.info("="*80)
    
    if success:
        logger.info("🎉 ✅ ALL TESTS PASSED!")
        logger.info("✅ Human validation corrections flow through unified JSON structure")
        logger.info("✅ Client-server integration working correctly")
        logger.info("✅ Data integrity maintained throughout workflow")
        logger.info("✅ Unified format prevents data loss issues")
    else:
        logger.info("❌ ⚠️ TESTS FAILED!")
        logger.info("❌ Issues found in validation flow - review implementation")
    
    logger.info("="*80)

async def main():
    """Run end-to-end validation test"""
    
    success = await test_complete_validation_flow()
    print_test_summary(success)
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)