"""
Question document match model for the RFP platform
"""
from sqlalchemy import Column, JSON, Index, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class QuestionDocumentMatch(BaseModel):
    """Question document match model representing relevance between questions and documents"""
    __tablename__ = 'question_document_matches'

    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey('extracted_questions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey('company_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    relevance_score = Column(
        DECIMAL(5, 2),
        nullable=False
    )
    
    chunk_ids = Column(
        JSON,
        nullable=False
    )

    # Relationships
    question = relationship(
        "ExtractedQuestion",
        back_populates="document_matches"
    )
    
    document = relationship(
        "CompanyDocument",
        back_populates="question_matches"
    )

    # Indexes for performance
    __table_args__ = (
        Index('ix_question_document_matches_question_relevance', 'question_id', 'relevance_score'),
        Index('ix_question_document_matches_document_relevance', 'document_id', 'relevance_score'),
        Index('ix_question_document_matches_question_document', 'question_id', 'document_id'),
    )

    def __repr__(self) -> str:
        return f"<QuestionDocumentMatch(id={self.id}, question_id={self.question_id}, document_id={self.document_id}, relevance_score={self.relevance_score})>"
