import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Load environment variables from .env file
load_dotenv()

# Function to retrieve environment variables safely
def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing environment variable: {var_name}")
    return value

# Database Configuration
DB_HOST = get_env_variable("DB_HOST")
DB_PORT = get_env_variable("DB_PORT")
DB_NAME = get_env_variable("DB_NAME")
DB_USER = get_env_variable("DB_USER")
DB_PASSWORD = get_env_variable("DB_PASSWORD")

# Database URL for asynchronous PostgreSQL connection
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the async SQLAlchemy engine
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=20,
    max_overflow=0,
    pool_timeout=30,
    pool_pre_ping=True
)

# Session management with AsyncSession
async_sessionmaker = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Async context manager for session scope
@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of async operations."""
    session = async_sessionmaker()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logging.error(f"Transaction failed: {e}", exc_info=True)  # Log exception details
        raise
    finally:
        await session.close()

# Test the asynchronous database connection
async def test_db_connection():
    try:
        async with async_engine.connect() as connection:
            logging.info("Database connection successful!")
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        

# Yield an asynchronous database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an asynchronous database session."""
    async with async_sessionmaker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()  # Rollback in case of error
            raise e
        finally:
            await session.close()  # Close the session when done
            logging.info("Initialization complete.")



