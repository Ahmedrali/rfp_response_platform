"""
RFP API routes for the RFP platform
"""
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, Path, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.rfp import ApiResponse, RfpUploadResponse, RfpStatusResponse
from app.services.rfp_service import RfpService
from app.tasks.rfp_tasks import process_rfp_document
from app.utils.dependencies import get_db_session, verify_company_access
from app.utils.rate_limiting import limiter

router = APIRouter(tags=["RFP"], prefix="/api/v1")


@router.post("/companies/{company_id}/rfp/upload", response_model=ApiResponse)
@limiter.limit("5/minute")
async def upload_rfp(
    request: Request,  # Required by the limiter
    company_id: Annotated[str, Path()],
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[bool, Depends(verify_company_access)]
):
    """
    Upload an RFP document for processing
    
    Args:
        company_id: Company ID
        file: Uploaded RFP document
        db: Database session
        _: Verify company access
        
    Returns:
        RFP document details
    """
    rfp_service = RfpService()
    result = await rfp_service.upload_rfp(file, company_id, db)
    
    # Trigger background processing task
    process_rfp_document.delay(result["rfpId"])
    
    return ApiResponse(
        success=True,
        data=RfpUploadResponse(
            rfpId=result["rfpId"],
            filename=result["filename"],
            status=result["status"]
        ).model_dump()
    )


@router.get("/companies/{company_id}/rfp/{rfp_id}/status", response_model=ApiResponse)
async def get_rfp_status(
    company_id: Annotated[str, Path()],
    rfp_id: Annotated[str, Path()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[bool, Depends(verify_company_access)]
):
    """
    Get RFP document processing status
    
    Args:
        company_id: Company ID
        rfp_id: RFP ID
        db: Database session
        _: Verify company access
        
    Returns:
        RFP status with extracted questions and answers
    """
    rfp_service = RfpService()
    result = await rfp_service.get_rfp_status(rfp_id, company_id, db)
    
    return ApiResponse(
        success=True,
        data=result
    )
