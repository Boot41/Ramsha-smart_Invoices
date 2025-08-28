from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from services.llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/llm", tags=["LLM Services"])

# Pydantic models for requests
class EmbeddingRequest(BaseModel):
    text: str

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Health check endpoint for LLM services
    """
    try:
        logger.info("🏥 LLM Health check requested")
        
        llm_service = get_llm_service()
        result = llm_service.test_embedding_service()
        
        return {
            "status": "success",
            "message": "🟢 LLM Service Health Check Complete!",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.post("/embedding", response_model=Dict[str, Any])
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate embedding for a single text
    
    Args:
        request: EmbeddingRequest containing text to embed
        
    Returns:
        Dictionary containing embedding results
    """
    try:
        logger.info(f"📝 Embedding request received for text: '{request.text[:30]}...'")
        
        llm_service = get_llm_service()
        result = llm_service.generate_embedding(request.text)
        
        return {
            "status": "success",
            "message": "✅ Embedding generated successfully!",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {str(e)}"
        )


@router.post("/embedding/batch", response_model=Dict[str, Any])
async def generate_batch_embeddings(request: BatchEmbeddingRequest):
    """
    Generate embeddings for multiple texts
    
    Args:
        request: BatchEmbeddingRequest containing list of texts to embed
        
    Returns:
        Dictionary containing batch embedding results
    """
    try:
        logger.info(f"📦 Batch embedding request received for {len(request.texts)} texts")
        
        if len(request.texts) > 100:  # Reasonable limit
            raise HTTPException(
                status_code=400,
                detail="Too many texts. Maximum 100 texts per batch request."
            )
        
        llm_service = get_llm_service()
        result = llm_service.generate_batch_embeddings(request.texts)
        
        return {
            "status": "success",
            "message": f"✅ Batch embeddings generated for {len(request.texts)} texts!",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Batch embedding generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch embedding generation failed: {str(e)}"
        )


@router.get("/test", response_model=Dict[str, Any])
async def test_llm_service():
    """
    Simple test endpoint to verify LLM service is running
    """
    try:
        logger.info("🧪 LLM Service test requested")
        
        # Test with a simple message
        test_text = "Hello, this is a test message for the Vertex AI embedding service!"
        
        llm_service = get_llm_service()
        result = llm_service.generate_embedding(test_text)
        
        return {
            "status": "success",
            "message": "🎉 LLM Service test completed successfully!",
            "test_text": test_text,
            "embedding_result": result,
            "service_info": {
                "model": "text-embedding-004",
                "provider": "Google Vertex AI",
                "status": "🟢 Running"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ LLM Service test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM Service test failed: {str(e)}"
        )