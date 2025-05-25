"""
Pydantic schemas for authentication endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class CompanyRegisterRequest(BaseModel):
    """Request schema for company registration"""
    companyName: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Company name for registration"
    )


class CompanyRegisterResponse(BaseModel):
    """Response schema for successful company registration"""
    success: bool = True
    data: "CompanyRegisterData"


class CompanyRegisterData(BaseModel):
    """Data payload for company registration response"""
    companyId: str = Field(..., description="UUID of the created company")
    companyName: str = Field(..., description="Name of the company")
    apiKey: str = Field(..., description="Generated API key for the company")


class CompanyAuthenticateRequest(BaseModel):
    """Request schema for company authentication"""
    companyName: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Company name for authentication"
    )
    apiKey: str = Field(
        ..., 
        min_length=1,
        description="API key for authentication"
    )


class CompanyAuthenticateResponse(BaseModel):
    """Response schema for successful company authentication"""
    success: bool = True
    data: "CompanyAuthenticateData"


class CompanyAuthenticateData(BaseModel):
    """Data payload for company authentication response"""
    companyId: str = Field(..., description="UUID of the authenticated company")
    companyName: str = Field(..., description="Name of the company")
    authenticated: bool = Field(True, description="Authentication status")


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    success: bool = False
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


# Update forward references
CompanyRegisterResponse.model_rebuild()
CompanyAuthenticateResponse.model_rebuild()
