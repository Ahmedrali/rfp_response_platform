"""
RFP document model for the RFP platform
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Index, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.company_document import ProcessingStatus


class RfpDocument(BaseModel):
    """RFP document model representing uploaded RFP documents"""
    __tablename__ = 'rfp_documents'

    rfp_id = Column(
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
        ENUM(ProcessingStatus, name='rfp_processing_status_enum'),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True
    )
    
    extraction_score = Column(
        DECIMAL(5, 2),
        nullable=True
    )
    
    questions_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    processing_started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    processing_completed_at = Column(
        DateTime(timezone=True),
        nullable=True
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
        back_populates="rfp_documents"
    )
    
    questions = relationship(
        "ExtractedQuestion",
        back_populates="rfp_document",
        cascade="all, delete-orphan"
    )
    
    report_generations = relationship(
        "ReportGeneration",
        back_populates="rfp_document",
        cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index('ix_rfp_documents_company_status', 'company_id', 'processing_status'),
        Index('ix_rfp_documents_company_type', 'company_id', 'file_type'),
        Index('ix_rfp_documents_processing_times', 'processing_started_at', 'processing_completed_at'),
        Index('ix_rfp_documents_extraction_score', 'extraction_score'),
    )

    def __repr__(self) -> str:
        return f"<RfpDocument(id={self.id}, rfp_id='{self.rfp_id}', filename='{self.filename}', status={self.processing_status})>"
