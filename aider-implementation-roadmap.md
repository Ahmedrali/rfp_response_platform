# RFP Platform Backend - Aider Implementation Roadmap

## Overview
This roadmap provides a step-by-step approach to implementing the RFP Platform backend using Python FastAPI with Aider. Each step includes specific prompts, expected outcomes, and validation steps.

## Prerequisites
- Python 3.9-3.11 (3.11 recommended)
- PostgreSQL database
- Redis server
- Project structure already created

---

## Step 1: FastAPI Foundation & Configuration

### Aider Prompt:
```
Help me set up a FastAPI application foundation with the following requirements:

PROJECT STRUCTURE (already exists):
backend/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
├── main.py
├── requirements.txt
└── tests/

REQUIREMENTS:
- FastAPI 0.115.0 with SQLAlchemy 2.0.25 and Alembic 1.13.1
- PostgreSQL database connection with async support
- Environment configuration using pydantic-settings
- CORS middleware for frontend integration
- Basic health check endpoint
- Error handling middleware
- Logging configuration with structlog

Create:
1. main.py - FastAPI app with middleware and basic setup
2. app/utils/config.py - Environment settings with Pydantic
3. app/utils/database.py - SQLAlchemy async database setup
4. app/utils/dependencies.py - Common FastAPI dependencies
5. Basic logging configuration

Use the exact package versions from my requirements.txt.
```

### Expected Outcome:
- Working FastAPI application
- Database connection configuration
- Environment variable management
- CORS setup for frontend integration
- Health check endpoint

### Validation Steps:
```bash
# 1. Start development server
uvicorn main:app --reload

# 2. Check health endpoint
curl http://localhost:8000/health

# 3. Check API docs
curl http://localhost:8000/docs

# 4. Verify CORS headers
curl -H "Origin: https://ahmed.femtoid.com" http://localhost:8000/health
```

---

## Step 2: Database Models & Schema

### Aider Prompt:
```
Create SQLAlchemy 2.0 models for the RFP platform based on this schema:

COMPANIES TABLE:
- id (UUID, primary key)
- name (VARCHAR(255), unique, not null)
- api_key (VARCHAR(255), unique, not null)
- created_at, updated_at (TIMESTAMP)
- is_active (BOOLEAN, default True)
- metadata (JSON)

COMPANY_DOCUMENTS TABLE:
- id (UUID, primary key)
- doc_id (VARCHAR(255), unique, not null) -- Frontend reference
- company_id (UUID, foreign key to companies)
- filename, file_type, file_size, file_path (VARCHAR/INTEGER)
- processing_status (ENUM: PENDING, PROCESSING, COMPLETED, FAILED)
- processing_started_at, processing_completed_at (TIMESTAMP)
- chunk_count (INTEGER, default 0)
- metadata (JSON)
- error_message (TEXT)

DOCUMENT_CHUNKS TABLE:
- id (UUID, primary key)
- document_id (UUID, foreign key to company_documents)
- chunk_index (INTEGER)
- chunk_id (TEXT, not null)
- metadata (JSON)
- created_at (TIMESTAMP)

RFP_DOCUMENTS TABLE:
- id (UUID, primary key)
- rfp_id (VARCHAR(255), unique, not null)
- company_id (UUID, foreign key to companies)
- filename, file_type, file_size, file_path (VARCHAR/INTEGER)
- processing_status (ENUM: PENDING, PROCESSING, COMPLETED, FAILED)
- extraction_score (DECIMAL 5,2)
- questions_count (INTEGER, default 0)
- processing_started_at, processing_completed_at (TIMESTAMP)
- metadata (JSON)
- error_message (TEXT)

EXTRACTED_QUESTIONS TABLE:
- id (UUID, primary key)
- rfp_document_id (UUID, foreign key to rfp_documents)
- question_number (INTEGER)
- question_text (TEXT)
- question_type (VARCHAR 100)
- generated_answer (TEXT)
- confidence_score (DECIMAL 5,2)
- answer_status (ENUM: PENDING, PROCESSING, ANSWERED, FAILED)
- is_user_edited (BOOLEAN, default False)
- user_edited_answer (TEXT)
- processing_started_at, processing_completed_at (TIMESTAMP)
- created_at, updated_at (TIMESTAMP)

QUESTION_DOCUMENT_MATCHES TABLE:
- id (UUID, primary key)
- question_id (UUID, foreign key to extracted_questions)
- document_id (UUID, foreign key to company_documents)
- relevance_score (DECIMAL 5,2)
- chunk_ids (JSON array)
- created_at (TIMESTAMP)

REPORT_GENERATIONS TABLE:
- id (UUID, primary key)
- res_id (VARCHAR(255), unique)
- rfp_document_id (UUID, foreign key to rfp_documents)
- company_id (UUID, foreign key to companies)
- generation_status (ENUM: PENDING, PROCESSING, COMPLETED, FAILED)
- report_url (VARCHAR 500)
- generation_started_at, generation_completed_at (TIMESTAMP)
- metadata (JSON)
- error_message (TEXT)

Create:
- All SQLAlchemy models in app/models/ with proper relationships
- Base model class with common fields (id, created_at, updated_at)
- Proper indexes for performance
- Alembic configuration and initial migration
```

