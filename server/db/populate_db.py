#!/usr/bin/env python3
"""
Database Population Script
Initializes and populates PostgreSQL database with sample data
"""

import asyncio
import os
import sys
import logging

# Add server directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.init_db import create_tables, check_database_connection

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def populate_database():
    """Initialize tables and populate with sample data"""
    try:
        logger.info("🔄 Starting database population...")
        
        # Check connection
        logger.info("📡 Checking database connection...")
        if not await check_database_connection():
            logger.error("❌ Cannot connect to database. Check your DATABASE_URL in .env")
            return False
        
        # Create tables
        logger.info("🏗️  Creating database tables...")
        if not await create_tables():
            logger.error("❌ Failed to create tables")
            return False
        
        # Import required modules for database operations
        from sqlalchemy import text
        from db.postgresdb import engine
        
        # Read and execute sample data SQL
        sample_data_path = os.path.join(os.path.dirname(__file__), 'sample_data.sql')
        
        if not os.path.exists(sample_data_path):
            logger.error(f"❌ Sample data file not found: {sample_data_path}")
            return False
        
        logger.info("📝 Reading sample data file...")
        with open(sample_data_path, 'r') as f:
            sql_content = f.read()
        
        # Split SQL file into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        logger.info("💾 Inserting sample data...")
        async with engine.begin() as conn:
            for i, statement in enumerate(statements):
                if statement and not statement.startswith('--'):
                    try:
                        print(f"Executing statement {i+1}: {statement}")
                        await conn.execute(text(statement))
                        print(f"✅ Executed statement {i+1}/{len(statements)}")
                        logger.debug(f"✅ Executed statement {i+1}/{len(statements)}")
                    except Exception as e:
                        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                            logger.debug(f"⚠️  Skipped duplicate data in statement {i+1}")
                        else:
                            logger.warning(f"⚠️  Warning in statement {i+1}: {str(e)}")
        
        logger.info("✅ Database population completed successfully!")
        
        # Verify data was inserted
        logger.info("🔍 Verifying inserted data...")
        async with engine.begin() as conn:
            # Check users
            result = await conn.execute(text("SELECT COUNT(*) as count FROM users"))
            user_count = result.fetchone()[0]
            logger.info(f"👥 Users: {user_count}")
            
            # Check invoices  
            result = await conn.execute(text("SELECT COUNT(*) as count FROM invoices"))
            invoice_count = result.fetchone()[0]
            logger.info(f"🧾 Invoices: {invoice_count}")
            
            # Check templates
            result = await conn.execute(text("SELECT COUNT(*) as count FROM invoice_templates"))
            template_count = result.fetchone()[0]
            logger.info(f"📄 Templates: {template_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database population failed: {str(e)}")
        return False

def print_connection_info():
    """Print database connection instructions"""
    print("\n" + "="*60)
    print("🔗 DATABASE CONNECTION INSTRUCTIONS")
    print("="*60)
    print()
    print("To connect to PostgreSQL using psql:")
    print("1. Using password from .env file:")
    print("   psql -h localhost -U postgres -d smart_invoice_scheduler")
    print("   Password: ramsha123")
    print()
    print("2. Using environment variable:")
    print("   PGPASSWORD=ramsha123 psql -h localhost -U postgres -d smart_invoice_scheduler")
    print()
    print("3. Once connected, useful commands:")
    print("   \dt                          # List all tables")
    print("   \d invoices                  # Describe invoices table")
    print("   SELECT * FROM invoices;      # View all invoices")
    print("   SELECT * FROM invoice_templates; # View all templates")
    print("   SELECT COUNT(*) FROM invoices;   # Count invoices")
    print()
    print("4. View sample invoices:")
    print("   SELECT invoice_number, client_name, total_amount, status")
    print("   FROM invoices ORDER BY created_at DESC;")
    print()

async def main():
    """Main entry point"""
    print("🚀 Smart Invoice Scheduler - Database Population")
    print("This script will initialize tables and insert sample data")
    print()
    
    success = await populate_database()
    
    if success:
        print_connection_info()
        print("🎉 Database is ready! You can now:")
        print("   1. Connect with psql (see instructions above)")
        print("   2. Start the FastAPI server to test endpoints")
        print("   3. View templates in the React frontend")
    else:
        print("❌ Database population failed. Check the logs above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
