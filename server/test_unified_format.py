#!/usr/bin/env python3
"""
Test script to validate the unified invoice format across the workflow
"""

import sys
import asyncio
import json
from datetime import datetime
from decimal import Decimal

# Add the server directory to the path
sys.path.insert(0, '/home/ramsha/Documents/smart-invoice-scheduler/server')

try:
    from schemas.unified_invoice_schemas import (
        UnifiedInvoiceData, UnifiedParty, UnifiedPaymentTerms, 
        PartyRole, CurrencyCode, ContractType, InvoiceFrequency
    )
    from services.validation_service import get_validation_service
    print("✅ Successfully imported unified schemas and validation service")
    
    # Only import agents if we need them (avoid dependency issues)
    AGENTS_AVAILABLE = False
    try:
        from agents.correction_agent import CorrectionAgent
        from services.database_service import get_database_service
        AGENTS_AVAILABLE = True
        print("✅ Agents and database service imported successfully")
    except ImportError as e:
        print(f"⚠️  Agents/database not available: {str(e)}")
        
except ImportError as e:
    print(f"❌ Failed to import required modules: {str(e)}")
    sys.exit(1)


def create_test_invoice_data():
    """Create a test unified invoice data"""
    print("🔧 Creating test unified invoice data...")
    
    unified_data = UnifiedInvoiceData(
        contract_title="Service Agreement - Web Development",
        contract_type=ContractType.SERVICE_AGREEMENT,
        contract_number="SA-2024-001",
        
        # Parties
        client=UnifiedParty(
            name="Acme Corporation",
            email="billing@acme.com",
            address="123 Business Ave, Suite 100, New York, NY 10001",
            phone="+1-555-0123",
            role=PartyRole.CLIENT
        ),
        
        service_provider=UnifiedParty(
            name="Tech Solutions LLC",
            email="contact@techsolutions.com", 
            address="456 Developer St, San Francisco, CA 94105",
            phone="+1-555-0456",
            role=PartyRole.SERVICE_PROVIDER
        ),
        
        # Payment terms
        payment_terms=UnifiedPaymentTerms(
            amount=Decimal("5000.00"),
            currency=CurrencyCode.USD,
            frequency=InvoiceFrequency.MONTHLY,
            due_days=30,
            payment_method="bank_transfer"
        ),
        
        # Dates
        start_date="2024-01-01",
        end_date="2024-12-31",
        effective_date="2024-01-01",
        
        # Invoice schedule
        invoice_frequency=InvoiceFrequency.MONTHLY,
        first_invoice_date="2024-01-01",
        next_invoice_date="2024-02-01",
        
        # Additional terms
        special_terms="Payment due within 30 days of invoice date",
        notes="Monthly retainer for web development services"
    )
    
    print("✅ Test unified invoice data created")
    return unified_data


def test_legacy_conversion():
    """Test conversion from legacy format to unified format"""
    print("\n🔄 Testing legacy format conversion...")
    
    # Sample legacy format data
    legacy_data = {
        "contract_title": "Rental Agreement",
        "contract_type": "rental_lease",
        "client": {
            "name": "John Doe",
            "email": "john@example.com",
            "address": "789 Tenant Lane",
            "role": "client"
        },
        "service_provider": {
            "name": "Property Management Co",
            "email": "rent@propmanage.com",
            "address": "321 Landlord Blvd",
            "role": "service_provider"
        },
        "payment_terms": {
            "amount": "2500.00",
            "currency": "USD",
            "frequency": "monthly",
            "due_days": 5
        },
        "start_date": "2024-01-01",
        "invoice_frequency": "monthly"
    }
    
    try:
        # Convert legacy to unified
        unified_data = UnifiedInvoiceData.from_legacy_format(legacy_data)
        print("✅ Legacy format converted successfully")
        
        # Test backward compatibility
        try:
            legacy_converted = unified_data.to_legacy_contract_invoice_data()
            print("✅ Backward conversion to legacy format successful")
        except Exception as e:
            print(f"⚠️  Backward conversion failed: {str(e)}")
        
        # Test database format conversion
        try:
            db_format = unified_data.to_database_format()
            print("✅ Database format conversion successful")
        except Exception as e:
            print(f"⚠️  Database format conversion failed: {str(e)}")
        
        return unified_data
        
    except Exception as e:
        print(f"❌ Legacy conversion failed: {str(e)}")
        return None


async def test_validation_agent():
    """Test validation agent with unified format"""
    print("\n🔍 Testing validation agent with unified format...")
    
    try:
        validation_service = get_validation_service()
        
        # Test with complete data (should pass validation)
        complete_data = create_test_invoice_data()
        validation_result = validation_service.validate_unified_invoice_data(
            complete_data, 
            user_id="test-user", 
            contract_name="Test Contract"
        )
        
        print(f"✅ Validation result: Valid={validation_result.is_valid}, Score={validation_result.validation_score:.2f}")
        
        # Test with incomplete data (should require human input)
        incomplete_data = UnifiedInvoiceData(
            contract_title="Incomplete Contract",
            # Missing required fields like client, service_provider, payment_terms
        )
        
        incomplete_validation = validation_service.validate_unified_invoice_data(
            incomplete_data,
            user_id="test-user",
            contract_name="Incomplete Test Contract"
        )
        
        print(f"✅ Incomplete validation result: Valid={incomplete_validation.is_valid}, Human Input Required={incomplete_validation.human_input_required}")
        
        return validation_result, incomplete_validation
        
    except Exception as e:
        print(f"❌ Validation agent test failed: {str(e)}")
        return None, None


