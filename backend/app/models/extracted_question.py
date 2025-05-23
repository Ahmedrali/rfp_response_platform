"""
Extracted question model for the RFP platform
"""
from enum import Enum

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Index, ForeignKey, DECIMAL, Boolean
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AnswerStatus(str, Enum):
    """Answer status enum for questions"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ANSWERED = "ANSWERED"
    FAILED = "FAILED"


class ExtractedQuestion(BaseModel):
    """Extracted question model representing questions from RFP documents"""
    __tablename__ = 'extracted_questions'

    rfp_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey('rfp_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    question_number = Column(
        Integer,
        nullable=False,
        index=True
    )
    
    question_text = Column(
        Text,
        nullable=False
    )
    
    question_type = Column(
        String(100),
        nullable=True,
        index=True
    )
    
    generated_answer = Column(
        Text,
        nullable=True
    )
    
    confidence_score = Column(
        DECIMAL(5, 2),
        nullable=True
    )
    
    answer_status = Column(
        ENUM(AnswerStatus, name='answer_status_enum'),
        nullable=False,
        default=AnswerStatus.PENDING,
        index=True
    )
    
    is_user_edited = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    
    user_edited_answer = Column(
        Text,
        nullable=True
    )
    
    processing_started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    processing_completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    rfp_document = relationship(
        "RfpDocument",
        back_populates="questions"
    )
    
    document_matches = relationship(
        "QuestionDocumentMatch",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index('ix_extracted_questions_rfp_number', 'rfp_document_id', 'question_number'),
        Index('ix_extracted_questions_rfp_status', 'rfp_document_id', 'answer_status'),
        Index('ix_extracted_questions_type_status', 'question_type', 'answer_status'),
        Index('ix_extracted_questions_confidence', 'confidence_score'),
        Index('ix_extracted_questions_user_edited', 'is_user_edited'),
    )

    def __repr__(self) -> str:
        return f"<ExtractedQuestion(id={self.id}, rfp_document_id={self.rfp_document_id}, question_number={self.question_number}, status={self.answer_status})>"
