# SQLAlchemy Models for RFP Platform

This directory contains SQLAlchemy 2.0 models for the RFP platform. These models represent the database schema and provide the ORM layer for interacting with the database.

## Model Structure

### Base Classes

- `Base`: The SQLAlchemy declarative base class used for all models
- `BaseModel`: Abstract base class with common fields (id, created_at, updated_at)

### Core Models

- `Company`: Represents organizations using the platform
- `CompanyDocument`: Represents documents uploaded by companies
- `DocumentChunk`: Represents chunks of processed documents
- `RfpDocument`: Represents RFP documents uploaded for processing
- `ExtractedQuestion`: Represents questions extracted from RFP documents
- `QuestionDocumentMatch`: Represents matches between questions and company documents
- `ReportGeneration`: Represents PDF report generation requests

### Enums

- `ProcessingStatus`: PENDING, PROCESSING, COMPLETED, FAILED
- `AnswerStatus`: PENDING, PROCESSING, ANSWERED, FAILED
- `GenerationStatus`: PENDING, PROCESSING, COMPLETED, FAILED

## Database Structure

The models follow these relationships:

- A Company has many CompanyDocuments, RfpDocuments, and ReportGenerations
- A CompanyDocument has many DocumentChunks and can be matched to many ExtractedQuestions
- An RfpDocument has many ExtractedQuestions and ReportGenerations
- An ExtractedQuestion can match many CompanyDocuments through QuestionDocumentMatches

## Usage

```python
# Example: Creating a new company
from app.models import Company
from app.utils.dependencies import get_db_session

async def create_company(name: str, api_key: str):
    async for db in get_db_session():
        company = Company(name=name, api_key=api_key)
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company
```

## Working with Models

- All models inherit from `BaseModel` which provides common fields and methods
- Foreign key relationships are defined with proper cascading delete behavior
- Indexes are created for performance on frequently queried fields
- UUID primary keys are used for all models
- Enum fields use SQLAlchemy's ENUM type for enforcing valid values
- JSON fields are available for flexible metadata storage
