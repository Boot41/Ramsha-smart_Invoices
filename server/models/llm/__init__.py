from .embedding import get_embedding_service, EmbeddingService
from .base import get_model

def get_embedding_model():
    """Get embedding model for backward compatibility"""
    return get_embedding_service()

def get_chat_model():
    """Get chat model for backward compatibility"""
    return get_model()