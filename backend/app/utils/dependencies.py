from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import AsyncSessionLocal
import structlog

log = structlog.get_logger(__name__)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get an SQLAlchemy asynchronous database session.
    Ensures the session is closed after the request.
    Handles commit on success and rollback on failure.
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
        log.debug("Database session committed")
    except Exception as e:
        log.error("Database session rollback due to exception", exc_info=e)
        await session.rollback()
        raise
    finally:
        await session.close()
        log.debug("Database session closed")
