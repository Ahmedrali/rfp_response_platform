"""
Document service for business logic operations
"""
import secrets
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
import structlog

from app.models.company_document import CompanyDocument, ProcessingStatus
from app.models.document_chunk import DocumentChunk
from app.models.question_document_match import QuestionDocumentMatch
from app.utils.file_storage import file_storage
from app.schemas.documents import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentListItem,
    DocumentStatusResponse
)

log = structlog.get_logger(__name__)


class DocumentService:
    """Service class for document management operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize document service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _generate_doc_id(self) -> str:
        """Generate unique document ID"""
        return f"doc_{secrets.token_hex(16)}"
    
    async def upload_document(
        self,
        company_id: UUID,
        file: UploadFile
    ) -> DocumentUploadResponse:
        """
        Upload and store a document for a company.
        
        Args:
            company_id: Company ID
            file: Uploaded file
            
        Returns:
            Document upload response
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Generate unique document ID
            doc_id = self._generate_doc_id()
            
            log.info("Starting document upload",
                    company_id=str(company_id),
                    doc_id=doc_id,
                    filename=file.filename,
                    content_type=file.content_type)
            
            # Save file using file storage utility
            file_path, file_size = await file_storage.save_file(
                file=file,
                company_id=str(company_id),
                doc_id=doc_id
            )
            
            # Get file type from filename
            file_type = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else 'unknown'
            
            # Create database record
            document = CompanyDocument(
                doc_id=doc_id,
                company_id=company_id,
                filename=file.filename or f"document.{file_type}",
                file_type=file_type,
                file_size=file_size,
                file_path=file_path,
                processing_status=ProcessingStatus.PENDING,
                meta_data={
                    "content_type": file.content_type,
                    "uploaded_at": datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(document)
            await self.db.flush()  # Flush to get the ID
            
            log.info("Document uploaded successfully",
                    company_id=str(company_id),
                    doc_id=doc_id,
                    document_id=str(document.id),
                    filename=file.filename,
                    file_size=file_size)
            
            # Automatically trigger document processing
            log.info("Automatically triggering document processing",
                    company_id=str(company_id),
                    doc_id=doc_id,
                    document_id=str(document.id))
            
            # Import here to avoid circular imports
            from app.tasks.document_tasks import process_document
            
            # Update document status to PROCESSING
            document.processing_status = ProcessingStatus.PROCESSING
            document.processing_started_at = datetime.utcnow()
            await self.db.commit()  # Commit the changes to the database
            
            # Send task to Celery
            process_document.delay(
                document_id=str(document.id),
                company_id=str(company_id)
            )
            
            return DocumentUploadResponse(
                docId=doc_id,
                filename=document.filename,
                status=ProcessingStatus.PROCESSING  # Return PROCESSING status instead of PENDING
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error("Error uploading document",
                     company_id=str(company_id),
                     filename=file.filename,
                     error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload document"
            )
    
    async def list_documents(
        self,
        company_id: UUID,
        status_filter: Optional[ProcessingStatus] = None
    ) -> DocumentListResponse:
        """
        List all documents for a company.
        
        Args:
            company_id: Company ID
            status_filter: Optional status filter
            
        Returns:
            List of documents
        """
        try:
            # Build query
            query = select(CompanyDocument).where(
                CompanyDocument.company_id == company_id
            )
            
            if status_filter:
                query = query.where(CompanyDocument.processing_status == status_filter)
            
            # Order by creation date (newest first)
            query = query.order_by(CompanyDocument.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            documents = result.scalars().all()
            
            # Convert to response format
            document_items = []
            for doc in documents:
                document_items.append(DocumentListItem(
                    docId=doc.doc_id,
                    filename=doc.filename,
                    fileType=doc.file_type,
                    fileSize=doc.file_size,
                    status=doc.processing_status,
                    chunkCount=doc.chunk_count,
                    processingStartedAt=doc.processing_started_at,
                    processingCompletedAt=doc.processing_completed_at,
                    createdAt=doc.created_at,
                    errorMessage=doc.error_message
                ))
            
            log.info("Documents listed successfully",
                    company_id=str(company_id),
                    document_count=len(document_items),
                    status_filter=status_filter)
            
            return DocumentListResponse(documents=document_items)
            
        except Exception as e:
            log.error("Error listing documents",
                     company_id=str(company_id),
                     error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list documents"
            )
    
    async def get_document_status(
        self,
        company_id: UUID,
        doc_id: str
    ) -> DocumentStatusResponse:
        """
        Get status and metadata for a specific document.
        
        Args:
            company_id: Company ID
            doc_id: Document ID
            
        Returns:
            Document status information
            
        Raises:
            HTTPException: If document not found
        """
        try:
            # Query for document
            query = select(CompanyDocument).where(
                and_(
                    CompanyDocument.company_id == company_id,
                    CompanyDocument.doc_id == doc_id
                )
            )
            
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()
            
            if not document:
                log.warning("Document not found",
                           company_id=str(company_id),
                           doc_id=doc_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            log.info("Document status retrieved",
                    company_id=str(company_id),
                    doc_id=doc_id,
                    status=document.processing_status)
            
            return DocumentStatusResponse(
                docId=document.doc_id,
                filename=document.filename,
                fileType=document.file_type,
                fileSize=document.file_size,
                status=document.processing_status,
                chunkCount=document.chunk_count,
                processingStartedAt=document.processing_started_at,
                processingCompletedAt=document.processing_completed_at,
                createdAt=document.created_at,
                updatedAt=document.updated_at,
                metadata=document.meta_data,
                errorMessage=document.error_message
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error("Error getting document status",
                     company_id=str(company_id),
                     doc_id=doc_id,
                     error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get document status"
            )
    
    async def delete_document(
        self,
        company_id: UUID,
        doc_id: str
    ) -> None:
        """
        Delete a document and clean up associated files and chunks.
        
        Args:
            company_id: Company ID
            doc_id: Document ID
            
        Raises:
            HTTPException: If document not found or deletion fails
        """
        try:
            # Query for document with relationships
            query = select(CompanyDocument).options(
                selectinload(CompanyDocument.chunks),
                selectinload(CompanyDocument.question_matches)
            ).where(
                and_(
                    CompanyDocument.company_id == company_id,
                    CompanyDocument.doc_id == doc_id
                )
            )
            
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()
            
            if not document:
                log.warning("Document not found for deletion",
                           company_id=str(company_id),
                           doc_id=doc_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            log.info("Starting document deletion",
                    company_id=str(company_id),
                    doc_id=doc_id,
                    filename=document.filename,
                    chunk_count=len(document.chunks),
                    match_count=len(document.question_matches))
            
            # Delete file from storage
            await file_storage.delete_file(document.file_path)
            
            # Delete database record (cascading deletes will handle chunks and matches)
            await self.db.delete(document)
            
            log.info("Document deleted successfully",
                    company_id=str(company_id),
                    doc_id=doc_id)
            
        except HTTPException:
            raise
        except Exception as e:
            log.error("Error deleting document",
                     company_id=str(company_id),
                     doc_id=doc_id,
                     error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
    
    async def process_document(
        self,
        company_id: UUID,
        doc_id: str
    ) -> DocumentStatusResponse:
        """
        Trigger background processing for a document using RAG.
        
        Args:
            company_id: Company ID
            doc_id: Document ID
            
        Returns:
            Updated document status
            
        Raises:
            HTTPException: If document not found or processing fails
        """
        try:
            # Query for document
            query = select(CompanyDocument).where(
                and_(
                    CompanyDocument.company_id == company_id,
                    CompanyDocument.doc_id == doc_id
                )
            )
            
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()
            
            if not document:
                log.warning("Document not found for processing",
                           company_id=str(company_id),
                           doc_id=doc_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            # Check if document is already processed or processing
            if document.processing_status == ProcessingStatus.PROCESSING:
                log.info("Document already processing",
                        company_id=str(company_id),
                        doc_id=doc_id,
                        status=document.processing_status)
                
                # Return current status
                return await self.get_document_status(company_id, doc_id)
            
            # For re-processing, we need to clear any existing chunks
            if document.processing_status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                log.info("Re-processing document - clearing existing chunks",
                        company_id=str(company_id),
                        doc_id=doc_id,
                        current_chunk_count=document.chunk_count)
                
                # Delete existing chunks
                delete_query = delete(DocumentChunk).where(
                    DocumentChunk.document_id == document.id
                )
                await self.db.execute(delete_query)
                
                # Reset chunk count
                document.chunk_count = 0
                
                # Clear any error message from previous processing
                if document.error_message:
                    document.error_message = None
            
            # Submit background task for processing
            from app.tasks.document_tasks import process_document
            
            log.info("Triggering document processing task",
                    company_id=str(company_id),
                    doc_id=doc_id,
                    document_id=str(document.id))
            
            # Send task to Celery
            process_document.delay(
                document_id=str(document.id),
                company_id=str(company_id)
            )
            
            # Update document status to PROCESSING
            document.processing_status = ProcessingStatus.PROCESSING
            document.processing_started_at = datetime.utcnow()
            await self.db.commit()
            
            log.info("Document processing started",
                    company_id=str(company_id),
                    doc_id=doc_id)
            
            # Return updated status
            return await self.get_document_status(company_id, doc_id)
            
        except HTTPException:
            raise
        except Exception as e:
            log.error("Error triggering document processing",
                     company_id=str(company_id),
                     doc_id=doc_id,
                     error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document"
            )
