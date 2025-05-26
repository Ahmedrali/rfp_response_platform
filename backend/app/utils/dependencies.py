from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy import select
from app.utils.database import AsyncSessionLocal
from app.models.company import Company
from app.utils.security import verify_api_key
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


# Typed dependency for easier usage
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_company(
    authorization: str = Header(..., description="Bearer token with API key"),
    db: AsyncSession = Depends(get_db_session)
) -> Company:
    """
    Dependency to authenticate and get the current company from Authorization header.
    Expected format: "Bearer <api_key>"
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database session
        
    Returns:
        Authenticated Company object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check authorization header format
        if not authorization.startswith("Bearer "):
            log.warning("Invalid authorization header format")
            raise credentials_exception
        
        # Extract API key
        api_key = authorization.replace("Bearer ", "")
        if not api_key:
            log.warning("Missing API key in authorization header")
            raise credentials_exception
        
        # Find company with matching API key
        # Note: We need to check all companies since API keys are hashed
        result = await db.execute(select(Company).where(Company.is_active == True))
        companies = result.scalars().all()
        
        for company in companies:
            if verify_api_key(api_key, company.api_key):
                log.info("Company authenticated successfully", 
                        company_id=str(company.id), 
                        company_name=company.name)
                return company
        
        log.warning("No matching company found for provided API key")
        raise credentials_exception
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error during authentication", error=str(e))
        raise credentials_exception


# Typed dependency for easier usage
CurrentCompany = Annotated[Company, Depends(get_current_company)]


async def verify_company_access(
    company_id: str,
    current_company: Company = Depends(get_current_company)
) -> bool:
    """
    Verify that the authenticated company matches the requested company_id.
    
    Args:
        company_id: The company ID from the URL path
        current_company: The authenticated company
        
    Returns:
        True if access is granted
        
    Raises:
        HTTPException: If company doesn't match or access is denied
    """
    if str(current_company.id) != company_id:
        log.warning("Company access denied", 
                   authenticated_company=str(current_company.id),
                   requested_company=company_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Company mismatch"
        )
    
    return True
