#!/usr/bin/env python3
"""
Run database migration for corrected invoice data fields
"""

import asyncio
import logging
from pathlib import Path
from db.postgresdb import engine

logger = logging.getLogger(__name__)

async def run_migration():
    """Run the migration to add corrected invoice data fields"""
    try:
        # Read the migration SQL file
        migration_file = Path(__file__).parent / "migrations" / "add_corrected_invoice_data_fields.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Use the global engine from postgresdb
        
        # Execute the migration
        async with engine.begin() as conn:
            # Split the SQL into individual statements and execute each one
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    logger.info(f"Executing: {statement[:100]}...")
                    await conn.execute(text(statement))
        
        logger.info("✅ Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return False

async def main():
    """Main function"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("🚀 Starting database migration...")
    success = await run_migration()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
    else:
        logger.error("💥 Migration failed!")

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(main())