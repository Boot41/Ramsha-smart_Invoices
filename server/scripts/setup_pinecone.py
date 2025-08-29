#!/usr/bin/env python3
"""
Pinecone Index Setup Script

This script creates the required Pinecone index for the Smart Invoice Scheduler
if it doesn't already exist.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Add parent directory to path to import from project
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables"""
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "contracts")
    
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is required")
    
    return api_key, index_name

def setup_pinecone_index():
    """Create Pinecone index if it doesn't exist"""
    try:
        api_key, index_name = load_environment()
        
        logger.info(f"🔗 Connecting to Pinecone with index: {index_name}")
        
        # Initialize Pinecone client
        pc = Pinecone(api_key=api_key)
        
        # Check if index exists
        existing_indexes = pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes.indexes]
        
        if index_name in index_names:
            logger.info(f"✅ Index '{index_name}' already exists")
            
            # Get index stats
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            logger.info(f"📊 Index stats: {stats}")
            
            return True
        
        logger.info(f"📝 Creating new index: {index_name}")
        
        # Create index with specifications for text embeddings
        pc.create_index(
            name=index_name,
            dimension=768,  # Google Vertex AI text-embedding-004 dimension
            metric='cosine',  # Cosine similarity for text embeddings
            spec=ServerlessSpec(
                cloud='aws',  # Use AWS serverless
                region='us-east-1'  # Choose appropriate region
            )
        )
        
        logger.info(f"✅ Successfully created index: {index_name}")
        
        # Verify index was created
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        logger.info(f"📊 New index stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Pinecone index: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting Pinecone index setup...")
    
    success = setup_pinecone_index()
    
    if success:
        logger.info("🎉 Pinecone setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Pinecone setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()