### Expected Outcome:
- Complete SQLAlchemy models with relationships
- Alembic configuration
- Initial database migration
- Proper foreign key constraints and indexes

### Validation Steps:
```bash
# 1. Initialize Alembic
alembic init alembic

# 2. Generate migration
alembic revision --autogenerate -m "Initial database schema"

# 3. Apply migration
alembic upgrade head

# 4. Verify tables in PostgreSQL
psql -d rfp_platform -c "\dt"

# 5. Test model imports
python -c "from app.models import Company, CompanyDocument; print('Models imported successfully')"
```

---

## Step 3: Authentication & Company Management

### Aider Prompt:
```
Implement company registration and authentication system with these endpoints:

POST /api/v1/companies/register
- Input: {"companyName": "string"}
- Check if company exists, generate unique API key if not
- Hash API key before storing in database
- Return: {"success": true, "data": {"companyId": "uuid", "companyName": "string", "apiKey": "string"}}
- Handle duplicate companies with 409 Conflict

POST /api/v1/companies/authenticate  
- Input: {"companyName": "string", "apiKey": "string"}
- Validate company name and hashed API key
- Return: {"success": true, "data": {"companyId": "uuid", "companyName": "string", "authenticated": true}}
- Return 401 for invalid credentials

REQUIREMENTS:
- API key generation using secrets module (32 character hex)
- API key hashing using bcrypt for database storage
- Authentication dependency for protecting routes
- Pydantic models for request/response validation
- Rate limiting using slowapi
- Proper HTTP status codes and error messages
- Company-scoped access control

Create:
- app/routes/auth.py - Authentication endpoints
- app/services/auth_service.py - Business logic for auth operations
- app/utils/security.py - API key generation and hashing utilities
- Pydantic schemas for requests/responses
- Authentication dependency for route protection
```

### Expected Outcome:
- Company registration endpoint
- Authentication endpoint
- API key generation and verification
- Route protection middleware
- Rate limiting on registration

### Validation Steps:
```bash
# 1. Register new company
curl -X POST http://localhost:8000/api/v1/companies/register \
  -H "Content-Type: application/json" \
  -d '{"companyName": "Test Company"}'

# 2. Test duplicate registration
curl -X POST http://localhost:8000/api/v1/companies/register \
  -H "Content-Type: application/json" \
  -d '{"companyName": "Test Company"}'

# 3. Test authentication
curl -X POST http://localhost:8000/api/v1/companies/authenticate \
  -H "Content-Type: application/json" \
  -d '{"companyName": "Test Company", "apiKey": "YOUR_API_KEY"}'

# 4. Test invalid authentication
curl -X POST http://localhost:8000/api/v1/companies/authenticate \
  -H "Content-Type: application/json" \
  -d '{"companyName": "Test Company", "apiKey": "invalid_key"}'
```

---

## Step 4: Document Upload & Management

