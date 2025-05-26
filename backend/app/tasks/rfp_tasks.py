"""
Celery tasks for RFP processing
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import structlog

# Load environment variables first
env_path = Path(__file__).parents[3] / '.env'
load_dotenv(dotenv_path=env_path)

# Debug log environment variables
log = structlog.get_logger(__name__)
log.info(
    "Environment variables loaded in RFP tasks",
    openai_key=bool(os.getenv("OPENAI_API_KEY")),
    openai_base_url=os.getenv("OPENAI_BASE_URL"),
    chat_model=os.getenv("CHAT_MODEL"),
    embedding_model=os.getenv("EMBEDDING_MODEL")
)

from app.celery_app import celery_app
from app.models.rfp_document import RfpDocument
from app.services.rfp_service import RfpService

log = structlog.get_logger(__name__)


@celery_app.task(name="process_rfp_document")
def process_rfp_document(rfp_id: str):
    """
    Process an RFP document in the background using synchronous operations
    
    Args:
        rfp_id: RFP document ID
    """
    log.info("Starting RFP document processing", rfp_id=rfp_id)
    
    try:
        # Use synchronous database operations for Celery
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.utils.config import get_database_url
        
        # Create synchronous engine and session
        engine = create_engine(get_database_url().replace("postgresql+asyncpg://", "postgresql://"))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # Get RFP document
            rfp_document = session.query(RfpDocument).filter(RfpDocument.rfp_id == rfp_id).first()
            
            if not rfp_document:
                log.error("RFP document not found", rfp_id=rfp_id)
                return
            
            # Process RFP document synchronously
            rfp_service = RfpService()
            rfp_service.process_rfp_sync(rfp_document, session)
            
            log.info("RFP document processing completed", rfp_id=rfp_id)
            
    except Exception as e:
        log.error("Error processing RFP document", rfp_id=rfp_id, error=str(e))
        raise
