"""
Company model for the RFP platform
"""
from sqlalchemy import Column, String, Boolean, JSON, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Company(BaseModel):
    """Company model representing organizations using the platform"""
    __tablename__ = 'companies'

    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    api_key = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )
    
    meta_data = Column(
        JSON,
        nullable=True
    )

    # Relationships
    documents = relationship(
        "CompanyDocument",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    rfp_documents = relationship(
        "RfpDocument",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    report_generations = relationship(
        "ReportGeneration",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    # Additional indexes for performance
    __table_args__ = (
        Index('ix_companies_name_active', 'name', 'is_active'),
        Index('ix_companies_api_key_active', 'api_key', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', is_active={self.is_active})>"
