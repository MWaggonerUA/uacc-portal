"""
Database connection and session management.

This module provides async database connections using SQLAlchemy with async MySQL support.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.core.config import settings

# Base class for ORM models
Base = declarative_base()

# Database URL - using asyncmy or aiomysql for async MySQL support
# Format: mysql+asyncmy://user:password@host:port/database
DATABASE_URL = (
    f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

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
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


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

