#!/usr/bin/env python3
"""
Script to create database tables for contract and invoice data.
"""
import asyncio
from db.postgresdb import engine, Base
from models.database_models import Contract, ContractParty, ExtractedInvoiceData, GeneratedInvoice
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Create all database tables"""
    try:
        logger.info("🚀 Creating database tables...")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully!")
        logger.info("Tables created:")
        logger.info("  - contracts")
        logger.info("  - contract_parties") 
        logger.info("  - extracted_invoice_data")
        logger.info("  - generated_invoices")
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())