#!/usr/bin/env python3
"""
Debug script to inspect what data is stored in Pinecone
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db import get_pinecone_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_pinecone_data():
    """Inspect what data is stored in Pinecone"""
    try:
        # Get Pinecone client
        index = get_pinecone_client()
        
        # Get index stats
        stats = index.describe_index_stats()
        print("=== Pinecone Index Stats ===")
        print(f"Total vectors: {stats.total_vector_count}")
        print(f"Namespaces: {stats.namespaces}")
        print()
        
        # Try to query with minimal filter to see what's there
        print("=== Querying for any data ===")
        dummy_query = [0.0] * 768  # Using 768 dimensions based on index error
        
        # Query without filters to see all data
        response = index.query(
            vector=dummy_query,
            top_k=10,
            include_metadata=True
        )
        
        if response.matches:
            print(f"Found {len(response.matches)} matches:")
            for i, match in enumerate(response.matches):
                print(f"\nMatch {i+1}:")
                print(f"  ID: {match.id}")
                print(f"  Score: {match.score}")
                if match.metadata:
                    print(f"  Metadata:")
                    for key, value in match.metadata.items():
                        if key == 'text':
                            print(f"    {key}: {value[:100]}..." if len(str(value)) > 100 else f"    {key}: {value}")
                        else:
                            print(f"    {key}: {value}")
        else:
            print("No matches found - index might be empty")
        
        # Query specifically for contracts
        print("\n=== Querying specifically for contracts ===")
        contract_response = index.query(
            vector=dummy_query,
            top_k=10,
            include_metadata=True,
            filter={"document_type": "contract"}
        )
        
        if contract_response.matches:
            print(f"Found {len(contract_response.matches)} contract matches:")
            for i, match in enumerate(contract_response.matches):
                print(f"\nContract {i+1}:")
                print(f"  ID: {match.id}")
                if match.metadata:
                    contract_name = match.metadata.get('contract_name', 'Unknown')
                    user_id = match.metadata.get('user_id', 'Unknown')
                    print(f"  Contract: {contract_name}")
                    print(f"  User ID: {user_id}")
        else:
            print("No contract data found in index")
            
        # Query specifically for "Prompt history.pdf"
        print('\n=== Querying specifically for "Prompt history.pdf" ===')
        prompt_response = index.query(
            vector=dummy_query,
            top_k=10,
            include_metadata=True,
            filter={"contract_name": "Prompt history.pdf"}
        )
        
        if prompt_response.matches:
            print(f"Found {len(prompt_response.matches)} matches for 'Prompt history.pdf':")
            for i, match in enumerate(prompt_response.matches):
                print(f"\nMatch {i+1}:")
                print(f"  ID: {match.id}")
                if match.metadata:
                    for key, value in match.metadata.items():
                        if key == 'text':
                            print(f"    {key}: {value[:100]}..." if len(str(value)) > 100 else f"    {key}: {value}")
                        else:
                            print(f"    {key}: {value}")
        else:
            print("No data found for 'Prompt history.pdf'")
            
    except Exception as e:
        logger.error(f"Error inspecting Pinecone: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    inspect_pinecone_data()