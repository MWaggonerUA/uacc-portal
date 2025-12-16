"""
Database connection and session management.

This module provides async database connections using SQLAlchemy with async MySQL support.
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()

# Database URL - using asyncmy or aiomysql for async MySQL support
# Format: mysql+asyncmy://user:password@host:port/database
DATABASE_URL = (
    f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Log connection details (without password) for debugging
masked_password = "*" * len(settings.DB_PASSWORD) if settings.DB_PASSWORD else "(empty)"
connection_info = (
    f"mysql+asyncmy://{settings.DB_USER}:{masked_password}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)
logger.info(f"Database connection configured: {connection_info}")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.APP_ENV == "development",  # Log SQL queries in development
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.
    
    Usage in FastAPI routes:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                # Log connection errors with helpful context
                error_str = str(e).lower()
                if "connection refused" in error_str or "errno 111" in error_str:
                    logger.error(
                        f"Database connection refused. "
                        f"Host: {settings.DB_HOST}, Port: {settings.DB_PORT}. "
                        f"Check if MySQL is running and accessible. "
                        f"Run 'scripts/diagnose_db_connection.py' for diagnostics."
                    )
                elif "access denied" in error_str or "authentication" in error_str:
                    logger.error(
                        f"Database authentication failed for user '{settings.DB_USER}'. "
                        f"Check username and password in configuration."
                    )
                elif "unknown database" in error_str or "doesn't exist" in error_str:
                    logger.error(
                        f"Database '{settings.DB_NAME}' does not exist. "
                        f"Create the database or update DB_NAME in configuration."
                    )
                raise
            finally:
                await session.close()
    except Exception as e:
        # Re-raise with additional context for connection errors
        error_str = str(e).lower()
        if "connection refused" in error_str or "errno 111" in error_str:
            raise ConnectionError(
                f"Cannot connect to MySQL server at {settings.DB_HOST}:{settings.DB_PORT}. "
                f"Connection refused. Please check:\n"
                f"  1. MySQL server is running\n"
                f"  2. MySQL is accessible at {settings.DB_HOST}:{settings.DB_PORT}\n"
                f"  3. Configuration file exists at ~/config/env/uacc_db.env\n"
                f"  4. Run 'python scripts/diagnose_db_connection.py' for detailed diagnostics"
            ) from e
        raise


async def init_db():
    """
    Initialize database tables.
    Call this on application startup to create all tables.
    """
    async with engine.begin() as conn:
        # Import all models here so they're registered with Base
        from backend.models.orm_models import (
            BudgetRecord,
            FundingRecord,
            ILabsRecord,
            MembershipRecord,
            ProposalRecord,
            PublicationRecord,
        )
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections on application shutdown."""
    try:
        await engine.dispose()
    except Exception:
        # Ignore errors during shutdown if engine wasn't initialized
        pass

