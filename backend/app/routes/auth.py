from fastapi import APIRouter, Depends, HTTPException, status, Request
import structlog

from app.services.auth_service import AuthService
from app.schemas.auth_schemas import (
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    CompanyRegisterResponseData,
    CompanyAuthenticateRequest,
    CompanyAuthenticateResponse,
    CompanyAuthenticateResponseData,
)
from app.utils.dependencies import DbSession # Using the DbSession type alias
from app.utils.config import settings # For API prefix
from app.utils.limiter import limiter # Import the limiter instance

log = structlog.get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/companies", # Using API_V1_STR from settings
    tags=["Authentication"],
)

@router.post(
    "/register",
    response_model=CompanyRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new company",
    response_description="Company registered successfully, returns company details and API key.",
)
@limiter.limit("5/minute") # Apply rate limit: 5 requests per minute per IP
async def register_company_route(
    request: Request, # Required by the limiter
    request_data: CompanyRegisterRequest,
    db_session: DbSession, # Use the typed dependency
):
    """
    Registers a new company.

    - **companyName**: The name of the company to register.
    """
    auth_service = AuthService(db_session)
    try:
        company, plain_api_key = await auth_service.register_company(request_data)
        log.info("Company registration route successful", company_name=company.name)
        return CompanyRegisterResponse(
            success=True,
            data=CompanyRegisterResponseData(
                companyId=company.id,
                companyName=company.name,
                apiKey=plain_api_key, # Return the plain text API key
            ),
        )
    except HTTPException as e:
        # Log the specific HTTP exception details
        log.error("Company registration failed in route", company_name=request_data.companyName, detail=e.detail, status_code=e.status_code)
        raise e # Re-raise the HTTPException to be handled by FastAPI
    except Exception as e:
        # Catch any other unexpected errors
        log.exception("Unexpected error during company registration", company_name=request_data.companyName)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during company registration.",
        )

@router.post(
    "/authenticate",
    response_model=CompanyAuthenticateResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a company",
    response_description="Company authenticated successfully.",
)
async def authenticate_company_route(
    request_data: CompanyAuthenticateRequest,
    db_session: DbSession, # Use the typed dependency
):
    """
    Authenticates a company using its name and API key.

    - **companyName**: The name of the company.
    - **apiKey**: The API key provided during registration.
    """
    auth_service = AuthService(db_session)
    try:
        company = await auth_service.authenticate_company(request_data)
        log.info("Company authentication route successful", company_name=company.name)
        return CompanyAuthenticateResponse(
            success=True,
            data=CompanyAuthenticateResponseData(
                companyId=company.id,
                companyName=company.name,
                authenticated=True,
            ),
        )
    except HTTPException as e:
        log.error("Company authentication failed in route", company_name=request_data.companyName, detail=e.detail, status_code=e.status_code)
        raise e
    except Exception as e:
        log.exception("Unexpected error during company authentication", company_name=request_data.companyName)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during company authentication.",
        )
