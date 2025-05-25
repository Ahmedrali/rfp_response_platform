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
- Multipart file upload with validation (PDF, DOCX max 10MB)
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

## Step 5: Document Processing Pipeline with RAG AI Integration

### Aider Prompt:
```
Integrate the existing RAG-based DocumentProcessor with the document processing pipeline:

EXISTING RAG DOCUMENTPROCESSOR:
Use the existing app/services/rag_document_processor.py which provides:

1. index_document(file_content: str, db_identifier: str) -> List[str]
   - Processes document using LangGraph workflow with chunking and vector embeddings
   - Stores chunks in ChromaDB with company isolation
   - Returns list of chunk IDs generated during indexing

2. extract_questions(file_content: str) -> ExtractionResult
   - Uses OpenAI/compatible LLM for intelligent question extraction
   - Returns ExtractionResult with questions list and confidence_score
   - Leverages AI for accurate question identification

3. answer_question(question: str, db_id: str) -> AnswerResult  
   - Generates answers using RAG (Retrieval-Augmented Generation)
   - Retrieves relevant chunks from company-specific vector store
   - Returns AnswerResult with answer, chunk_ids, confidence_score

DATA STRUCTURES (already defined in rag_document_processor.py):
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
1. Text extraction from PDF/DOCX files (PyPDF2, python-docx)
2. Use existing DocumentProcessor.index_document() with company-specific db_identifier
3. Store chunks with returned chunk_ids in database
4. Update document status throughout process
5. Background task processing with Celery
6. Status updates and error handling

ENVIRONMENT SETUP REQUIREMENTS:
- OpenAI API key or compatible endpoint (OPENAI_API_KEY, OPENAI_BASE_URL)
- Embedding model configuration (EMBEDDING_MODEL, CHAT_MODEL)
- ChromaDB vector store for persistent storage

Create:
- app/services/document_service.py - Uses existing RAG DocumentProcessor for text processing
- app/tasks/document_tasks.py - Celery tasks for background processing with RAG integration
- app/celery_app.py - Celery application configuration
- Endpoint to trigger document processing
- Environment variable configuration for AI models

The system will use production-ready RAG capabilities with LangGraph workflows and ChromaDB vector storage.
```

### Expected Outcome:
- Integration with production RAG DocumentProcessor
- Text extraction for PDF, Word, Excel files  
- Document chunking with vector embeddings stored in ChromaDB
- Celery integration for background processing
- Status tracking with database updates
- AI-powered question extraction and answer generation
- Company-isolated vector storage

### Validation Steps:
```bash
# 1. Set up environment variables for RAG
export OPENAI_API_KEY="your_openai_api_key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # or your compatible endpoint
export EMBEDDING_MODEL="text-embedding-ada-002"
export CHAT_MODEL="gpt-3.5-turbo"

# 2. Test RAG DocumentProcessor integration
python -c "
from app.services.rag_document_processor import DocumentProcessor
processor = DocumentProcessor()

# Test indexing with real RAG
chunks = processor.index_document('What are your security measures? How do you ensure quality control?', 'company_123')
print(f'Generated {len(chunks)} chunks with IDs: {chunks}')

# Test AI question extraction  
result = processor.extract_questions('What is your methodology? How do you ensure quality? What are your security measures?')
print(f'AI extracted {len(result.questions)} questions with {result.confidence_score:.2f} confidence')
print(f'Questions: {result.questions}')

# Test RAG answer generation
answer = processor.answer_question('What are your security measures?', 'company_123')
print(f'RAG Answer: {answer.answer[:100]}... (confidence: {answer.confidence_score:.2f})')
print(f'Source chunks: {answer.chunk_ids}')
"

# 3. Start Redis and Celery
redis-cli ping
celery -A app.celery_app worker --loglevel=info

# 4. Trigger document processing with RAG
curl -X POST http://localhost:8000/api/v1/companies/{company_id}/documents/{doc_id}/process \
  -H "Authorization: Bearer {api_key}"

# 5. Monitor RAG processing status
watch curl -X GET http://localhost:8000/api/v1/companies/{company_id}/documents/{doc_id}/status \
  -H "Authorization: Bearer {api_key}"

# 6. Verify ChromaDB collections and chunks
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collections = client.list_collections()
print(f'ChromaDB collections: {[c.name for c in collections]}')

if collections:
    collection = collections[0]
    count = collection.count()
    print(f'Collection {collection.name} has {count} documents')
"

# 7. Test company isolation in vector store
python -c "
from app.services.rag_document_processor import DocumentProcessor
processor = DocumentProcessor()

# Index for two different companies
chunks1 = processor.index_document('Company A security policies', 'company_a')
chunks2 = processor.index_document('Company B security policies', 'company_b')

# Test cross-company isolation
answer_a = processor.answer_question('What are the security policies?', 'company_a')
answer_b = processor.answer_question('What are the security policies?', 'company_b')

print(f'Company A answer sources: {answer_a.chunk_ids}')
print(f'Company B answer sources: {answer_b.chunk_ids}')
print('Chunk IDs should be different, confirming isolation')
"
```

---

## Step 6: RFP Upload & Question Extraction with RAG AI