### Aider Prompt:
```
Implement document management endpoints for company documents:

POST /api/v1/companies/{company_id}/documents
- Multipart file upload with validation (PDF, DOCX, XLSX, max 10MB)
- Generate unique doc_id, store file securely in uploads/ directory
- Create database record with PENDING status
- Return: {"success": true, "data": {"docId": "string", "filename": "string", "status": "PENDING"}}

GET /api/v1/companies/{company_id}/documents
- List all documents for the authenticated company
- Optional status filter query parameter
- Return: {"success": true, "data": {"documents": [array]}}

GET /api/v1/companies/{company_id}/documents/{doc_id}/status  
- Return processing status and metadata
- Include chunk_count, processing times when available

DELETE /api/v1/companies/{company_id}/documents/{doc_id}
- Remove document record and associated files
- Clean up chunks and file storage
- Return 204 No Content on success

REQUIREMENTS:
- File type validation (check MIME types and extensions)
- File size limits (10MB max)
- Secure file storage with organized directory structure
- Company-scoped access control (users can only access their documents)
- Proper error handling for file operations
- File cleanup on deletion

Create:
- app/routes/documents.py - Document management endpoints
- app/services/document_service.py - Business logic for document operations
- app/utils/file_storage.py - File handling utilities
- Proper validation and error handling
```

### Expected Outcome:
- Document upload with validation
- File storage system
- Document listing and status endpoints
- Document deletion with cleanup
- Company access control

### Validation Steps:
```bash
# 1. Upload document
curl -X POST http://localhost:8000/api/v1/companies/{company_id}/documents \
  -H "Authorization: Bearer {api_key}" \
  -F "file=@test_document.pdf"

# 2. List documents
curl -X GET http://localhost:8000/api/v1/companies/{company_id}/documents \
  -H "Authorization: Bearer {api_key}"

# 3. Check document status
curl -X GET http://localhost:8000/api/v1/companies/{company_id}/documents/{doc_id}/status \
  -H "Authorization: Bearer {api_key}"

# 4. Test file validation (invalid file type)
curl -X POST http://localhost:8000/api/v1/companies/{company_id}/documents \
  -H "Authorization: Bearer {api_key}" \
  -F "file=@test.txt"

# 5. Delete document
curl -X DELETE http://localhost:8000/api/v1/companies/{company_id}/documents/{doc_id} \
  -H "Authorization: Bearer {api_key}"
```

---

## Step 5: Document Processing Pipeline with Placeholder AI

### Aider Prompt:
```
Create a document processing pipeline with placeholder DocumentProcessor utility class:

DOCUMENTPROCESSOR INTERFACE (create placeholder implementation):
Create app/services/document_processor.py with these exact methods:

1. index_document(file_content: str, db_identifier: str) -> List[str]
   - Processes document by chunking and indexing 
   - Returns list of chunk IDs generated during indexing
   - Simulate processing with 1-2 second delay

2. extract_questions(file_content: str) -> ExtractionResult
   - Extracts questions from document with confidence score
   - Returns ExtractionResult with questions list and confidence_score
   - Use simple text parsing (lines ending with "?") plus fallback questions

3. answer_question(question: str, db_id: str) -> AnswerResult  
   - Generates answer using template responses
   - Returns AnswerResult with answer, chunk_ids, confidence_score
   - Use keyword matching for realistic responses

DATA STRUCTURES:
```python
@dataclasses.dataclass
class ExtractionResult:
    questions: List[str]
    confidence_score: float

@dataclasses.dataclass  
class AnswerResult:
    answer: str
    chunk_ids: List[str]
    confidence_score: float
```

DOCUMENT PROCESSING PIPELINE:
1. Text extraction from PDF/DOCX/XLSX files (PyPDF2, python-docx, openpyxl)
2. Text chunking with overlap (1000 chars, 200 overlap)
3. Use DocumentProcessor.index_document() to generate chunk IDs
4. Store chunks with returned chunk_ids in database
5. Update document status throughout process
6. Background task processing with Celery
7. Status updates and error handling

Create:
- app/services/document_processor.py - Placeholder implementation with realistic responses
- app/services/document_service.py - Uses DocumentProcessor for text processing
- app/utils/text_chunker.py - Text chunking utility
- app/tasks/document_tasks.py - Celery tasks for background processing
- app/celery_app.py - Celery application configuration
- Endpoint to trigger document processing

The placeholder allows full backend functionality while AI utility is developed separately.
```

