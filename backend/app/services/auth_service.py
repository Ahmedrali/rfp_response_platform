"""
Authentication service for company registration and authentication
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional, Tuple

from app.models.company import Company
from app.utils.security import generate_api_key, hash_api_key, verify_api_key
from app.schemas.auth import (
    CompanyRegisterRequest, 
    CompanyRegisterData,
    CompanyAuthenticateRequest,
    CompanyAuthenticateData
)

log = structlog.get_logger(__name__)


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def register_company(self, request: CompanyRegisterRequest) -> CompanyRegisterData:
        """
        Register a new company with API key generation
        
        Args:
            request: Company registration request data
            
        Returns:
            CompanyRegisterData with company details and API key
            
        Raises:
            HTTPException: If company already exists (409) or other errors
        """
        log.info("Attempting to register company", company_name=request.companyName)
        
        try:
            # Check if company already exists
            existing_company = await self._get_company_by_name(request.companyName)
            if existing_company:
                log.warning("Company already exists", company_name=request.companyName)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Company with this name already exists"
                )
            
            # Generate API key and hash it
            api_key = generate_api_key()
            hashed_api_key = hash_api_key(api_key)
            
            # Create new company
            new_company = Company(
                name=request.companyName,
                api_key=hashed_api_key,
                is_active=True
            )
            
            self.db.add(new_company)
            await self.db.commit()
            await self.db.refresh(new_company)
            
            log.info("Company registered successfully", 
                    company_id=str(new_company.id), 
                    company_name=new_company.name)
            
            return CompanyRegisterData(
                companyId=str(new_company.id),
                companyName=new_company.name,
                apiKey=api_key  # Return original API key, not the hash
            )
            
        except IntegrityError as e:
            await self.db.rollback()
            log.error("Database integrity error during company registration", 
                     company_name=request.companyName, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company with this name already exists"
            )
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("Unexpected error during company registration", 
                     company_name=request.companyName, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during registration"
            )
    
    async def authenticate_company(self, request: CompanyAuthenticateRequest) -> CompanyAuthenticateData:
        """
        Authenticate a company using name and API key
        
        Args:
            request: Company authentication request data
            
        Returns:
            CompanyAuthenticateData with company details
            
        Raises:
            HTTPException: If authentication fails (401)
        """
        log.info("Attempting to authenticate company", company_name=request.companyName)
        
        try:
            # Get company by name
            company = await self._get_company_by_name(request.companyName)
            if not company:
                log.warning("Company not found during authentication", 
                           company_name=request.companyName)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid company name or API key"
                )
            
            # Check if company is active
            if not company.is_active:
                log.warning("Inactive company attempted authentication", 
                           company_name=request.companyName)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Company account is inactive"
                )
            
            # Verify API key
            if not verify_api_key(request.apiKey, company.api_key):
                log.warning("Invalid API key during authentication", 
                           company_name=request.companyName)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid company name or API key"
                )
            
            log.info("Company authenticated successfully", 
                    company_id=str(company.id), 
                    company_name=company.name)
            
            return CompanyAuthenticateData(
                companyId=str(company.id),
                companyName=company.name,
                authenticated=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error("Unexpected error during company authentication", 
                     company_name=request.companyName, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during authentication"
            )
    
    async def _get_company_by_name(self, company_name: str) -> Optional[Company]:
        """
        Get company by name
        
        Args:
            company_name: Name of the company to find
            
        Returns:
            Company object if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(Company).where(Company.name == company_name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            log.error("Error fetching company by name", 
                     company_name=company_name, error=str(e))
            return None
    
    async def get_company_by_id(self, company_id: str) -> Optional[Company]:
        """
        Get company by ID
        
        Args:
            company_id: UUID of the company to find
            
        Returns:
            Company object if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(Company).where(Company.id == company_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            log.error("Error fetching company by ID", 
                     company_id=company_id, error=str(e))
            return None