### Aider Prompt:
```
Implement RFP document upload and question extraction using existing RAG DocumentProcessor:

POST /api/v1/companies/{company_id}/rfp/upload
- Upload RFP document (PDF/DOCX)
- Generate unique rfp_id
- Store file and create database record
- Return: {"success": true, "data": {"rfpId": "string", "filename": "string", "status": "PENDING"}}

GET /api/v1/companies/{company_id}/rfp/{rfp_id}/status
- Return RFP processing status with extraction_score and questions array
- Each question: {"questionId": "uuid", "questionNumber": int, "questionText": "string", "questionType": "string", "status": "ANSWERED", "answer": "string", "confidenceScore": float, "matchedDocuments": [array]}

RFP PROCESSING PIPELINE using RAG DocumentProcessor:
1. Extract text from RFP document using existing text extraction
2. Use DocumentProcessor.extract_questions(file_content) for AI-powered question extraction
3. For each extracted question:
   - Create ExtractedQuestion record in database
   - Use DocumentProcessor.answer_question(question, company_id) for RAG-based answers
   - Create QuestionDocumentMatches with actual chunk_ids from vector store
   - Set question status to "ANSWERED" with real confidence scores
4. Use real extraction_score from DocumentProcessor result
5. Update RFP status to "COMPLETED"

QUESTION-DOCUMENT MATCHING (RAG-powered):
- Use chunk_ids returned from DocumentProcessor.answer_question()
- Create QuestionDocumentMatch records with actual vector similarity scores
- Set relevance_score based on DocumentProcessor confidence_score
- Real document chunks retrieved from ChromaDB vector store
- Company-isolated matching using db_identifier

Create:
- app/routes/rfp.py - RFP endpoints
- app/services/rfp_service.py - RFP processing logic using RAG DocumentProcessor
- app/tasks/rfp_tasks.py - Background RFP processing with Celery and RAG
- AI-powered question extraction and answer generation
- Status tracking for RFP processing
- Real document matching with vector similarity scores

The system will provide intelligent question extraction and accurate answers using production RAG capabilities.
```

### Expected Outcome:
- RFP upload functionality
- AI-powered question extraction using RAG DocumentProcessor
- Intelligent answer generation with vector similarity matching
- Real question-document matching with chunk references from ChromaDB
- Complete RFP processing workflow with production AI capabilities
- Company-isolated vector storage and retrieval

### Validation Steps:
```bash
# 1. Upload RFP document
curl -X POST http://localhost:8000/api/v1/companies/{company_id}/rfp/upload \
  -H "Authorization: Bearer {api_key}" \
  -F "file=@sample_rfp.pdf"

# 2. Monitor RFP processing with AI
watch curl -X GET http://localhost:8000/api/v1/companies/{company_id}/rfp/{rfp_id}/status \
  -H "Authorization: Bearer {api_key}"

# 3. Verify AI-extracted questions with real answers
curl -X GET http://localhost:8000/api/v1/companies/{company_id}/rfp/{rfp_id}/status \
  -H "Authorization: Bearer {api_key}" | jq '.data.questions[0]'

# 4. Test RAG DocumentProcessor with RFP content
python -c "
from app.services.rag_document_processor import DocumentProcessor
processor = DocumentProcessor()

# Test with sample RFP content
rfp_content = '''
Request for Proposal: IT Services Contract

Section 1: Company Overview
Please provide detailed information about your company's experience and capabilities.

Section 2: Technical Requirements
1. What is your approach to data security and compliance?
2. How do you ensure system reliability and uptime?
3. What are your disaster recovery procedures?
4. Describe your quality assurance methodology.

Section 3: Project Management
5. What project management framework do you use?
6. How do you handle change requests and scope modifications?
'''

# AI-powered question extraction
result = processor.extract_questions(rfp_content)
print(f'AI extracted {len(result.questions)} questions:')
for i, question in enumerate(result.questions, 1):
    print(f'{i}. {question}')
print(f'Extraction confidence: {result.confidence_score:.2f}')

# Test RAG answer generation for first question
if result.questions:
    answer = processor.answer_question(result.questions[0], 'company_123')
    print(f'\\nRAG Answer for: {result.questions[0]}')
    print(f'Answer: {answer.answer[:200]}...')
    print(f'Source chunks: {answer.chunk_ids}')
    print(f'Confidence: {answer.confidence_score:.2f}')
"

# 5. Verify real vector similarity matching
python -c "
from app.models import ExtractedQuestion, QuestionDocumentMatch
from app.utils.database import get_session
session = next(get_session())

questions = session.query(ExtractedQuestion).all()
matches = session.query(QuestionDocumentMatch).all()

print(f'Questions extracted: {len(questions)}')
print(f'Document matches created: {len(matches)}')

if matches:
    match = matches[0]
    print(f'Sample match relevance score: {match.relevance_score}')
    print(f'Sample chunk IDs: {match.chunk_ids}')
"

# 6. Test company isolation in RFP processing
python -c "
from app.services.rag_document_processor import DocumentProcessor
processor = DocumentProcessor()

# Index documents for two companies
processor.index_document('Company A has ISO 27001 certification', 'company_a')
processor.index_document('Company B uses AWS security standards', 'company_b')

# Test isolation in question answering
question = 'What are your security certifications?'
answer_a = processor.answer_question(question, 'company_a')
answer_b = processor.answer_question(question, 'company_b')

print(f'Company A answer: {answer_a.answer[:100]}...')
print(f'Company B answer: {answer_b.answer[:100]}...')
print('Answers should reference different security approaches')
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
✅ **RAG-powered question extraction and answer generation**
✅ **Production-ready AI integration with ChromaDB vector storage**
✅ **Company-isolated document processing and retrieval**
✅ **Answer management system**
✅ **PDF report generation**
✅ **Background job processing with Celery**
✅ **Comprehensive testing suite**

The backend will be ready for frontend integration and provides production-ready AI capabilities with intelligent document processing, vector search, and retrieval-augmented generation.