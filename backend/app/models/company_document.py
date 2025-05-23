"""
Company document model for the RFP platform
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ProcessingStatus(str, Enum):
    """Processing status enum for documents"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CompanyDocument(BaseModel):
    """Company document model representing uploaded documents"""
    __tablename__ = 'company_documents'

    doc_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    filename = Column(
        String(500),
        nullable=False
    )
    
    file_type = Column(
        String(100),
        nullable=False,
        index=True
    )
    
    file_size = Column(
        Integer,
        nullable=False
    )
    
    file_path = Column(
        String(1000),
        nullable=False
    )
    
    processing_status = Column(
        ENUM(ProcessingStatus, name='processing_status_enum'),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True
    )
    
    processing_started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    processing_completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    chunk_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    meta_data = Column(
        JSON,
        nullable=True
    )
    
    error_message = Column(
        Text,
        nullable=True
    )

    # Relationships
    company = relationship(
        "Company",
        back_populates="documents"
    )
    
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    question_matches = relationship(
        "QuestionDocumentMatch",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index('ix_company_documents_company_status', 'company_id', 'processing_status'),
        Index('ix_company_documents_company_type', 'company_id', 'file_type'),
        Index('ix_company_documents_processing_times', 'processing_started_at', 'processing_completed_at'),
    )

    def __repr__(self) -> str:
        return f"<CompanyDocument(id={self.id}, doc_id='{self.doc_id}', filename='{self.filename}', status={self.processing_status})>"
