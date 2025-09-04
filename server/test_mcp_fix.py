#!/usr/bin/env python3
"""
Test script to verify MCP integration is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.mcp_service import get_mcp_service

def test_mcp_integration():
    print("🔍 Testing MCP Google Drive Integration")
    print("=" * 50)
    
    try:
        mcp_service = get_mcp_service()
        print("✅ MCP service initialized successfully")
        
        # Test 1: General contracts search
        print("\n📄 Testing general contracts search...")
        contracts = mcp_service.search_contracts()
        print(f"Found {len(contracts)} general contracts:")
        for i, contract in enumerate(contracts):
            print(f"  {i+1}. {contract['name']}")
            print(f"     ID: {contract['file_id']}")
            print(f"     Type: {contract['mime_type']}")
        
        # Test 2: Rental contracts search
        print("\n🏠 Testing rental contracts search...")
        rental_contracts = mcp_service.search_rental_contracts()
        print(f"Found {len(rental_contracts)} rental contracts:")
        for i, contract in enumerate(rental_contracts):
            print(f"  {i+1}. {contract['name']}")
            print(f"     ID: {contract['file_id']}")
            print(f"     Type: {contract['mime_type']}")
        
        # Test 3: Raw search
        print("\n🔍 Testing raw search...")
        raw_files = mcp_service.search_files("rental")
        print(f"Found {len(raw_files)} files with 'rental' search:")
        for i, file_info in enumerate(raw_files):
            print(f"  {i+1}. {file_info['name']}")
        
        print("\n" + "=" * 50)
        print("🎉 MCP Integration Test Results:")
        print(f"   General contracts: {len(contracts)}")
        print(f"   Rental contracts: {len(rental_contracts)}")
        print(f"   Raw rental files: {len(raw_files)}")
        
        if len(rental_contracts) > 0:
            print("✅ SUCCESS: Rental contracts are being found!")
        else:
            print("❌ ISSUE: No rental contracts found")
            
        return len(contracts) > 0 or len(rental_contracts) > 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mcp_integration()
    sys.exit(0 if success else 1)