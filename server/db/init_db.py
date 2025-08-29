import asyncio
import logging
from sqlalchemy.exc import SQLAlchemyError
from .postgresdb import engine, Base
from models.database_models import User, Address, SecurityEvent, UserSession

logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables"""
    try:
        logger.info("🔄 Creating database tables...")
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully!")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error while creating tables: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error while creating tables: {str(e)}")
        return False


async def drop_tables():
    """Drop all database tables (for development/testing)"""
    try:
        logger.warning("⚠️ Dropping all database tables...")
        
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("✅ Database tables dropped successfully!")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error while dropping tables: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error while dropping tables: {str(e)}")
        return False


async def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        logger.info("🔄 Resetting database...")
        
        # Drop existing tables
        await drop_tables()
        
        # Create tables again
        await create_tables()
        
        logger.info("✅ Database reset completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error resetting database: {str(e)}")
        return False


async def check_database_connection():
    """Check if database connection is working"""
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
        
        logger.info("✅ Database connection is working!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    async def main():
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
        # Check connection
        if not await check_database_connection():
            logger.error("❌ Cannot connect to database. Please check your DATABASE_URL.")
            return
        
        # Create tables
        await create_tables()
        
        logger.info("🎉 Database initialization completed!")
    
    asyncio.run(main())