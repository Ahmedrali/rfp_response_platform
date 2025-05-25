"""
Authentication routes for company registration and authentication
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.dependencies import get_db_session, get_current_company
from app.services.auth_service import AuthService
from app.schemas.auth import (
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    CompanyAuthenticateRequest,
    CompanyAuthenticateResponse,
    ErrorResponse
)
from app.utils.rate_limiting import limiter
from app.models.company import Company

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/companies", tags=["Authentication"])


@router.post(
    "/register",
    response_model=CompanyRegisterResponse,
    status_code=201,
    responses={
        409: {"model": ErrorResponse, "description": "Company already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Register a new company",
    description="Register a new company and generate an API key for authentication"
)
@limiter.limit("5/minute")  # Rate limit: 5 registrations per minute per IP
async def register_company(
    request: Request,
    company_data: CompanyRegisterRequest,
    db: AsyncSession = Depends(get_db_session)
) -> CompanyRegisterResponse:
    """
    Register a new company with API key generation.
    
    - **companyName**: Name of the company to register (must be unique)
    
    Returns the company ID, name, and generated API key.
    """
    log.info("Company registration request received", 
             company_name=company_data.companyName)
    
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.register_company(company_data)
        
        log.info("Company registration successful", 
                company_id=result.companyId,
                company_name=result.companyName)
        
        return CompanyRegisterResponse(data=result)
        
    except HTTPException as e:
        log.warning("Company registration failed", 
                   company_name=company_data.companyName,
                   status_code=e.status_code,
                   detail=e.detail)
        raise
    except Exception as e:
        log.error("Unexpected error during company registration", 
                 company_name=company_data.companyName,
                 error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error during registration"
        )


@router.post(
    "/authenticate",
    response_model=CompanyAuthenticateResponse,
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Authenticate a company",
    description="Authenticate a company using company name and API key"
)
async def authenticate_company(
    auth_data: CompanyAuthenticateRequest,
    db: AsyncSession = Depends(get_db_session)
) -> CompanyAuthenticateResponse:
    """
    Authenticate a company using name and API key.
    
    - **companyName**: Name of the company
    - **apiKey**: API key generated during registration
    
    Returns company details if authentication is successful.
    """
    log.info("Company authentication request received", 
             company_name=auth_data.companyName)
    
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.authenticate_company(auth_data)
        
        log.info("Company authentication successful", 
                company_id=result.companyId,
                company_name=result.companyName)
        
        return CompanyAuthenticateResponse(data=result)
        
    except HTTPException as e:
        log.warning("Company authentication failed", 
                   company_name=auth_data.companyName,
                   status_code=e.status_code,
                   detail=e.detail)
        raise
    except Exception as e:
        log.error("Unexpected error during company authentication", 
                 company_name=auth_data.companyName,
                 error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )


@router.get(
    "/profile",
    summary="Get authenticated company profile",
    description="Get profile information for the authenticated company"
)
async def get_company_profile(
    current_company: Company = Depends(get_current_company)
):
    """
    Get profile information for the authenticated company.
    Requires valid Authorization header with Bearer token.
    """
    return {
        "success": True,
        "data": {
            "companyId": str(current_company.id),
            "companyName": current_company.name,
            "isActive": current_company.is_active,
            "createdAt": current_company.created_at.isoformat() if current_company.created_at else None
        }
    }
