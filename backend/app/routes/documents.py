"""
Document management routes for the RFP platform
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.utils.dependencies import get_db_session, get_current_company
from app.models.company import Company
from app.services.document_service import DocumentService
from app.schemas.documents import (
    DocumentUploadSuccessResponse,
    DocumentListSuccessResponse, 
    DocumentStatusSuccessResponse,
    ProcessingStatus,
    ErrorResponse
)

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/companies", tags=["Documents"])


@router.post(
    "/{company_id}/documents",
    response_model=DocumentUploadSuccessResponse,
    status_code=202,  # Changed from 201 to 202 Accepted since processing is started
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type or size"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Upload and process a company document",
    description="Upload a PDF or DOCX document and automatically start processing with RAG. Maximum file size: 10MB."
)
async def upload_document(
    company_id: UUID,
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, DOC only)"),
    current_company: Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db_session)
) -> DocumentUploadSuccessResponse:
    """
    Upload a document for the specified company and automatically start processing.
    
    - **company_id**: UUID of the company
    - **file**: Document file to upload (PDF, DOCX, DOC formats, max 10MB)
    
    Returns document ID, filename, and processing status. Document processing is
    automatically started in the background immediately after upload.
    """
    # Verify company access
    if current_company.id != company_id:
        log.warning("Unauthorized document upload attempt",
                   current_company_id=str(current_company.id),
                   requested_company_id=str(company_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Cannot upload documents for this company"
        )
    
    # Validate file is provided
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    log.info("Document upload request received",
            company_id=str(company_id),
            filename=file.filename,
            content_type=file.content_type)
    
    try:
        document_service = DocumentService(db)
        result = await document_service.upload_document(company_id, file)
        
        log.info("Document upload and processing started",
                company_id=str(company_id),
                doc_id=result.docId,
                filename=result.filename,
                status=result.status)
        
        return DocumentUploadSuccessResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error during document upload",
                 company_id=str(company_id),
                 filename=file.filename,
                 error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document upload"
        )


@router.get(
    "/{company_id}/documents",
    response_model=DocumentListSuccessResponse,
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="List company documents",
    description="List all documents for the authenticated company with optional status filter."
)
async def list_documents(
    company_id: UUID,
    status_filter: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    current_company: Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db_session)
) -> DocumentListSuccessResponse:
    """
    List all documents for the specified company.
    
    - **company_id**: UUID of the company
    - **status**: Optional filter by processing status (PENDING, PROCESSING, COMPLETED, FAILED)
    
    Returns list of documents with metadata.
    """
    # Verify company access
    if current_company.id != company_id:
        log.warning("Unauthorized document list attempt",
                   current_company_id=str(current_company.id),
                   requested_company_id=str(company_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Cannot list documents for this company"
        )
    
    log.info("Document list request received",
            company_id=str(company_id),
            status_filter=status_filter)
    
    try:
        document_service = DocumentService(db)
        result = await document_service.list_documents(company_id, status_filter)
        
        log.info("Document list successful",
                company_id=str(company_id),
                document_count=len(result.documents),
                status_filter=status_filter)
        
        return DocumentListSuccessResponse(data=result)
        
    except Exception as e:
        log.error("Unexpected error during document listing",
                 company_id=str(company_id),
                 error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document listing"
        )


@router.get(
    "/{company_id}/documents/{doc_id}/status",
    response_model=DocumentStatusSuccessResponse,
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get document status",
    description="Get processing status and metadata for a specific document."
)
async def get_document_status(
    company_id: UUID,
    doc_id: str,
    current_company: Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db_session)
) -> DocumentStatusSuccessResponse:
    """
    Get status and metadata for a specific document.
    
    - **company_id**: UUID of the company
    - **doc_id**: Unique document identifier
    
    Returns detailed document information including processing status.
    """
    # Verify company access
    if current_company.id != company_id:
        log.warning("Unauthorized document status attempt",
                   current_company_id=str(current_company.id),
                   requested_company_id=str(company_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Cannot access documents for this company"
        )
    
    log.info("Document status request received",
            company_id=str(company_id),
            doc_id=doc_id)
    
    try:
        document_service = DocumentService(db)
        result = await document_service.get_document_status(company_id, doc_id)
        
        log.info("Document status retrieved successfully",
                company_id=str(company_id),
                doc_id=doc_id,
                status=result.status)
        
        return DocumentStatusSuccessResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error during document status retrieval",
                 company_id=str(company_id),
                 doc_id=doc_id,
                 error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document status retrieval"
        )


@router.delete(
    "/{company_id}/documents/{doc_id}",
    status_code=204,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Delete a document",
    description="Delete a document and clean up associated files and chunks."
)
async def delete_document(
    company_id: UUID,
    doc_id: str,
    current_company: Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db_session)
) -> None:
    """
    Delete a document and clean up associated files and chunks.
    
    - **company_id**: UUID of the company
    - **doc_id**: Unique document identifier
    
    Returns 204 No Content on successful deletion.
    """
    # Verify company access
    if current_company.id != company_id:
        log.warning("Unauthorized document deletion attempt",
                   current_company_id=str(current_company.id),
                   requested_company_id=str(company_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Cannot delete documents for this company"
        )
    
    log.info("Document deletion request received",
            company_id=str(company_id),
            doc_id=doc_id)
    
    try:
        document_service = DocumentService(db)
        await document_service.delete_document(company_id, doc_id)
        
        log.info("Document deleted successfully",
                company_id=str(company_id),
                doc_id=doc_id)
        
        # Return 204 No Content (FastAPI automatically handles this)
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error during document deletion",
                 company_id=str(company_id),
                 doc_id=doc_id,
                 error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document deletion"
        )


@router.post(
    "/{company_id}/documents/{doc_id}/process",
    response_model=DocumentStatusSuccessResponse,
    status_code=202,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Manually re-process document with RAG",
    description="Manually trigger re-processing of a document with text extraction and RAG integration. Typically used when initial automatic processing failed or needs to be refreshed."
)
async def process_document(
    company_id: UUID,
    doc_id: str,
    current_company: Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db_session)
) -> DocumentStatusSuccessResponse:
    """
    Manually re-process a document using RAG document processor.
    
    - **company_id**: UUID of the company
    - **doc_id**: Unique document identifier
    
    Returns document status information after triggering re-processing.
    Note: Documents are automatically processed on upload, use this endpoint
    only when you need to manually re-process a document.
    """
    # Verify company access
    if current_company.id != company_id:
        log.warning("Unauthorized document processing attempt",
                   current_company_id=str(current_company.id),
                   requested_company_id=str(company_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Cannot process documents for this company"
        )
    
    log.info("Manual document re-processing request received",
            company_id=str(company_id),
            doc_id=doc_id)
    
    try:
        document_service = DocumentService(db)
        result = await document_service.process_document(company_id, doc_id)
        
        log.info("Document re-processing triggered successfully",
                company_id=str(company_id),
                doc_id=doc_id,
                status=result.status)
        
        return DocumentStatusSuccessResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error during document processing request",
                 company_id=str(company_id),
                 doc_id=doc_id,
                 error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document processing request"
        )
