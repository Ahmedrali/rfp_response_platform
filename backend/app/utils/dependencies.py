from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import APIKeyHeader
from uuid import UUID
import structlog

from app.utils.database import AsyncSessionLocal
from app.models.company import Company
from app.utils.security import verify_api_key

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


# Typed dependency for easier usage
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# --- Authentication Dependency ---

api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_active_company(
    company_id_from_path: Annotated[UUID, Path(description="The ID of the company to access.")],
    api_key: Annotated[str | None, Depends(api_key_header_scheme)],
    db_session: DbSession,
) -> Company:
    """
    Dependency to authenticate a company based on company_id in path and X-API-Key header.
    Ensures the company exists, is active, and the API key is valid.
    """
    if api_key is None:
        log.warning("API key missing in request header", company_id_attempted=company_id_from_path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: API key required in X-API-Key header.",
            headers={"WWW-Authenticate": 'APIKey realm="protected area"'},
        )

    log.debug("Attempting to authenticate company via API key", company_id=company_id_from_path)

    query = select(Company).where(Company.id == company_id_from_path)
    result = await db_session.execute(query)
    company = result.scalars().first()

    if not company:
        log.warning("Company not found for authentication", company_id=company_id_from_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    if not company.is_active:
        log.warning("Authentication failed: company is not active", company_name=company.name, company_id=company.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company account is inactive.",
        )

    if not verify_api_key(api_key, company.api_key):
        log.warning("Authentication failed: invalid API key for company", company_name=company.name, company_id=company.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key for the specified company.",
            headers={"WWW-Authenticate": 'APIKey realm="protected area"'},
        )

    log.info("Company authenticated successfully via API key", company_name=company.name, company_id=company.id)
    return company

# Typed dependency for easier usage in route signatures for authenticated company
AuthenticatedCompany = Annotated[Company, Depends(get_current_active_company)]
