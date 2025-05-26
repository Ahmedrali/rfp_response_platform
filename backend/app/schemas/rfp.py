"""
Pydantic schemas for RFP endpoints
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RfpUploadResponse(BaseModel):
    """Response schema for RFP upload"""
    rfpId: str
    filename: str
    status: str


class MatchedDocument(BaseModel):
    """Schema for matched documents"""
    documentId: str
    filename: str
    relevanceScore: float
    chunkIds: List[str]


class ExtractedQuestionResponse(BaseModel):
    """Schema for extracted question"""
    questionId: str
    questionNumber: int
    questionText: str
    questionType: str
    status: str
    answer: Optional[str] = None
    confidenceScore: Optional[float] = None
    matchedDocuments: List[MatchedDocument]


class RfpStatusResponse(BaseModel):
    """Response schema for RFP status"""
    rfpId: str
    filename: str
    status: str
    extractionScore: Optional[float] = None
    questionsCount: int
    processingStartedAt: Optional[datetime] = None
    processingCompletedAt: Optional[datetime] = None
    questions: List[ExtractedQuestionResponse]


class ApiResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = True
    data: Optional[dict] = None
    error: Optional[str] = None
