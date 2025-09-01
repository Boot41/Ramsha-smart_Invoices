import os
import logging
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from vertexai.preview.language_models import TextEmbeddingModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class EmbeddingService:
    """Vertex AI Embedding Service for text embeddings"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "text-embedding-004"):
        if not hasattr(self, 'initialized'):
            self.project_id = os.getenv("PROJECT_ID")
            if not self.project_id:
                raise ValueError("PROJECT_ID must be set in environment variables")

            self.model_name = model_name
            try:
                self.model = TextEmbeddingModel.from_pretrained(self.model_name)
                self.initialized = True
                logger.info(f"✅ EmbeddingService initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize EmbeddingService: {str(e)}")
                raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts."""
        try:
            embeddings = self.model.get_embeddings(texts)
            return [embedding.values for embedding in embeddings]
        except Exception as e:
            logger.error(f"❌ Failed to embed documents: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        return self.embed_documents([text])[0]

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
            embedding = self.embed_query(text)

            result = {
                "success": True,
                "message": "✅ Embedding generated successfully!",
                "text": text,
                "embedding_length": len(embedding),
                "embedding_preview": embedding[:5],  # First 5 dimensions
                "model": self.model_name,
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
            embeddings = self.embed_documents(texts)

            result = {
                "success": True,
                "message": f"✅ Generated embeddings for {len(texts)} texts!",
                "texts": texts,
                "embeddings_count": len(embeddings),
                "embedding_length": len(embeddings[0]) if embeddings else 0,
                "model": self.model_name,
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
                    "model": self.model_name,
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
