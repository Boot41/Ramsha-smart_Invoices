from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime, date
from decimal import Decimal

from models.database_models import Contract, ContractParty, ExtractedInvoiceData, GeneratedInvoice, ContractType, InvoiceFrequency
from db.postgresdb import get_async_db_session

logger = logging.getLogger(__name__)


class ContractDatabaseService:
    """Service for contract database operations"""
    
    def __init__(self):
        """Initialize the contract database service"""
        logger.info("✅ Contract Database Service initialized")
    
    async def save_contract(
        self,
        user_id: str,
        original_filename: str,
        storage_path: str,
        file_size: int,
        content_type: str = "application/pdf",
        **kwargs
    ) -> Contract:
        """
        Save contract information to database
        
        Args:
            user_id: User ID who uploaded the contract
            original_filename: Original filename
            storage_path: GCP Storage path
            file_size: File size in bytes
            content_type: MIME type
            **kwargs: Additional contract metadata
            
        Returns:
            Created Contract object
        """
        try:
            logger.info(f"💾 Saving contract to database: {original_filename}")
            
            async with get_async_db_session() as session:
                contract = Contract(
                    user_id=user_id,
                    original_filename=original_filename,
                    storage_path=storage_path,
                    file_size=file_size,
                    content_type=content_type,
                    # Optional processing metadata
                    total_chunks=kwargs.get('total_chunks'),
                    total_embeddings=kwargs.get('total_embeddings'),
                    pinecone_vector_ids=kwargs.get('vector_ids'),
                    text_preview=kwargs.get('text_preview'),
                    processing_metadata=kwargs.get('processing_metadata'),
                    is_processed=kwargs.get('is_processed', False)
                )
                
                session.add(contract)
                await session.commit()
                await session.refresh(contract)
                
                logger.info(f"✅ Contract saved with ID: {contract.id}")
                return contract
                
        except Exception as e:
            logger.error(f"❌ Failed to save contract: {str(e)}")
            raise
    
    async def update_contract_processing_status(
        self,
        storage_path: str,
        is_processed: bool = True,
        total_chunks: Optional[int] = None,
        total_embeddings: Optional[int] = None,
        vector_ids: Optional[List[str]] = None,
        text_preview: Optional[str] = None
    ) -> Optional[Contract]:
        """
        Update contract processing status
        
        Args:
            storage_path: Contract storage path
            is_processed: Processing completion status
            total_chunks: Number of text chunks
            total_embeddings: Number of embeddings
            vector_ids: List of Pinecone vector IDs
            text_preview: Preview of extracted text
            
        Returns:
            Updated Contract object or None
        """
        try:
            async with get_async_db_session() as session:
                stmt = select(Contract).where(Contract.storage_path == storage_path)
                result = await session.execute(stmt)
                contract = result.scalar_one_or_none()
                
                if not contract:
                    logger.warning(f"Contract not found with storage path: {storage_path}")
                    return None
                
                # Update processing status
                contract.is_processed = is_processed
                if is_processed:
                    contract.processing_completed_at = datetime.utcnow()
                
                if total_chunks is not None:
                    contract.total_chunks = total_chunks
                if total_embeddings is not None:
                    contract.total_embeddings = total_embeddings
                if vector_ids is not None:
                    contract.pinecone_vector_ids = vector_ids
                if text_preview is not None:
                    contract.text_preview = text_preview
                
                await session.commit()
                await session.refresh(contract)
                
                logger.info(f"✅ Updated contract processing status: {contract.id}")
                return contract
                
        except Exception as e:
            logger.error(f"❌ Failed to update contract status: {str(e)}")
            raise
    
    async def save_extracted_invoice_data(
        self,
        contract_id: str,
        user_id: str,
        invoice_data: Dict[str, Any],
        confidence_score: Optional[float] = None,
        extraction_query: Optional[str] = None,
        raw_ai_response: Optional[str] = None
    ) -> ExtractedInvoiceData:
        """
        Save extracted invoice data from AI/RAG processing
        
        Args:
            contract_id: Contract ID
            user_id: User ID
            invoice_data: Extracted invoice data dictionary
            confidence_score: AI confidence score (0.0 to 1.0)
            extraction_query: Query used for extraction
            raw_ai_response: Raw AI response
            
        Returns:
            Created ExtractedInvoiceData object
        """
        try:
            logger.info(f"💾 Saving extracted invoice data for contract: {contract_id}")
            
            async with get_async_db_session() as session:
                # Parse invoice frequency
                invoice_frequency = None
                if invoice_data.get('invoice_frequency'):
                    try:
                        invoice_frequency = InvoiceFrequency(invoice_data['invoice_frequency'])
                    except ValueError:
                        logger.warning(f"Invalid invoice frequency: {invoice_data.get('invoice_frequency')}")
                
                # Parse dates
                first_invoice_date = None
                if invoice_data.get('first_invoice_date'):
                    try:
                        if isinstance(invoice_data['first_invoice_date'], str):
                            first_invoice_date = datetime.strptime(invoice_data['first_invoice_date'], '%Y-%m-%d').date()
                        elif isinstance(invoice_data['first_invoice_date'], date):
                            first_invoice_date = invoice_data['first_invoice_date']
                    except ValueError:
                        logger.warning(f"Invalid first_invoice_date: {invoice_data.get('first_invoice_date')}")
                
                next_invoice_date = None
                if invoice_data.get('next_invoice_date'):
                    try:
                        if isinstance(invoice_data['next_invoice_date'], str):
                            next_invoice_date = datetime.strptime(invoice_data['next_invoice_date'], '%Y-%m-%d').date()
                        elif isinstance(invoice_data['next_invoice_date'], date):
                            next_invoice_date = invoice_data['next_invoice_date']
                    except ValueError:
                        logger.warning(f"Invalid next_invoice_date: {invoice_data.get('next_invoice_date')}")
                
                # Parse payment amount
                payment_amount = None
                if invoice_data.get('payment_terms', {}).get('amount'):
                    try:
                        payment_amount = Decimal(str(invoice_data['payment_terms']['amount']))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid payment amount: {invoice_data.get('payment_terms', {}).get('amount')}")
                
                # Create extracted invoice data
                extracted_data = ExtractedInvoiceData(
                    contract_id=contract_id,
                    user_id=user_id,
                    invoice_frequency=invoice_frequency,
                    first_invoice_date=first_invoice_date,
                    next_invoice_date=next_invoice_date,
                    payment_amount=payment_amount,
                    currency=invoice_data.get('payment_terms', {}).get('currency', 'USD'),
                    payment_due_days=invoice_data.get('payment_terms', {}).get('due_days', 30),
                    late_fee=invoice_data.get('payment_terms', {}).get('late_fee'),
                    discount_terms=invoice_data.get('payment_terms', {}).get('discount_terms'),
                    services=invoice_data.get('services', []),
                    special_terms=invoice_data.get('special_terms'),
                    notes=invoice_data.get('notes'),
                    confidence_score=confidence_score,
                    extraction_query=extraction_query,
                    raw_ai_response=raw_ai_response
                )
                
                # Handle existing data (update if exists, create if new)
                stmt = select(ExtractedInvoiceData).where(ExtractedInvoiceData.contract_id == contract_id)
                result = await session.execute(stmt)
                existing_data = result.scalar_one_or_none()
                
                if existing_data:
                    # Update existing data
                    for key, value in extracted_data.__dict__.items():
                        if not key.startswith('_') and value is not None:
                            setattr(existing_data, key, value)
                    extracted_data = existing_data
                else:
                    # Create new data
                    session.add(extracted_data)
                
                await session.commit()
                await session.refresh(extracted_data)
                
                logger.info(f"✅ Saved extracted invoice data with ID: {extracted_data.id}")
                return extracted_data
                
        except Exception as e:
            logger.error(f"❌ Failed to save extracted invoice data: {str(e)}")
            raise
    
    async def get_contract_by_storage_path(self, storage_path: str) -> Optional[Contract]:
        """
        Get contract by storage path
        
        Args:
            storage_path: GCP Storage path
            
        Returns:
            Contract object or None
        """
        try:
            async with get_async_db_session() as session:
                stmt = select(Contract).where(Contract.storage_path == storage_path)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"❌ Failed to get contract by storage path: {str(e)}")
            raise
    
    async def get_contract_with_invoice_data(self, contract_id: str) -> Optional[Contract]:
        """
        Get contract with extracted invoice data
        
        Args:
            contract_id: Contract ID
            
        Returns:
            Contract object with invoice data or None
        """
        try:
            async with get_async_db_session() as session:
                stmt = (
                    select(Contract)
                    .options(selectinload(Contract.extracted_invoice_data))
                    .where(Contract.id == contract_id)
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"❌ Failed to get contract with invoice data: {str(e)}")
            raise
    
    async def get_contracts_by_user(self, user_id: str) -> List[Contract]:
        """
        Get all contracts for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of Contract objects
        """
        try:
            async with get_async_db_session() as session:
                stmt = (
                    select(Contract)
                    .options(selectinload(Contract.extracted_invoice_data))
                    .where(Contract.user_id == user_id)
                    .order_by(desc(Contract.created_at))
                )
                result = await session.execute(stmt)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"❌ Failed to get contracts for user: {str(e)}")
            raise
    
    async def get_extracted_invoice_data_by_contract(self, contract_id: str) -> Optional[ExtractedInvoiceData]:
        """
        Get extracted invoice data by contract ID
        
        Args:
            contract_id: Contract ID
            
        Returns:
            ExtractedInvoiceData object or None
        """
        try:
            async with get_async_db_session() as session:
                stmt = select(ExtractedInvoiceData).where(ExtractedInvoiceData.contract_id == contract_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"❌ Failed to get extracted invoice data: {str(e)}")
            raise


# Singleton instance
_contract_db_service_instance = None

def get_contract_db_service() -> ContractDatabaseService:
    """Get contract database service singleton"""
    global _contract_db_service_instance
    if _contract_db_service_instance is None:
        _contract_db_service_instance = ContractDatabaseService()
    return _contract_db_service_instance