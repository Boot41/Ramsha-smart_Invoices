from models.llm.embedding import get_embedding_service
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Service layer for LLM operations"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        logger.info("🚀 LLM Service initialized")
    
    def test_embedding_service(self) -> Dict[str, Any]:
        """
        Test the embedding service to ensure it's working
        
        Returns:
            Dictionary with test results
        """
        try:
            logger.info("🔍 Testing embedding service...")
            
            # Perform health check
            health_result = self.embedding_service.health_check()
            
            return {
                "service": "LLM Service",
                "status": "✅ Service is running successfully!",
                "timestamp": "2024-01-01T00:00:00Z",  # You can add real timestamp
                "embedding_test": health_result
            }
            
        except Exception as e:
            logger.error(f"❌ LLM Service test failed: {str(e)}")
            return {
                "service": "LLM Service", 
                "status": "❌ Service test failed",
                "error": str(e)
            }
    
    def generate_embedding(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a given text
        
        Args:
            text: Text to embed
            
        Returns:
            Dictionary containing embedding results
        """
        try:
            logger.info(f"📝 Processing embedding request for text: '{text[:30]}...'")
            
            result = self.embedding_service.get_embedding(text)
            
            return {
                "service": "LLM Service - Embedding",
                "request_status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {str(e)}")
            return {
                "service": "LLM Service - Embedding",
                "request_status": "failed",
                "error": str(e)
            }
    
    def generate_batch_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Dictionary containing batch embedding results
        """
        try:
            logger.info(f"📝 Processing batch embedding request for {len(texts)} texts")
            
            result = self.embedding_service.get_embeddings(texts)
            
            return {
                "service": "LLM Service - Batch Embedding",
                "request_status": "completed", 
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Batch embedding generation failed: {str(e)}")
            return {
                "service": "LLM Service - Batch Embedding",
                "request_status": "failed",
                "error": str(e)
            }


# Global service instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service