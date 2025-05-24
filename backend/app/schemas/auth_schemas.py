from pydantic import BaseModel, Field
from uuid import UUID

# --- Company Registration Schemas ---

class CompanyRegisterRequest(BaseModel):
    companyName: str = Field(..., min_length=1, max_length=255, description="Name of the company to register.")

class CompanyRegisterResponseData(BaseModel):
    companyId: UUID = Field(..., description="Unique identifier for the registered company.")
    companyName: str = Field(..., description="Name of the registered company.")
    apiKey: str = Field(..., description="Generated API key for the company. Store this securely, it will not be shown again.")

class CompanyRegisterResponse(BaseModel):
    success: bool = Field(True, description="Indicates if the registration was successful.")
    data: CompanyRegisterResponseData

# --- Company Authentication Schemas ---

class CompanyAuthenticateRequest(BaseModel):
    companyName: str = Field(..., min_length=1, max_length=255, description="Name of the company to authenticate.")
    apiKey: str = Field(..., description="API key for the company.")

class CompanyAuthenticateResponseData(BaseModel):
    companyId: UUID = Field(..., description="Unique identifier for the authenticated company.")
    companyName: str = Field(..., description="Name of the authenticated company.")
    authenticated: bool = Field(True, description="Indicates if the authentication was successful.")

class CompanyAuthenticateResponse(BaseModel):
    success: bool = Field(True, description="Indicates if the authentication attempt was processed.")
    data: CompanyAuthenticateResponseData

# --- Generic Error Response Schema (Optional, but good practice) ---
# We can define a more generic error schema if needed, or rely on FastAPI's default
# HTTPException handling for now. For specific structured errors:
# class ErrorDetail(BaseModel):
#     message: str
#     type: str | None = None
#
# class ErrorResponse(BaseModel):
#     success: bool = False
#     error: ErrorDetail