### Expected Outcome:
- Placeholder DocumentProcessor with exact interface
- Text extraction for PDF, Word, Excel files  
- Document chunking with chunk ID generation
- Celery integration for background processing
- Status tracking with database updates
- Foundation for future AI integration

### Validation Steps:
```bash
# 1. Test DocumentProcessor placeholder
python -c "
from app.services.document_processor import DocumentProcessor
processor = DocumentProcessor()

# Test indexing
chunks = processor.index_document('Sample content here?', 'company_123')
print(f'Generated {len(chunks)} chunks: {chunks}')

# Test question extraction  
result = processor.extract_questions('What is your methodology? How do you ensure quality?')
print(f'Extracted {len(result.questions)} questions with {result.confidence_score:.2f} confidence')

# Test answer generation
answer = processor.answer_question('What are your security measures?', 'company_123')
print(f'Answer: {answer.answer[:100]}... (confidence: {answer.confidence_score:.2f})')
"

# 2. Start Redis and Celery
redis-cli ping
celery -A app.celery_app worker --loglevel=info

# 3. Trigger document processing
curl -X POST http://localhost:8000/api/v1/companies/{company_id}/documents/{doc_id}/process \
  -H "Authorization: Bearer {api_key}"

# 4. Monitor processing status
watch curl -X GET http://localhost:8000/api/v1/companies/{company_id}/documents/{doc_id}/status \
  -H "Authorization: Bearer {api_key}"

# 5. Check chunks created in database
python -c "
from app.models import DocumentChunk
from app.utils.database import get_session
session = next(get_session())
chunks = session.query(DocumentChunk).count()
print(f'Total chunks in database: {chunks}')
"
```

---

## Step 6: RFP Upload & Question Extraction with Placeholder AI

### Aider Prompt:
```
Implement RFP document upload and question extraction using DocumentProcessor placeholder:

POST /api/v1/companies/{company_id}/rfp/upload
- Upload RFP document (PDF/DOCX)
- Generate unique rfp_id
- Store file and create database record
- Return: {"success": true, "data": {"rfpId": "string", "filename": "string", "status": "PENDING"}}

GET /api/v1/companies/{company_id}/rfp/{rfp_id}/status
- Return RFP processing status with extraction_score and questions array
- Each question: {"questionId": "uuid", "questionNumber": int, "questionText": "string", "questionType": "string", "status": "ANSWERED", "answer": "string", "confidenceScore": float, "matchedDocuments": [array]}

RFP PROCESSING PIPELINE using DocumentProcessor:
1. Extract text from RFP document using existing text extraction
2. Use DocumentProcessor.extract_questions(file_content) to get questions
3. For each extracted question:
   - Create ExtractedQuestion record in database
   - Use DocumentProcessor.answer_question(question, company_id) to generate answer
   - Create placeholder QuestionDocumentMatches with chunk_ids
   - Set question status to "ANSWERED"
4. Calculate overall extraction_score from DocumentProcessor result
5. Update RFP status to "COMPLETED"

QUESTION-DOCUMENT MATCHING (Placeholder):
- Use chunk_ids returned from DocumentProcessor.answer_question()
- Create QuestionDocumentMatch records linking questions to company documents
- Set relevance_score based on DocumentProcessor confidence_score
- This provides realistic data structure for frontend

Create:
- app/routes/rfp.py - RFP endpoints
- app/services/rfp_service.py - RFP processing logic using DocumentProcessor
- app/tasks/rfp_tasks.py - Background RFP processing with Celery
- Question extraction and answer generation using placeholder AI
- Status tracking for RFP processing
- Realistic document matching for frontend integration

The system will work fully with placeholder AI, providing proper data structures and workflow.
```

### Expected Outcome:
- RFP upload functionality
- Question extraction using DocumentProcessor placeholder
- Answer generation with confidence scoring
- Question-document matching with chunk references
- Complete RFP processing workflow
- Foundation for AI integration

