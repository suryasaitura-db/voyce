"""
Database configuration and connection management.
Supports both PostgreSQL and Databricks backends with async SQLAlchemy.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

# Database engine
engine = None
async_session_maker = None


def get_engine_config():
    """Get engine configuration based on database backend."""
    config = {
        "echo": settings.DEBUG,
        "future": True,
    }

    if settings.DB_BACKEND == "postgresql":
        config.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        })
    elif settings.DB_BACKEND == "databricks":
        # Databricks uses HTTP connections, disable pooling
        config.update({
            "poolclass": NullPool,
        })

    return config


async def init_db():
    """Initialize database connection."""
    global engine, async_session_maker

    logger.info(f"Initializing database connection (backend: {settings.DB_BACKEND})")

    try:
        # Create async engine
        engine = create_async_engine(
            settings.database_url,
            **get_engine_config()
        )

        # Create session maker
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Test connection
        async with engine.begin() as conn:
            if settings.DB_BACKEND == "postgresql":
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"Connected to PostgreSQL: {version}")
            elif settings.DB_BACKEND == "databricks":
                result = await conn.execute(text("SELECT current_version()"))
                version = result.scalar()
                logger.info(f"Connected to Databricks: {version}")

        # Create tables (in production, use migrations instead)
        if settings.ENVIRONMENT == "development":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created")

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise


async def close_db():
    """Close database connection."""
    global engine

    if engine:
        logger.info("Closing database connection")
        await engine.dispose()
        logger.info("Database connection closed")


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def execute_query(query: str, params: dict = None):
    """
    Execute a raw SQL query.

    Args:
        query: SQL query string
        params: Query parameters

    Returns:
        Query result
    """
    if not engine:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with engine.begin() as conn:
        result = await conn.execute(text(query), params or {})
        return result


async def get_current_user_id():
    """
    Get current user ID for row-level security.
    This should be set by middleware/context.
    """
    # This is a placeholder - implement based on your auth system
    # Could use contextvars to store user context
    return None


async def set_row_level_security_context(session: AsyncSession, user_id: str):
    """
    Set row-level security context for the session.

    Args:
        session: Database session
        user_id: Current user ID
    """
    if settings.DB_BACKEND == "postgresql":
        # PostgreSQL row-level security
        await session.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": user_id}
        )
    elif settings.DB_BACKEND == "databricks":
        # Databricks Unity Catalog has built-in row-level security
        # This is handled at the catalog/schema level
        pass
