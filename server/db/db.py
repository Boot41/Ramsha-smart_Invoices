import os
from pinecone import Pinecone
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Global Pinecone client
_pinecone_client = None


def get_pinecone_client():
    """Get Pinecone client instance"""
    global _pinecone_client
    
    if _pinecone_client is None:
        try:
            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("PINECONE_API_KEY environment variable is required")
            
            # Initialize Pinecone
            pc = Pinecone(api_key=api_key)
            
            # Get the index
            index_name = os.getenv("PINECONE_INDEX_NAME", "contracts")
            _pinecone_client = pc.Index(index_name)
            
            logger.info(f"✅ Pinecone client initialized with index: {index_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Pinecone client: {str(e)}")
            raise
    
    return _pinecone_client


def get_async_database():
    """Placeholder for async database connection"""
    # This can be implemented later for other database operations
    return None