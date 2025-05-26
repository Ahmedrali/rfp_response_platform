# RFP Response Platform - Backend

An intelligent RFP (Request for Proposal) response automation platform that uses AI to analyze company documents and generate contextual responses to RFP questionnaires.

## 🚀 Features

- **Company Registration & Authentication** - API key-based authentication system
- **Document Management** - Upload and process company documents (PDF, Word, Excel)
- **AI-Powered RFP Analysis** - Automatic question extraction from RFP documents
- **Intelligent Response Generation** - RAG-based answer generation using company knowledge base
- **Real-time Processing** - Background task processing with status tracking
- **Professional Report Generation** - PDF reports with source attribution
- **Vector Search** - Semantic search for relevant document matching
- **Enterprise-Ready** - Multi-tenant architecture with company isolation

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

### 1. Python 3.9-3.11
```bash
# Check your Python version
python3 --version
# Should be 3.9, 3.10, or 3.11 (3.11 recommended)
# Note: Python 3.12+ not yet fully supported by all dependencies
```

### 2. PostgreSQL Database
```bash
# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows
# Download from: https://www.postgresql.org/download/windows/
```

### 3. Redis Server
```bash
# macOS (using Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server

# Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

### 4. OpenAI API Key
- Sign up at [OpenAI Platform](https://platform.openai.com/)
- Generate an API key
- Keep it secure for environment configuration

## 🛠️ Installation

### 1. Clone and Setup Project Structure
```bash
# Navigate to your project root (alongside frontend folder)
cd your-project

# Create backend directory
mkdir backend
cd backend

# Create directory structure
mkdir -p app/{models,routes,services,utils} tests
touch app/__init__.py app/models/__init__.py app/routes/__init__.py 
touch app/services/__init__.py app/utils/__init__.py tests/__init__.py
touch main.py .env.example .gitignore
```

### 2. Create Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify critical installations
pip list | grep fastapi
pip list | grep celery
pip list | grep openai
```

### 📌 **Important Version Notes:**
- **FastAPI 0.115.0+** - Latest stable with SQLAlchemy 2.0 support
- **OpenAI 1.6.1+** - Required for langchain-openai compatibility
- **Celery 5.5.2** - Latest stable with Python 3.11 support
- **ChromaDB 0.4.24** - Compatible with Python 3.11 (avoid 1.0+ for now)
- **SQLAlchemy 2.0.25** - Modern async support with Alembic 1.13+

## ⚙️ Configuration

### 1. Database Setup
```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE rfp_platform;
CREATE USER rfp_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE rfp_platform TO rfp_user;
\q
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
```env
# Database Configuration
DATABASE_URL=postgresql://rfp_user:your_secure_password@localhost:5432/rfp_platform

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_super_secret_key_here_min_32_characters

# Application Settings
ENVIRONMENT=development
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,https://ahmed.femtoid.com

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
UPLOAD_DIR=uploads/
```

### 3. Database Migration (After Aider Implementation)
```bash
# Initialize Alembic (only needed once)
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial database schema"

# Apply migrations
alembic upgrade head
```

## 🚀 Running the Application

### 1. Start Redis Server
```bash
# Make sure Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Start PostgreSQL
```bash
# Make sure PostgreSQL is running
pg_isready
# Should return: accepting connections
```

### 3. Start FastAPI Development Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Background Workers (In separate terminals)
```bash
# Terminal 1: Start Celery Worker
celery -A app.celery_app worker --loglevel=info

# Terminal 2: Start Celery Beat (for periodic tasks)
celery -A app.celery_app beat --loglevel=info

# Terminal 3: Monitor Celery Tasks (optional)
celery -A app.celery_app flower
```

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints

#### Authentication
```
POST /api/v1/companies/register
POST /api/v1/companies/authenticate
```

#### Document Management
```
POST /api/v1/companies/{company_id}/documents
GET  /api/v1/companies/{company_id}/documents
GET  /api/v1/companies/{company_id}/documents/{doc_id}/status
DELETE /api/v1/companies/{company_id}/documents/{doc_id}
```

#### RFP Processing
```
POST /api/v1/companies/{company_id}/rfp/upload
GET  /api/v1/companies/{company_id}/rfp/{rfp_id}/status
PUT  /api/v1/companies/{company_id}/rfp/{rfp_id}/questions/{question_id}/answer
```

#### Report Generation
```
POST /api/v1/companies/{company_id}/rfp/{rfp_id}/generate-report
GET  /api/v1/companies/{company_id}/reports/{res_id}/status
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest tests/test_auth.py -v
pytest tests/test_documents.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Test Database Setup
```bash
# Create test database
createdb rfp_platform_test

