"""
Document chunk model for the RFP platform
"""
from sqlalchemy import Column, Integer, Text, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DocumentChunk(BaseModel):
    """Document chunk model representing processed document chunks"""
    __tablename__ = 'document_chunks'

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey('company_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    chunk_index = Column(
        Integer,
        nullable=False,
        index=True
    )
    
    chunk_id = Column(
        Text,
        nullable=False,
        index=True
    )
    
    meta_data = Column(
        JSON,
        nullable=True
    )

    # Relationships
    document = relationship(
        "CompanyDocument",
        back_populates="chunks"
    )

    # Indexes for performance
    __table_args__ = (
        Index('ix_document_chunks_document_index', 'document_id', 'chunk_index'),
        Index('ix_document_chunks_chunk_id', 'chunk_id'),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
