#!/usr/bin/env python3
"""
Test script for document listing API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_document_list(auth_token: str):
    """Test document listing endpoints"""
    
    print("🚀 Testing Document List API")
    print("=" * 50)
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Test 1: List all documents
    print("\n📋 Test 1: List all documents")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{BASE_URL}/documents/",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        if response.content:
            data = response.json()
            print(f"Total Documents: {data.get('total', 0)}")
            print(f"Documents in Response: {len(data.get('documents', []))}")
            
            if data.get('documents'):
                print("\n📄 Sample Document:")
                print(json.dumps(data['documents'][0], indent=2))
            else:
                print("ℹ️  No documents found in bucket")
                
        else:
            print("Empty response")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the server running?")
        return
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    
    # Test 2: List contracts only
    print("\n📋 Test 2: List contract documents only")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{BASE_URL}/documents/?document_type=contract",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        if response.content:
            data = response.json()
            print(f"Contract Documents: {data.get('total', 0)}")
            print(f"Documents in Response: {len(data.get('documents', []))}")
        else:
            print("Empty response")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 3: List with pagination
    print("\n📋 Test 3: List with pagination (limit=2)")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{BASE_URL}/documents/?limit=2&offset=0",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        if response.content:
            data = response.json()
            print(f"Total Documents: {data.get('total', 0)}")
            print(f"Limit: {data.get('limit')}")
            print(f"Offset: {data.get('offset')}")
            print(f"Has More: {data.get('has_more')}")
            print(f"Documents in Response: {len(data.get('documents', []))}")
        else:
            print("Empty response")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def check_bucket_direct():
    """Check if there are any issues with GCP bucket access"""
    print("\n🔍 Troubleshooting Tips:")
    print("=" * 50)
    print("1. Check if documents were actually uploaded to GCP Storage")
    print("2. Verify GCP credentials and bucket permissions")
    print("3. Check server logs for GCP Storage errors")
    print("4. Ensure PROJECT_ID and GCP_STORAGE_BUCKET env vars are set")
    print("5. Try uploading a test document first using /documents/upload")
    
    print("\n📝 Expected Bucket Structure:")
    print("bucket-name/")
    print("├── contract/")
    print("│   └── 20240115_103000_rental_agreement.pdf")
    print("├── invoice/") 
    print("│   └── 20240115_120000_utility_bill.pdf")
    print("└── other/")
    print("    └── 20240115_130000_document.pdf")

def main():
    auth_token = input("Enter your JWT token: ").strip()
    
    if not auth_token:
        print("❌ JWT token is required")
        return
    
    test_document_list(auth_token)
    check_bucket_direct()

if __name__ == "__main__":
    main()