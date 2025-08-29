import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it in your .env file or environment.")

engine = create_async_engine(DATABASE_URL, echo=True)

# Create a sessionmaker for async sessions
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False 
)

Base = declarative_base()

async def get_db():
    """
    Dependency to get an asynchronous database session.
    """
    try:
        async with AsyncSessionLocal() as session:
            print("Database session created successfully.")
            yield session
    except Exception as e:
        print(f"Error creating database session: {e}")
        raise 