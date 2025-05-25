from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
import structlog

from app.models.company import Company
from app.schemas.auth_schemas import CompanyRegisterRequest, CompanyAuthenticateRequest
from app.utils.security import generate_api_key, hash_api_key, verify_api_key

log = structlog.get_logger(__name__)

class AuthService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def register_company(self, company_data: CompanyRegisterRequest) -> tuple[Company, str]:
        """
        Registers a new company.
        Generates an API key, hashes it, and stores the company.
        Returns the company object and the plain text API key.
        """
        log.info("Attempting to register company", company_name=company_data.companyName)

        # Check if company already exists
        query = select(Company).where(Company.name == company_data.companyName)
        result = await self.db_session.execute(query)
        existing_company = result.scalars().first()

        if existing_company:
            log.warning("Company registration failed: company already exists", company_name=company_data.companyName)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company with this name already exists.",
            )

        # Generate and hash API key
        plain_api_key = generate_api_key()
        hashed_api_key_str = hash_api_key(plain_api_key)

        new_company = Company(
            name=company_data.companyName,
            api_key=hashed_api_key_str, # Store the hashed key
            is_active=True
        )

        self.db_session.add(new_company)
        await self.db_session.flush() # Flush to get ID and other defaults if needed before returning
        # The actual commit will be handled by the get_db_session dependency

        log.info("Company registered successfully", company_name=new_company.name, company_id=new_company.id)
        return new_company, plain_api_key

    async def authenticate_company(self, auth_data: CompanyAuthenticateRequest) -> Company:
        """
        Authenticates a company based on its name and API key.
        Returns the company object if authentication is successful.
        """
        log.info("Attempting to authenticate company", company_name=auth_data.companyName)

        query = select(Company).where(Company.name == auth_data.companyName)
        result = await self.db_session.execute(query)
        company = result.scalars().first()

        if not company:
            log.warning("Authentication failed: company not found", company_name=auth_data.companyName)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid company name or API key.",
            )

        if not company.is_active:
            log.warning("Authentication failed: company is not active", company_name=auth_data.companyName)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # More specific than 401 if user exists but is inactive
                detail="Company account is inactive.",
            )

        if not verify_api_key(auth_data.apiKey, company.api_key):
            log.warning("Authentication failed: invalid API key", company_name=auth_data.companyName)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid company name or API key.",
            )

        log.info("Company authenticated successfully", company_name=company.name, company_id=company.id)
        return company
