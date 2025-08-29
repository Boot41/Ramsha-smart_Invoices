#!/usr/bin/env python3
"""
Test Pinecone Integration Script

This script tests the complete Pinecone integration including:
- Creating embeddings
- Storing vectors in Pinecone
- Searching for similar vectors
- Managing vector lifecycle
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import from project
sys.path.append(str(Path(__file__).parent.parent))

from services.pinecone_service import get_pinecone_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def test_health_check():
    """Test Pinecone service health check"""
    logger.info("🏥 Testing health check...")
    
    try:
        service = get_pinecone_service()
        result = service.health_check()
        
        if result["status"] == "healthy":
            logger.info("✅ Health check passed!")
            return True
        else:
            logger.error(f"❌ Health check failed: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Health check error: {str(e)}")
        return False


def test_embedding_creation():
    """Test embedding creation"""
    logger.info("🧠 Testing embedding creation...")
    
    try:
        service = get_pinecone_service()
        test_text = "This is a test contract for rental agreement"
        
        embedding = service.create_embedding(test_text)
        
        logger.info(f"✅ Embedding created successfully! Length: {len(embedding)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Embedding creation failed: {str(e)}")
        return False


def test_store_single_vector():
    """Test storing a single vector"""
    logger.info("📤 Testing single vector storage...")
    
    try:
        service = get_pinecone_service()
        test_text = "Sample rental contract with monthly payment terms"
        metadata = {
            "document_type": "rental_contract",
            "source": "test_script",
            "test_type": "single_vector"
        }
        
        result = service.store_embedding(
            text=test_text,
            metadata=metadata
        )
        
        if result["success"]:
            logger.info(f"✅ Vector stored successfully! ID: {result['vector_id']}")
            return result["vector_id"]
        else:
            logger.error(f"❌ Vector storage failed: {result['message']}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Vector storage error: {str(e)}")
        return None


def test_store_batch_vectors():
    """Test storing multiple vectors"""
    logger.info("📦 Testing batch vector storage...")
    
    try:
        service = get_pinecone_service()
        test_texts = [
            "Commercial lease agreement with 5-year term",
            "Residential rental contract for apartment",
            "Office space lease with utilities included",
            "Warehouse rental agreement with loading dock"
        ]
        
        metadata_list = []
        for i, text in enumerate(test_texts):
            metadata_list.append({
                "document_type": "lease_agreement",
                "source": "test_script",
                "test_type": "batch_vector",
                "batch_index": i
            })
        
        result = service.store_embeddings_batch(
            texts=test_texts,
            metadata_list=metadata_list
        )
        
        if result["success"]:
            logger.info(f"✅ Batch vectors stored successfully! Count: {result['texts_count']}")
            return result["vector_ids"]
        else:
            logger.error(f"❌ Batch vector storage failed: {result['message']}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Batch vector storage error: {str(e)}")
        return None


def test_similarity_search():
    """Test similarity search"""
    logger.info("🔍 Testing similarity search...")
    
    try:
        service = get_pinecone_service()
        query_text = "Looking for rental agreement with monthly payments"
        
        result = service.search_similar(
            query_text=query_text,
            top_k=5,
            filter_metadata={"source": "test_script"}
        )
        
        if result["success"]:
            logger.info(f"✅ Search completed successfully! Found {result['total_matches']} matches")
            
            for i, match in enumerate(result["results"], 1):
                logger.info(f"  {i}. Score: {match['score']:.4f} - Text: {match['text'][:50]}...")
            
            return result["results"]
        else:
            logger.error(f"❌ Search failed: {result['message']}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}")
        return None


def test_index_stats():
    """Test getting index statistics"""
    logger.info("📊 Testing index statistics...")
    
    try:
        service = get_pinecone_service()
        result = service.get_index_stats()
        
        if result["success"]:
            stats = result["stats"]
            logger.info(f"✅ Index stats retrieved successfully!")
            logger.info(f"  - Total vectors: {stats['total_vectors']}")
            logger.info(f"  - Dimension: {stats['dimension']}")
            logger.info(f"  - Index fullness: {stats['index_fullness']:.2%}")
            return True
        else:
            logger.error(f"❌ Index stats failed: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Index stats error: {str(e)}")
        return False


def test_vector_deletion(vector_ids):
    """Test vector deletion"""
    logger.info("🗑️ Testing vector deletion...")
    
    if not vector_ids:
        logger.warning("⚠️ No vector IDs provided for deletion test")
        return True
    
    try:
        service = get_pinecone_service()
        
        # Delete first vector from the list
        test_id = vector_ids[0] if isinstance(vector_ids, list) else vector_ids
        
        result = service.delete_vector(test_id)
        
        if result["success"]:
            logger.info(f"✅ Vector deleted successfully! ID: {test_id}")
            return True
        else:
            logger.error(f"❌ Vector deletion failed: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Vector deletion error: {str(e)}")
        return False


def run_comprehensive_test():
    """Run comprehensive test suite"""
    logger.info("🚀 Starting comprehensive Pinecone integration test...")
    
    test_results = []
    
    # Test 1: Health Check
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Health Check")
    logger.info("="*50)
    test_results.append(("Health Check", test_health_check()))
    
    # Test 2: Embedding Creation
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Embedding Creation")
    logger.info("="*50)
    test_results.append(("Embedding Creation", test_embedding_creation()))
    
    # Test 3: Single Vector Storage
    logger.info("\n" + "="*50)
    logger.info("TEST 3: Single Vector Storage")
    logger.info("="*50)
    single_vector_id = test_store_single_vector()
    test_results.append(("Single Vector Storage", single_vector_id is not None))
    
    # Test 4: Batch Vector Storage
    logger.info("\n" + "="*50)
    logger.info("TEST 4: Batch Vector Storage")
    logger.info("="*50)
    batch_vector_ids = test_store_batch_vectors()
    test_results.append(("Batch Vector Storage", batch_vector_ids is not None))
    
    # Test 5: Similarity Search
    logger.info("\n" + "="*50)
    logger.info("TEST 5: Similarity Search")
    logger.info("="*50)
    search_results = test_similarity_search()
    test_results.append(("Similarity Search", search_results is not None))
    
    # Test 6: Index Statistics
    logger.info("\n" + "="*50)
    logger.info("TEST 6: Index Statistics")
    logger.info("="*50)
    test_results.append(("Index Statistics", test_index_stats()))
    
    # Test 7: Vector Deletion
    logger.info("\n" + "="*50)
    logger.info("TEST 7: Vector Deletion")
    logger.info("="*50)
    test_results.append(("Vector Deletion", test_vector_deletion(single_vector_id)))
    
    # Print Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:<25} {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("="*60)
    logger.info(f"Total Tests: {len(test_results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Pinecone integration is working correctly!")
        return True
    else:
        logger.error(f"💥 {failed} tests failed. Please check the errors above.")
        return False


def main():
    """Main function"""
    logger.info("🎯 Pinecone Integration Test Suite")
    logger.info("This will test the complete Pinecone integration")
    
    success = run_comprehensive_test()
    
    if success:
        logger.info("\n🎊 Congratulations! Pinecone integration is fully functional!")
        sys.exit(0)
    else:
        logger.error("\n💔 Some tests failed. Please review and fix the issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()