from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.utils.config import settings
from app.models.base import Base

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": "public"}} # Ensure public schema is used for asyncpg
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False, # Important for async context
    autocommit=False,
    autoflush=False,
)


# Function to create all tables in development (bypassing Alembic)
async def create_tables():
    """Create all tables in the database (for development only)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# For getting a session (synchronous style)
def get_session():
    """Get a database session (for testing and scripts)"""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        session.close()

# Dependency to get DB session (moved to dependencies.py for better structure)
# async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()
