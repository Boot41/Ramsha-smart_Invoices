import pdfplumber
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
        self.chunk_size = 100
        self.chunk_overlap = 20
        logger.info("🚀 Contract Processor initialized")
    
    def extract_text_from_pdf(self, pdf_file: bytes) -> str:
        """
        Extract text from PDF file using pdfplumber for better layout preservation
        
        Args:
            pdf_file: PDF file as bytes
            
        Returns:
            Extracted text content with improved table and layout handling
        """
        try:
            text = ""
            
            with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"📄 Processing page {page_num + 1}")
                    
                    # Extract regular text with layout preservation
                    page_text = page.extract_text()
                    if page_text:
                        text += f"--- Page {page_num + 1} ---\n"
                        text += page_text + "\n\n"
                    
                    # Extract tables separately to preserve structure
                    tables = page.extract_tables()
                    if tables:
                        text += f"--- Tables from Page {page_num + 1} ---\n"
                        for table_num, table in enumerate(tables):
                            text += f"Table {table_num + 1}:\n"
                            for row in table:
                                if row and any(cell for cell in row if cell):  # Skip empty rows
                                    # Clean and join cells, handling None values
                                    clean_row = [str(cell).strip() if cell else "" for cell in row]
                                    text += " | ".join(clean_row) + "\n"
                            text += "\n"
                    
                    # Extract text from specific regions (useful for amounts in specific locations)
                    # This helps capture text that might be in specific coordinate areas
                    bbox_text = page.within_bbox((0, 0, page.width, page.height)).extract_text()
                    if bbox_text and bbox_text not in page_text:
                        text += f"--- Additional text from Page {page_num + 1} ---\n"
                        text += bbox_text + "\n\n"
            
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF")
            
            # Enhanced text cleaning for better LLM processing
            text = self._clean_extracted_text(text)
            
            logger.info(f"✅ Extracted text from PDF: {len(text)} characters using pdfplumber")
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ Failed to extract text from PDF: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from PDF: {str(e)}"
            )
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean extracted text for better LLM processing
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text with better formatting
        """
        # Remove excessive whitespace while preserving structure
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Fix common OCR/extraction issues with currency symbols
        text = re.sub(r'[^\w\s\.\,\$\£\€\¥\%\-\:\;\(\)\|\n]', ' ', text)
        
        # Normalize currency patterns for better detection
        text = re.sub(r'\$\s*(\d)', r'$\1', text)  # Fix "$  100" -> "$100"
        text = re.sub(r'(\d)\s*\$', r'\1$', text)  # Fix "100  $" -> "100$"
        
        # Improve number formatting
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # Fix split numbers "1 000" -> "1000"
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        print(text)
        
        return text
    
    def process_text_content(self, text_content: str, user_id: str, contract_name: str) -> Dict[str, Any]:
        """
        Process text content directly (for evaluation purposes)
        
        Args:
            text_content: Raw contract text
            user_id: User ID
            contract_name: Name of the contract
            
        Returns:
            Processing result dictionary
        """
        try:
            logger.info(f"🚀 Starting text content processing for user {user_id}")
            
            # Clean the text
            cleaned_text = self._clean_extracted_text(text_content)
            
            # Generate chunks
            chunks = self.chunk_text(cleaned_text)
            logger.info(f"📄 Created {len(chunks)} text chunks")
            
            # Generate embeddings
            embeddings = self.generate_embeddings(chunks)
            logger.info(f"🔢 Generated {len(embeddings)} embeddings")
            
            # Store in Pinecone
            vector_ids = self.store_in_pinecone(user_id, contract_name, chunks, embeddings)
            storage_result = {
                "status": "success",
                "message": f"Stored {len(vector_ids)} vectors in Pinecone",
                "vector_ids": vector_ids[:5]
            }
            logger.info(f"💾 Pinecone storage: {storage_result['message']}")
            
            return {
                "status": "success",
                "message": f"Text content processed successfully for {contract_name}",
                "text_length": len(cleaned_text),
                "chunks_count": len(chunks),
                "embeddings_count": len(embeddings),
                "pinecone_storage": storage_result
            }
            
        except Exception as e:
            logger.error(f"❌ Text content processing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Text content processing failed: {str(e)}"
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
            embeddings = self.embedding_service.embed_documents(chunks)
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
            print(f"Extracted text length: {len(text)}")
            
            # Step 2: Chunk text
            chunks = self.chunk_text(text)
            print(f"Number of chunks created: {len(chunks)}")
            
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
