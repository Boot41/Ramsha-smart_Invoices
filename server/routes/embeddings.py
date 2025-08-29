from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.pinecone_service import get_pinecone_service, PineconeService
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


# Request/Response Models
class EmbeddingRequest(BaseModel):
    text: str

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]
    metadata_list: Optional[List[Dict[str, Any]]] = None
    vector_ids: Optional[List[str]] = None

class SearchRequest(BaseModel):
    query_text: str
    top_k: int = 10
    filter_metadata: Optional[Dict[str, Any]] = None

class DeleteRequest(BaseModel):
    vector_id: str


@router.post("/create")
async def create_embedding(
    request: EmbeddingRequest,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Create embedding for a single text"""
    try:
        logger.info(f"Creating embedding for text: {request.text[:50]}...")
        
        embedding = pinecone_service.create_embedding(request.text)
        
        return {
            "success": True,
            "message": "Embedding created successfully",
            "text": request.text,
            "embedding_length": len(embedding),
            "embedding_preview": embedding[:5]  # First 5 dimensions for preview
        }
        
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-batch")
async def create_batch_embeddings(
    request: BatchEmbeddingRequest,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Create embeddings for multiple texts"""
    try:
        logger.info(f"Creating batch embeddings for {len(request.texts)} texts")
        
        embeddings = pinecone_service.create_embeddings_batch(request.texts)
        
        return {
            "success": True,
            "message": f"Created embeddings for {len(request.texts)} texts",
            "texts_count": len(request.texts),
            "embeddings_count": len(embeddings),
            "embedding_length": len(embeddings[0]) if embeddings else 0
        }
        
    except Exception as e:
        logger.error(f"Error creating batch embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/store")
async def store_embedding(
    request: EmbeddingRequest,
    metadata: Optional[Dict[str, Any]] = None,
    vector_id: Optional[str] = None,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Create and store a single embedding in Pinecone"""
    try:
        logger.info(f"Storing embedding for text: {request.text[:50]}...")
        
        result = pinecone_service.store_embedding(
            text=request.text,
            metadata=metadata,
            vector_id=vector_id
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/store-batch")
async def store_batch_embeddings(
    request: BatchEmbeddingRequest,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Create and store multiple embeddings in Pinecone"""
    try:
        logger.info(f"Storing batch embeddings for {len(request.texts)} texts")
        
        result = pinecone_service.store_embeddings_batch(
            texts=request.texts,
            metadata_list=request.metadata_list,
            vector_ids=request.vector_ids
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing batch embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_similar_vectors(
    request: SearchRequest,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Search for similar vectors using text query"""
    try:
        logger.info(f"Searching for similar vectors: {request.query_text[:50]}...")
        
        result = pinecone_service.search_similar(
            query_text=request.query_text,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching vectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_vector(
    request: DeleteRequest,
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Delete a vector from Pinecone"""
    try:
        logger.info(f"Deleting vector: {request.vector_id}")
        
        result = pinecone_service.delete_vector(request.vector_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_index_statistics(
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Get Pinecone index statistics"""
    try:
        logger.info("Getting index statistics")
        
        result = pinecone_service.get_index_stats()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting index stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    pinecone_service: PineconeService = Depends(get_pinecone_service)
):
    """Perform health check on Pinecone service"""
    try:
        logger.info("Performing health check")
        
        result = pinecone_service.health_check()
        
        if result["status"] == "healthy":
            return result
        else:
            raise HTTPException(status_code=503, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))