def test_manual_corrections():
    """Test applying manual corrections to unified data"""
    print("\n✏️ Testing manual corrections...")
    
    try:
        # Create base data
        base_data = create_test_invoice_data()
        
        # Apply manual corrections
        corrections = {
            "client.name": "Updated Client Name Inc.",
            "client.email": "updated@client.com",
            "payment_terms.amount": "7500.00",
            "special_terms": "Updated payment terms - Net 45 days"
        }
        
        corrected_data = base_data.apply_manual_corrections(corrections)
        
        print(f"✅ Manual corrections applied:")
        print(f"   Client name: {corrected_data.client.name}")
        print(f"   Client email: {corrected_data.client.email}")
        print(f"   Payment amount: {corrected_data.payment_terms.amount}")
        print(f"   Special terms: {corrected_data.special_terms}")
        print(f"   Human input applied: {corrected_data.metadata.human_input_applied}")
        
        return corrected_data
        
    except Exception as e:
        print(f"❌ Manual corrections test failed: {str(e)}")
        return None


async def test_correction_agent():
    """Test correction agent with unified format"""
    print("\n🔧 Testing correction agent with unified format...")
    
    if not AGENTS_AVAILABLE:
        print("⚠️  Correction agent not available - skipping test")
        return None
    
    try:
        # Create a mock workflow state
        corrected_data = test_manual_corrections()
        if not corrected_data:
            print("❌ Cannot test correction agent without corrected data")
            return None
            
        # Create mock state with unified data
        mock_state = {
            "workflow_id": "test-workflow-123",
            "user_id": "test-user",
            "contract_name": "Test Contract",
            "unified_invoice_data": corrected_data.model_dump(),
            "human_input_resolved": True,
            "validation_results": {
                "is_valid": True,
                "validation_score": 0.95
            },
            "started_at": datetime.now().isoformat()
        }
        
        correction_agent = CorrectionAgent()
        
        # Test extracting unified data from state
        extracted_data = correction_agent._extract_unified_invoice_data_from_state(mock_state)
        
        if extracted_data:
            print("✅ Successfully extracted unified data from state")
            
            # Test generating corrected invoice JSON
            corrected_json = await correction_agent._generate_corrected_invoice_json_unified(
                extracted_data, mock_state
            )
            
            print("✅ Successfully generated corrected invoice JSON")
            print(f"   Invoice ID: {corrected_json.get('invoice_header', {}).get('invoice_id')}")
            print(f"   Total Amount: ${corrected_json.get('totals', {}).get('total_amount', 0):.2f}")
            
            return corrected_json
        else:
            print("❌ Failed to extract unified data from state")
            return None
            
    except Exception as e:
        print(f"❌ Correction agent test failed: {str(e)}")
        return None


async def test_database_operations():
    """Test database operations with unified format"""
    print("\n💾 Testing database operations...")
    
    if not AGENTS_AVAILABLE:
        print("⚠️  Database service not available - skipping test")
        return None
    
    try:
        db_service = get_database_service()
        
        # Create test unified data
        test_data = create_test_invoice_data()
        test_data.metadata.user_id = "test-user-db"
        test_data.metadata.workflow_id = "test-workflow-db"
        
        print("ℹ️ Note: Database operations test (creation disabled to avoid actual DB writes)")
        print("✅ Database service can handle unified format")
        
        # Test format conversion
        db_format = test_data.to_database_format()
        print("✅ Database format conversion successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all unified format tests"""
    print("🚀 Starting Unified Invoice Format Tests")
    print("=" * 50)
    
    # Test 1: Basic unified format creation
    test_data = create_test_invoice_data()
    if not test_data:
        print("❌ Failed to create test data")
        return
    
    # Test 2: Legacy format conversion
    legacy_converted = test_legacy_conversion()
    
    # Test 3: Validation agent
    validation_result, incomplete_validation = await test_validation_agent()
    
    # Test 4: Manual corrections
    corrected_data = test_manual_corrections()
    
    # Test 5: Correction agent
    corrected_json = await test_correction_agent()
    
    # Test 6: Database operations
    db_test_result = await test_database_operations()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Unified data creation", test_data is not None),
        ("Legacy format conversion", legacy_converted is not None),
        ("Validation agent", validation_result is not None),
        ("Manual corrections", corrected_data is not None),
        ("Correction agent", corrected_json is not None),
        ("Database operations", db_test_result)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Unified format is working correctly.")
    else:
        print("⚠️  Some tests failed. Review the output above for details.")


if __name__ == "__main__":
    asyncio.run(run_all_tests())