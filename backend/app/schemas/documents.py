"""
Document management schemas for request/response validation
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProcessingStatus(str, Enum):
    """Processing status enum for documents"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload"""
    docId: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    status: ProcessingStatus = Field(..., description="Processing status")


class DocumentListItem(BaseModel):
    """Document item in list response"""
    docId: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    fileType: str = Field(..., description="File type/extension")
    fileSize: int = Field(..., description="File size in bytes")
    status: ProcessingStatus = Field(..., description="Processing status")
    chunkCount: int = Field(default=0, description="Number of chunks processed")
    processingStartedAt: Optional[datetime] = Field(None, description="Processing start time")
    processingCompletedAt: Optional[datetime] = Field(None, description="Processing completion time")
    createdAt: datetime = Field(..., description="Document creation time")
    errorMessage: Optional[str] = Field(None, description="Error message if processing failed")


class DocumentListResponse(BaseModel):
    """Response schema for document listing"""
    documents: List[DocumentListItem] = Field(..., description="List of documents")


class DocumentStatusResponse(BaseModel):
    """Response schema for document status"""
    docId: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    fileType: str = Field(..., description="File type/extension")
    fileSize: int = Field(..., description="File size in bytes")
    status: ProcessingStatus = Field(..., description="Processing status")
    chunkCount: int = Field(default=0, description="Number of chunks processed")
    processingStartedAt: Optional[datetime] = Field(None, description="Processing start time")
    processingCompletedAt: Optional[datetime] = Field(None, description="Processing completion time")
    createdAt: datetime = Field(..., description="Document creation time")
    updatedAt: Optional[datetime] = Field(None, description="Last update time")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    errorMessage: Optional[str] = Field(None, description="Error message if processing failed")


# Wrapper response schemas
class DocumentUploadSuccessResponse(BaseModel):
    """Success response wrapper for document upload"""
    success: bool = True
    data: DocumentUploadResponse


class DocumentListSuccessResponse(BaseModel):
    """Success response wrapper for document list"""
    success: bool = True
    data: DocumentListResponse


class DocumentStatusSuccessResponse(BaseModel):
    """Success response wrapper for document status"""
    success: bool = True
    data: DocumentStatusResponse


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    detail: str = Field(..., description="Error message")
    errors: Optional[List[Any]] = Field(None, description="Detailed error information")