### Validation Steps:
```bash
# 1. Upload RFP document
curl -X POST http://localhost:8000/api/v1/companies/{company_id}/rfp/upload \
  -H "Authorization: Bearer {api_key}" \
  -F "file=@sample_rfp.pdf"

# 2. Monitor RFP processing
watch curl -X GET http://localhost:8000/api/v1/companies/{company_id}/rfp/{rfp_id}/status \
  -H "Authorization: Bearer {api_key}"

# 3. Verify questions extracted with answers
curl -X GET http://localhost:8000/api/v1/companies/{company_id}/rfp/{rfp_id}/status \
  -H "Authorization: Bearer {api_key}" | jq '.data.questions[0]'

# 4. Test DocumentProcessor integration
python -c "
from app.services.document_processor import DocumentProcessor
processor = DocumentProcessor()

# Test with sample RFP content
rfp_content = '''
1. What are your company's main capabilities?
2. How do you ensure data security?
3. What is your project methodology?
'''

result = processor.extract_questions(rfp_content)
print(f'Extracted: {result.questions}')
print(f'Confidence: {result.confidence_score}')

# Test answer generation
answer = processor.answer_question(result.questions[0], 'company_123')
print(f'Answer: {answer.answer[:100]}...')
print(f'Chunk IDs: {answer.chunk_ids}')
"

# 5. Verify database records created
python -c "
from app.models import ExtractedQuestion, QuestionDocumentMatch
from app.utils.database import get_session
session = next(get_session())
questions = session.query(ExtractedQuestion).count()
matches = session.query(QuestionDocumentMatch).count()
print(f'Questions: {questions}, Document matches: {matches}')
"
```

---

## Step 7: Answer Management & Updates

### Aider Prompt:
```
Implement answer editing and management system:

PUT /api/v1/companies/{company_id}/rfp/{rfp_id}/questions/{question_id}/answer
- Input: {"answer": "string"}
- Update question answer and mark as user_edited
- Validate question belongs to company's RFP
- Return: {"success": true, "data": {"questionId": "uuid", "updatedAnswer": "string", "isUserEdited": true, "updatedAt": "ISO8601"}}

FEATURES:
- Validate question ownership (belongs to company's RFP)
- Track edit history in metadata
- Update timestamps
- Maintain original generated answer
- Answer length validation (max 5000 characters)
- Proper error messages for invalid requests

QUESTION-DOCUMENT MATCHING (Placeholder):
- For now, create placeholder matches linking questions to company documents
- Set relevance_score to random values between 70-95
- This provides foundation for future AI-based matching

Create:
- Answer update endpoint with validation
- Edit tracking in question metadata
- Basic document matching for questions
- Proper access control and validation
```

### Expected Outcome:
- Answer update functionality
- Edit history tracking
- Question ownership validation
- Foundation for document matching

### Validation Steps:
```bash
# 1. Update an answer
curl -X PUT http://localhost:8000/api/v1/companies/{company_id}/rfp/{rfp_id}/questions/{question_id}/answer \
  -H "Authorization: Bearer {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"answer": "Updated answer content here"}'

# 2. Verify answer updated
curl -X GET http://localhost:8000/api/v1/companies/{company_id}/rfp/{rfp_id}/status \
  -H "Authorization: Bearer {api_key}" | jq '.data.questions[0].answer'

# 3. Test invalid question access
curl -X PUT http://localhost:8000/api/v1/companies/{wrong_company_id}/rfp/{rfp_id}/questions/{question_id}/answer \
  -H "Authorization: Bearer {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"answer": "Test"}'
```

---

## Step 8: Report Generation System

