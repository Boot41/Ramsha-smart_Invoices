from google.cloud import aiplatform as vertexai
from dotenv import load_dotenv
from pathlib import Path
from utils.config import REGIONS
import random
import os
from langchain_google_vertexai import VertexAIEmbeddings
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class EmbeddingService:
    """Vertex AI Embedding Service for text embeddings"""
    
    def __init__(self):
        self.project_id = os.getenv("PROJECT_ID")
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.location = self._get_random_region()
        
        if not self.project_id:
            raise ValueError("PROJECT_ID must be set in environment variables")
            
        logger.info(f"Initializing Vertex AI with project: {self.project_id}, location: {self.location}")
        
        try:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            
            # Initialize embedding model
            self.embedding_model = VertexAIEmbeddings(
                model_name="text-embedding-004",
                project=self.project_id,
                location=self.location
            )
            
            logger.info("✅ Vertex AI Embedding Service initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vertex AI: {str(e)}")
            raise
    
    def _get_random_region(self) -> str:
        """Get a random region for load balancing"""
        return REGIONS[random.randint(0, len(REGIONS) - 1)]
    
    def get_embedding(self, text: str) -> Dict[str, Any]:
        """
        Get embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Dictionary containing embedding and metadata
        """
        try:
            logger.info(f"🚀 Getting embedding for text: '{text[:50]}...'")
            
            # Get embedding
            embedding = self.embedding_model.embed_query(text)
            
            result = {
                "success": True,
                "message": "✅ Embedding generated successfully!",
                "text": text,
                "embedding_length": len(embedding),
                "embedding_preview": embedding[:5],  # First 5 dimensions
                "model": "text-embedding-004",
                "location": self.location,
                "project_id": self.project_id
            }
            
            logger.info(f"✅ Embedding completed. Vector length: {len(embedding)}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error getting embedding: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "text": text,
                "error": str(e)
            }
    
    def get_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """
        Get embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Dictionary containing embeddings and metadata
        """
        try:
            logger.info(f"🚀 Getting embeddings for {len(texts)} texts")
            
            # Get embeddings
            embeddings = self.embedding_model.embed_documents(texts)
            
            result = {
                "success": True,
                "message": f"✅ Generated embeddings for {len(texts)} texts!",
                "texts": texts,
                "embeddings_count": len(embeddings),
                "embedding_length": len(embeddings[0]) if embeddings else 0,
                "model": "text-embedding-004",
                "location": self.location,
                "project_id": self.project_id
            }
            
            logger.info(f"✅ Batch embedding completed. Generated {len(embeddings)} vectors")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error getting batch embeddings: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "texts": texts,
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check for the embedding service
        
        Returns:
            Dictionary containing service status
        """
        try:
            # Test with a simple text
            test_text = "Health check test"
            result = self.get_embedding(test_text)
            
            if result["success"]:
                return {
                    "status": "healthy",
                    "message": "🟢 Vertex AI Embedding Service is running successfully!",
                    "project_id": self.project_id,
                    "location": self.location,
                    "model": "text-embedding-004",
                    "test_result": result
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "🔴 Embedding service test failed",
                    "error": result.get("error")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"🔴 Health check failed: {str(e)}",
                "error": str(e)
            }


# Factory function for backward compatibility
def get_embedding_model():
    """Get embedding model instance"""
    return EmbeddingService()


# Global service instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