# Set test environment
export DATABASE_URL=postgresql://rfp_user:password@localhost:5432/rfp_platform_test
```

## 🔧 Development Workflow

### Code Quality
```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/

# Run pre-commit hooks
pre-commit run --all-files
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database (development only)
alembic downgrade base
alembic upgrade head
```

### Monitoring
```bash
# Check application health
curl http://localhost:8000/health

# Monitor Celery tasks
celery -A app.celery_app inspect active

# Redis monitoring
redis-cli monitor
```

## 📊 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── models/          # Database models
│   │   ├── __init__.py
│   │   ├── company.py
│   │   ├── document.py
│   │   └── rfp.py
│   ├── routes/          # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── documents.py
│   │   └── rfp.py
│   ├── services/        # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── document_service.py
│   │   ├── ai_service.py
│   │   └── vector_store.py
│   └── utils/           # Utilities
│       ├── __init__.py
│       ├── config.py
│       ├── database.py
│       └── dependencies.py
├── alembic/             # Database migrations
├── tests/               # Test files
├── uploads/             # File storage
├── main.py             # Application entry point
├── requirements.txt    # Dependencies
├── .env.example       # Environment template
└── README.md          # This file
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check PostgreSQL status
pg_isready
sudo systemctl status postgresql

# Check connection
psql -h localhost -U rfp_user -d rfp_platform
```

#### Redis Connection Error
```bash
# Check Redis status
redis-cli ping
sudo systemctl status redis-server

# Check Redis logs
sudo journalctl -u redis-server
```

#### OpenAI API Errors
```bash
# Verify API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check rate limits in logs
tail -f logs/app.log
```

#### File Upload Issues
```bash
# Check upload directory permissions
ls -la uploads/
chmod 755 uploads/

# Check disk space
df -h
```

### Performance Optimization

#### Database Optimization
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Analyze table statistics
ANALYZE companies;
ANALYZE company_documents;
```

#### Celery Optimization
```bash
# Monitor worker performance
celery -A app.celery_app inspect stats

# Scale workers
celery -A app.celery_app worker --concurrency=4
```

## 📝 License

This project is part of an educational assignment and is not intended for commercial use.

## 🤝 Contributing

This is an educational project. Please follow the assignment guidelines for any modifications.

## 📞 Support

For technical issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed correctly
3. Ensure environment variables are configured properly
4. Check application logs for detailed error messages

## 🔄 Development Status

- ✅ Project structure and dependencies
- ⏳ Database models and migrations (to be implemented with Aider)
- ⏳ Authentication system (to be implemented with Aider)
- ⏳ Document processing pipeline (to be implemented with Aider)
- ⏳ RFP analysis and AI integration (to be implemented with Aider)
- ⏳ Report generation system (to be implemented with Aider)
- ⏳ Testing suite (to be implemented with Aider)

Ready for Aider implementation! 🚀
ScreenShots:
<img width="1356" alt="Screenshot 2025-05-26 at 11 36 11 AM" src="https://github.com/user-attachments/assets/b2c151e3-f99b-4e5a-836c-407a87fcfd1a" />
<img width="1356" alt="Screenshot 2025-05-26 at 11 36 22 AM" src="https://github.com/user-attachments/assets/b137fcb5-a81c-4a71-89e8-cd6f8b799993" />
<img width="1356" alt="Screenshot 2025-05-26 at 11 36 32 AM" src="https://github.com/user-attachments/assets/cac588ca-3bbb-4954-96c9-c94cd499db9a" />
<img width="1356" alt="Screenshot 2025-05-26 at 11 36 47 AM" src="https://github.com/user-attachments/assets/ea855691-6f65-4d2e-b68d-5aea117af66c" />
<img width="1356" alt="Screenshot 2025-05-26 at 11 36 58 AM" src="https://github.com/user-attachments/assets/876be02b-df53-4e75-9546-123ce52cf277" />
<img width="1356" alt="Screenshot 2025-05-26 at 11 39 59 AM" src="https://github.com/user-attachments/assets/cf7760e2-2b11-4b4d-b51c-a0d9b634f20a" />
<img width="1356" alt="Screenshot 2025-05-26 at 2 10 00 PM" src="https://github.com/user-attachments/assets/5b418eab-7c9a-4065-8f01-2aa9755ea6f0" />
<img width="1356" alt="Screenshot 2025-05-26 at 2 10 18 PM" src="https://github.com/user-attachments/assets/2e100989-aed1-4474-9655-43f9b0f6f47f" />

