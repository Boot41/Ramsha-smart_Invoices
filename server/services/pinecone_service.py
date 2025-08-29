import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from models.llm.embedding import EmbeddingService
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class PineconeService:
    """Service for managing vector embeddings in Pinecone"""
    
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "contracts")
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        logger.info(f"🔗 Initializing Pinecone service with index: {self.index_name}")
        
        # Initialize Pinecone client
        self.client = Pinecone(api_key=self.api_key)
        
        # Initialize embedding service
        self.embedding_service = EmbeddingService()
        
        # Get or create index
        self.index = self._get_or_create_index()
        
        logger.info("✅ Pinecone service initialized successfully!")
    
    def _get_or_create_index(self):
        """Get existing index or create new one if it doesn't exist"""
        try:
            # Check if index exists
            existing_indexes = self.client.list_indexes()
            index_names = [idx.name for idx in existing_indexes.indexes]
            
            if self.index_name in index_names:
                logger.info(f"✅ Using existing index: {self.index_name}")
                return self.client.Index(self.index_name)
            
            logger.info(f"📝 Creating new index: {self.index_name}")
            
            # Create index with specifications for text embeddings
            self.client.create_index(
                name=self.index_name,
                dimension=768,  # Google Vertex AI text-embedding-004 dimension
                metric='cosine',  # Cosine similarity for text embeddings
                spec=ServerlessSpec(
                    cloud='aws',  # Use AWS serverless
                    region='us-east-1'  # Choose appropriate region
                )
            )
            
            # Wait for index to be ready
            logger.info("⏳ Waiting for index to be ready...")
            time.sleep(5)
            
            logger.info(f"✅ Successfully created index: {self.index_name}")
            return self.client.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"❌ Failed to get or create index: {str(e)}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for a single text using Vertex AI
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            logger.info(f"🚀 Creating embedding for text: '{text[:50]}...'")
            
            # Use the existing embedding service
            embedding = self.embedding_service.embedding_model.embed_query(text)
            
            logger.info(f"✅ Embedding created. Vector length: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error creating embedding: {str(e)}")
            raise
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"🚀 Creating embeddings for {len(texts)} texts")
            
            # Use the existing embedding service for batch processing
            embeddings = self.embedding_service.embedding_model.embed_documents(texts)
            
            logger.info(f"✅ Batch embeddings created. Generated {len(embeddings)} vectors")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Error creating batch embeddings: {str(e)}")
            raise
    
    def store_embedding(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None,
        vector_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create and store a single embedding in Pinecone
        
        Args:
            text: Text to embed and store
            metadata: Optional metadata to store with the vector
            vector_id: Optional custom ID for the vector
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Generate embedding
            embedding = self.create_embedding(text)
            
            # Generate ID if not provided
            if not vector_id:
                vector_id = str(uuid.uuid4())
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "text": text,
                "created_at": time.time(),
                "text_length": len(text)
            })
            
            # Store in Pinecone
            logger.info(f"📤 Storing vector with ID: {vector_id}")
            
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)]
            )
            
            result = {
                "success": True,
                "message": "✅ Vector stored successfully!",
                "vector_id": vector_id,
                "text": text,
                "metadata": metadata,
                "embedding_length": len(embedding)
            }
            
            logger.info(f"✅ Vector stored successfully with ID: {vector_id}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error storing embedding: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "text": text,
                "error": str(e)
            }
    
    def store_embeddings_batch(
        self, 
        texts: List[str], 
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        vector_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create and store multiple embeddings in Pinecone
        
        Args:
            texts: List of texts to embed and store
            metadata_list: Optional list of metadata for each text
            vector_ids: Optional list of custom IDs for the vectors
            
        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(f"🚀 Processing batch of {len(texts)} texts")
            
            # Generate embeddings
            embeddings = self.create_embeddings_batch(texts)
            
            # Prepare vectors for upsert
            vectors = []
            stored_ids = []
            
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                # Generate ID if not provided
                vector_id = vector_ids[i] if vector_ids and i < len(vector_ids) else str(uuid.uuid4())
                stored_ids.append(vector_id)
                
                # Prepare metadata
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                metadata.update({
                    "text": text,
                    "created_at": time.time(),
                    "text_length": len(text)
                })
                
                vectors.append((vector_id, embedding, metadata))
            
            # Store in Pinecone
            logger.info(f"📤 Storing {len(vectors)} vectors in Pinecone")
            
            self.index.upsert(vectors=vectors)
            
            result = {
                "success": True,
                "message": f"✅ Stored {len(vectors)} vectors successfully!",
                "vector_ids": stored_ids,
                "texts_count": len(texts),
                "embeddings_count": len(embeddings)
            }
            
            logger.info(f"✅ Batch storage completed. Stored {len(vectors)} vectors")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error storing batch embeddings: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "texts_count": len(texts),
                "error": str(e)
            }
    
    def search_similar(
        self, 
        query_text: str, 
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar vectors using text query
        
        Args:
            query_text: Text to search for
            top_k: Number of similar vectors to return
            filter_metadata: Optional metadata filters
            
        Returns:
            Dictionary with search results
        """
        try:
            logger.info(f"🔍 Searching for similar vectors to: '{query_text[:50]}...'")
            
            # Create embedding for query
            query_embedding = self.create_embedding(query_text)
            
            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_metadata,
                include_metadata=True
            )
            
            # Format results
            results = []
            for match in search_results.matches:
                results.append({
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": match.metadata,
                    "text": match.metadata.get("text", "") if match.metadata else ""
                })
            
            result = {
                "success": True,
                "message": f"✅ Found {len(results)} similar vectors",
                "query_text": query_text,
                "results": results,
                "total_matches": len(results)
            }
            
            logger.info(f"✅ Search completed. Found {len(results)} matches")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error searching vectors: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "query_text": query_text,
                "error": str(e)
            }
    
    def delete_vector(self, vector_id: str) -> Dict[str, Any]:
        """
        Delete a vector from Pinecone
        
        Args:
            vector_id: ID of vector to delete
            
        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(f"🗑️ Deleting vector with ID: {vector_id}")
            
            self.index.delete(ids=[vector_id])
            
            result = {
                "success": True,
                "message": f"✅ Vector {vector_id} deleted successfully",
                "vector_id": vector_id
            }
            
            logger.info(f"✅ Vector deleted: {vector_id}")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error deleting vector: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "vector_id": vector_id,
                "error": str(e)
            }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index
        
        Returns:
            Dictionary with index statistics
        """
        try:
            logger.info("📊 Getting index statistics")
            
            stats = self.index.describe_index_stats()
            
            result = {
                "success": True,
                "message": "✅ Index stats retrieved successfully",
                "index_name": self.index_name,
                "stats": {
                    "total_vectors": stats.total_vector_count,
                    "dimension": stats.dimension,
                    "index_fullness": stats.index_fullness,
                    "namespaces": dict(stats.namespaces) if stats.namespaces else {}
                }
            }
            
            logger.info(f"✅ Index stats: {stats.total_vector_count} vectors")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error getting index stats: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Pinecone service
        
        Returns:
            Dictionary with health status
        """
        try:
            logger.info("🏥 Performing health check")
            
            # Test embedding creation
            test_text = "Health check test for Pinecone service"
            embedding = self.create_embedding(test_text)
            
            # Test index access
            stats = self.index.describe_index_stats()
            
            result = {
                "status": "healthy",
                "message": "🟢 Pinecone service is running successfully!",
                "index_name": self.index_name,
                "total_vectors": stats.total_vector_count,
                "embedding_dimension": len(embedding),
                "embedding_service_status": "working"
            }
            
            logger.info("✅ Health check passed")
            return result
            
        except Exception as e:
            error_msg = f"🔴 Health check failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "unhealthy",
                "message": error_msg,
                "error": str(e)
            }


# Global service instance
_pinecone_service = None

def get_pinecone_service() -> PineconeService:
    """Get singleton Pinecone service instance"""
    global _pinecone_service
    if _pinecone_service is None:
        _pinecone_service = PineconeService()
    return _pinecone_service