"""
Report generation model for the RFP platform
"""
from enum import Enum

from sqlalchemy import Column, String, DateTime, JSON, Index, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class GenerationStatus(str, Enum):
    """Generation status enum for reports"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReportGeneration(BaseModel):
    """Report generation model representing PDF report generation requests"""
    __tablename__ = 'report_generations'

    res_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    rfp_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey('rfp_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    generation_status = Column(
        ENUM(GenerationStatus, name='generation_status_enum'),
        nullable=False,
        default=GenerationStatus.PENDING,
        index=True
    )
    
    report_url = Column(
        String(500),
        nullable=True
    )
    
    generation_started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    generation_completed_at = Column(
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
    rfp_document = relationship(
        "RfpDocument",
        back_populates="report_generations"
    )
    
    company = relationship(
        "Company",
        back_populates="report_generations"
    )

    # Indexes for performance
    __table_args__ = (
        Index('ix_report_generations_rfp_status', 'rfp_document_id', 'generation_status'),
        Index('ix_report_generations_company_status', 'company_id', 'generation_status'),
        Index('ix_report_generations_generation_times', 'generation_started_at', 'generation_completed_at'),
    )

    def __repr__(self) -> str:
        return f"<ReportGeneration(id={self.id}, res_id='{self.res_id}', rfp_document_id={self.rfp_document_id}, status={self.generation_status})>"