### Aider Prompt:
```
Implement report generation system for final RFP responses:

POST /api/v1/companies/{company_id}/rfp/{rfp_id}/generate-report
- Generate comprehensive RFP response document in PDF format
- Return: {"success": true, "data": {"resId": "string", "status": "PENDING", "estimatedCompletionTime": "ISO8601"}}

GET /api/v1/companies/{company_id}/reports/{res_id}/status  
- Return: {"success": true, "data": {"resId": "string", "status": "PROCESSING/COMPLETED/FAILED", "reportUrl": "string", "generationStartedAt": "ISO8601", "generationCompletedAt": "ISO8601"}}

REPORT GENERATION PIPELINE:
1. Collect all questions and final answers for the RFP
2. Create professional PDF using reportlab
3. Include company branding and formatting
4. Add question numbers, answers, and basic metadata
5. Store generated PDF in secure location
6. Return download URL with expiration

REPORT FEATURES:
- Professional PDF layout with headers/footers
- Question and answer formatting
- Company information in header
- Page numbering
- Basic styling and formatting
- File storage with organized naming

Create:
- app/routes/reports.py - Report generation endpoints
- app/services/report_service.py - PDF generation logic
- app/tasks/report_tasks.py - Background report generation
- PDF template using reportlab
- File storage for generated reports
```

### Expected Outcome:
- PDF report generation
- Professional formatting
- Background processing
- Secure file storage
- Download URL management

### Validation Steps:
```bash
# 1. Generate report
curl -X POST http://localhost:8000/api/v1/companies/{company_id}/rfp/{rfp_id}/generate-report \
  -H "Authorization: Bearer {api_key}"

# 2. Monitor report generation
watch curl -X GET http://localhost:8000/api/v1/companies/{company_id}/reports/{res_id}/status \
  -H "Authorization: Bearer {api_key}"

# 3. Download generated report
curl -X GET "{report_url}" -o downloaded_report.pdf

# 4. Verify PDF content
python -c "
import PyPDF2
with open('downloaded_report.pdf', 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    print(f'PDF has {len(pdf.pages)} pages')
"
```

---

## Step 9: Testing & Integration

### Aider Prompt:
```
Create comprehensive testing suite for the RFP platform:

TEST CATEGORIES:
1. Unit tests for services and utilities
2. Integration tests for API endpoints  
3. Authentication and authorization tests
4. File upload and processing tests
5. Database model tests

SPECIFIC TESTS:
- Company registration and authentication flow
- Document upload, processing, and deletion
- RFP upload and question extraction
- Answer updates and validation
- Report generation pipeline
- Error handling and edge cases
- Rate limiting tests

FIXTURES AND MOCKS:
- Test database with separate configuration
- Test file fixtures (sample PDFs, Word docs)
- Mock Celery tasks for testing
- Authentication test helpers
- Database transaction rollback for test isolation

Create:
- tests/test_auth.py - Authentication tests
- tests/test_documents.py - Document management tests
- tests/test_rfp.py - RFP processing tests
- tests/test_reports.py - Report generation tests
- tests/conftest.py - Pytest fixtures and configuration
- Test database configuration
- Sample test files

Include end-to-end workflow test that covers the complete user journey.
```

### Expected Outcome:
- Comprehensive test suite
- Test fixtures and sample data
- End-to-end workflow tests
- High test coverage
- Isolated test environment

### Validation Steps:
```bash
# 1. Run all tests
pytest -v

# 2. Run with coverage
pytest --cov=app --cov-report=html

# 3. Run specific test categories
pytest tests/test_auth.py -v
pytest tests/test_documents.py -v
pytest tests/test_rfp.py -v

# 4. Run end-to-end test
pytest tests/test_workflow.py -v

# 5. Check coverage report
open htmlcov/index.html
```

---

## Final Integration Test

### Complete Workflow Test:
```bash
# 1. Start all services
redis-server &
celery -A app.celery_app worker --loglevel=info &
uvicorn main:app --reload &

# 2. Run end-to-end test
python tests/integration/test_complete_workflow.py

# 3. Verify all endpoints work
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Success Criteria

After completing all steps, you should have:

✅ **Fully functional FastAPI backend**
✅ **Complete database schema with migrations**  
✅ **Authentication and authorization system**
✅ **Document upload and processing pipeline**
✅ **RFP analysis with basic question extraction**
✅ **Answer management system**
✅ **PDF report generation**
✅ **Background job processing with Celery**
✅ **Comprehensive testing suite**

The backend will be ready for frontend integration and provides a solid foundation that can be enhanced with AI capabilities in the future.