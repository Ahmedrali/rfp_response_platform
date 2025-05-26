"""
RFP service for handling RFP document operations
"""
import os
import uuid
import secrets
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import structlog
from fastapi import UploadFile, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.rfp_document import RfpDocument
from app.models.extracted_question import ExtractedQuestion, AnswerStatus
from app.models.question_document_match import QuestionDocumentMatch
from app.models.company_document import CompanyDocument, ProcessingStatus
from app.services.rag_document_processor import DocumentProcessor
from app.utils.file_storage import FileStorage

log = structlog.get_logger(__name__)


class RfpService:
    """Service for RFP document operations"""
    
    def __init__(self):
        """Initialize RFP service"""
        self.file_storage = FileStorage()
        self.document_processor = DocumentProcessor()
    
    async def upload_rfp(self, file: UploadFile, company_id: str, session: AsyncSession) -> Dict:
        """
        Upload an RFP document and create database record
        
        Args:
            file: Uploaded file
            company_id: Company ID
            session: Database session
            
        Returns:
            Dictionary with RFP details
            
        Raises:
            HTTPException: If file is invalid or company doesn't exist
        """
        # Validate company exists
        company_result = await session.execute(select(Company).where(Company.id == company_id))
        company = company_result.scalars().first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )            # Generate unique RFP ID for document storage
        doc_id = f"rfp_{secrets.token_hex(16)}"
            
        # Validate and store file
        try:
            file_path, file_size = await self.file_storage.save_file(file, str(company_id), doc_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Use the same ID we used for file storage
        rfp_id = doc_id
        
        # Create RFP document record
        rfp_document = RfpDocument(
            rfp_id=rfp_id,
            company_id=company_id,
            filename=file.filename,
            file_type=os.path.splitext(file.filename)[1].lower(),
            file_size=file_size,
            file_path=str(file_path),
            processing_status=ProcessingStatus.PENDING
        )
        
        session.add(rfp_document)
        await session.commit()
        await session.refresh(rfp_document)
        
        return {
            "rfpId": rfp_document.rfp_id,
            "filename": rfp_document.filename,
            "status": rfp_document.processing_status.value
        }
    
    async def get_rfp_status(self, rfp_id: str, company_id: str, session: AsyncSession) -> Dict:
        """
        Get RFP document status and extracted questions
        
        Args:
            rfp_id: RFP ID
            company_id: Company ID
            session: Database session
            
        Returns:
            Dictionary with RFP status and questions
            
        Raises:
            HTTPException: If RFP not found or doesn't belong to company
        """
        # Get RFP document
        rfp_query = select(RfpDocument).where(
            RfpDocument.rfp_id == rfp_id,
            RfpDocument.company_id == company_id
        )
        rfp_result = await session.execute(rfp_query)
        rfp_document = rfp_result.scalars().first()
        
        if not rfp_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP document not found"
            )
        
        # Get extracted questions
        questions_query = select(ExtractedQuestion).where(
            ExtractedQuestion.rfp_document_id == rfp_document.id
        ).order_by(ExtractedQuestion.question_number)
        
        questions_result = await session.execute(questions_query)
        questions = questions_result.scalars().all()
        
        # Format questions
        questions_data = []
        for question in questions:
            # Get document matches
            matches_query = select(QuestionDocumentMatch).where(
                QuestionDocumentMatch.question_id == question.id
            )
            matches_result = await session.execute(matches_query)
            matches = matches_result.scalars().all()
            
            # Format matches
            matched_documents = []
            for match in matches:
                doc_query = select(CompanyDocument).where(
                    CompanyDocument.id == match.document_id
                )
                doc_result = await session.execute(doc_query)
                doc = doc_result.scalars().first()
                
                if doc:
                    matched_documents.append({
                        "documentId": doc.doc_id,
                        "filename": doc.filename,
                        "relevanceScore": float(match.relevance_score),
                        "chunkIds": match.chunk_ids
                    })
            
            questions_data.append({
                "questionId": str(question.id),
                "questionNumber": question.question_number,
                "questionText": question.question_text,
                "questionType": question.question_type,
                "status": question.answer_status.value,
                "answer": question.generated_answer,
                "confidenceScore": float(question.confidence_score) if question.confidence_score else None,
                "matchedDocuments": matched_documents
            })
        
        return {
            "rfpId": rfp_document.rfp_id,
            "filename": rfp_document.filename,
            "status": rfp_document.processing_status.value,
            "extractionScore": float(rfp_document.extraction_score) if rfp_document.extraction_score else None,
            "questionsCount": rfp_document.questions_count,
            "processingStartedAt": rfp_document.processing_started_at.isoformat() if rfp_document.processing_started_at else None,
            "processingCompletedAt": rfp_document.processing_completed_at.isoformat() if rfp_document.processing_completed_at else None,
            "questions": questions_data
        }
    
    async def process_rfp(self, rfp_document: RfpDocument, session: AsyncSession) -> None:
        """
        Process an RFP document using the RAG document processor
        
        Args:
            rfp_document: RFP document to process
            session: Database session
        """
        try:
            # Update status to processing
            rfp_document.processing_status = ProcessingStatus.PROCESSING
            rfp_document.processing_started_at = datetime.now()
            await session.commit()
            
            # Extract text from file
            file_content = self.file_storage.extract_text(rfp_document.file_path)
            
            # Extract questions using RAG document processor
            extraction_result = self.document_processor.extract_questions(file_content)
            
            # Update RFP document with extraction results
            rfp_document.extraction_score = extraction_result.confidence_score
            rfp_document.questions_count = len(extraction_result.questions)
            
            # Create questions and generate answers
            for i, question_text in enumerate(extraction_result.questions, 1):
                # Create question record
                question = ExtractedQuestion(
                    rfp_document_id=rfp_document.id,
                    question_number=i,
                    question_text=question_text,
                    question_type="General",  # Default type
                    answer_status=AnswerStatus.PROCESSING
                )
                session.add(question)
                await session.commit()
                await session.refresh(question)
                
                # Generate answer using RAG
                try:
                    answer_result = self.document_processor.answer_question(question_text, str(rfp_document.company_id))
                    
                    # Update question with answer
                    question.generated_answer = answer_result.answer
                    question.confidence_score = answer_result.confidence_score
                    question.answer_status = AnswerStatus.ANSWERED
                    
                    # Create document matches based on chunk IDs
                    if answer_result.chunk_ids:
                        # Get company documents containing these chunks
                        for chunk_id in answer_result.chunk_ids:
                            # Find document that contains this chunk
                            document_query = select(CompanyDocument).join(
                                CompanyDocument.chunks
                            ).where(
                                CompanyDocument.company_id == rfp_document.company_id,
                                CompanyDocument.chunks.any(chunk_id=chunk_id)
                            )
                            document_result = await session.execute(document_query)
                            document = document_result.scalars().first()
                            
                            if document:
                                # Create match record
                                match = QuestionDocumentMatch(
                                    question_id=question.id,
                                    document_id=document.id,
                                    relevance_score=answer_result.confidence_score,
                                    chunk_ids=[chunk_id]
                                )
                                session.add(match)
                    
                    await session.commit()
                
                except Exception as e:
                    log.error("Error generating answer", question_id=str(question.id), error=str(e))
                    question.answer_status = AnswerStatus.FAILED
                    await session.commit()
            
            # Update RFP status to completed
            rfp_document.processing_status = ProcessingStatus.COMPLETED
            rfp_document.processing_completed_at = datetime.now()
            await session.commit()
            
        except Exception as e:
            log.error("Error processing RFP", rfp_id=rfp_document.rfp_id, error=str(e))
            rfp_document.processing_status = ProcessingStatus.FAILED
            rfp_document.error_message = str(e)
            await session.commit()
    
    def process_rfp_sync(self, rfp_document: RfpDocument, session) -> None:
        """
        Process an RFP document using the RAG document processor (synchronous version for Celery)
        
        Args:
            rfp_document: RFP document to process
            session: Synchronous database session
        """
        try:
            # Update status to processing
            rfp_document.processing_status = ProcessingStatus.PROCESSING
            rfp_document.processing_started_at = datetime.now()
            session.commit()
            
            # Extract text from file
            file_content = self.file_storage.extract_text(rfp_document.file_path)
            
            # Extract questions using RAG document processor
            extraction_result = self.document_processor.extract_questions(file_content)
            
            # Update RFP document with extraction results
            rfp_document.extraction_score = extraction_result.confidence_score
            rfp_document.questions_count = len(extraction_result.questions)
            
            # Create questions and generate answers
            for i, question_text in enumerate(extraction_result.questions, 1):
                # Create question record
                question = ExtractedQuestion(
                    rfp_document_id=rfp_document.id,
                    question_number=i,
                    question_text=question_text,
                    question_type="General",  # Default type
                    answer_status=AnswerStatus.PROCESSING
                )
                session.add(question)
                session.commit()
                session.refresh(question)
                
                # Generate answer using RAG
                try:
                    answer_result = self.document_processor.answer_question(question_text, str(rfp_document.company_id))
                    
                    # Update question with answer
                    question.generated_answer = answer_result.answer
                    question.confidence_score = answer_result.confidence_score
                    question.answer_status = AnswerStatus.ANSWERED
                    
                    # Create document matches based on chunk IDs
                    if answer_result.chunk_ids:
                        # Get company documents containing these chunks
                        for chunk_id in answer_result.chunk_ids:
                            # Find document that contains this chunk
                            document = session.query(CompanyDocument).join(
                                CompanyDocument.chunks
                            ).filter(
                                CompanyDocument.company_id == rfp_document.company_id,
                                CompanyDocument.chunks.any(chunk_id=chunk_id)
                            ).first()
                            
                            if document:
                                # Create match record
                                match = QuestionDocumentMatch(
                                    question_id=question.id,
                                    document_id=document.id,
                                    relevance_score=answer_result.confidence_score,
                                    chunk_ids=[chunk_id]
                                )
                                session.add(match)
                    
                    session.commit()
                
                except Exception as e:
                    log.error("Error generating answer", question_id=str(question.id), error=str(e))
                    question.answer_status = AnswerStatus.FAILED
                    session.commit()
            
            # Update RFP status to completed
            rfp_document.processing_status = ProcessingStatus.COMPLETED
            rfp_document.processing_completed_at = datetime.now()
            session.commit()
            
        except Exception as e:
            log.error("Error processing RFP", rfp_id=rfp_document.rfp_id, error=str(e))
            rfp_document.processing_status = ProcessingStatus.FAILED
            rfp_document.error_message = str(e)
            session.commit()
