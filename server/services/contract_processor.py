from pypdf import PdfReader
from typing import List, Dict, Any
from fastapi import HTTPException
import logging
import io
from models.llm.embedding import get_embedding_service
from db.db import get_pinecone_client
import uuid
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ContractProcessor:
    """Service for processing contract PDFs into text chunks and embeddings"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.chunk_size = 1000
        self.chunk_overlap = 200
        logger.info("🚀 Contract Processor initialized")
    
    def extract_text_from_pdf(self, pdf_file: bytes) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_file: PDF file as bytes
            
        Returns:
            Extracted text content
        """
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_file))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF")
                
            logger.info(f"✅ Extracted text from PDF: {len(text)} characters")
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ Failed to extract text from PDF: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from PDF: {str(e)}"
            )
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        try:
            # Clean up text
            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
            text = text.strip()
            
            chunks = []
            words = text.split()
            
            for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
                chunk_words = words[i:i + self.chunk_size]
                chunk = ' '.join(chunk_words)
                
                if chunk.strip():
                    chunks.append(chunk)
            
            logger.info(f"✅ Created {len(chunks)} chunks from text")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Failed to chunk text: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to chunk text: {str(e)}"
            )
    
    def generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of embeddings
        """
        try:
            embeddings = []
            
            for chunk in chunks:
                # Use the embedding service directly
                embedding = self.embedding_service.embedding_model.embed_query(chunk)
                embeddings.append(embedding)
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings: {str(e)}"
            )
    
    def store_in_pinecone(self, 
                         user_id: str,
                         contract_name: str,
                         chunks: List[str], 
                         embeddings: List[List[float]]) -> List[str]:
        """
        Store embeddings and chunks in Pinecone
        
        Args:
            user_id: User ID
            contract_name: Name of the contract file
            chunks: Text chunks
            embeddings: Corresponding embeddings
            
        Returns:
            List of stored vector IDs
        """
        try:
            index = get_pinecone_client()
            vector_ids = []
            
            # Prepare vectors for upsert
            vectors_to_upsert = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"contract_{user_id}_{uuid.uuid4().hex}_{i}"
                vector_ids.append(vector_id)
                
                metadata = {
                    "user_id": user_id,
                    "contract_name": contract_name,
                    "text": chunk,
                    "chunk_index": i,
                    "document_type": "contract",
                    "created_at": datetime.now().isoformat()
                }
                
                vectors_to_upsert.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert vectors in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                index.upsert(vectors=batch)
            
            logger.info(f"✅ Stored {len(vector_ids)} vectors in Pinecone")
            return vector_ids
            
        except Exception as e:
            logger.error(f"❌ Failed to store vectors in Pinecone: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store vectors in Pinecone: {str(e)}"
            )
    
    def process_contract(self, 
                        pdf_file: bytes, 
                        user_id: str, 
                        contract_name: str) -> Dict[str, Any]:
        """
        Complete contract processing pipeline
        
        Args:
            pdf_file: PDF file as bytes
            user_id: User ID
            contract_name: Name of the contract file
            
        Returns:
            Processing results
        """
        try:
            logger.info(f"🚀 Starting contract processing for user {user_id}")
            
            # Step 1: Extract text
            text = self.extract_text_from_pdf(pdf_file)
            
            # Step 2: Chunk text
            chunks = self.chunk_text(text)
            
            # Step 3: Generate embeddings
            embeddings = self.generate_embeddings(chunks)
            
            # Step 4: Store in Pinecone
            vector_ids = self.store_in_pinecone(user_id, contract_name, chunks, embeddings)
            
            result = {
                "status": "success",
                "message": "✅ Contract processed successfully",
                "contract_name": contract_name,
                "user_id": user_id,
                "total_chunks": len(chunks),
                "total_embeddings": len(embeddings),
                "vector_ids": vector_ids[:5],  # Return first 5 IDs for reference
                "text_preview": text[:500] + "..." if len(text) > 500 else text,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Contract processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Contract processing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Contract processing failed: {str(e)}"
            )


# Global service instance
_contract_processor = None

def get_contract_processor() -> ContractProcessor:
    """Get singleton contract processor instance"""
    global _contract_processor
    if _contract_processor is None:
        _contract_processor = ContractProcessor()
    return _contract_processor