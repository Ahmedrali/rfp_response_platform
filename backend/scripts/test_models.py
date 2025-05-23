#!/usr/bin/env python
"""
Script to test the SQLAlchemy models and database connection
"""
import asyncio
import os
import sys
import uuid

# Add the parent directory to the path so we can import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, CompanyDocument, ProcessingStatus
from app.utils.database import AsyncSessionLocal, create_tables


async def test_models():
    """Test the database models"""
    print("Testing database models...")
    
    # Create the tables if they don't exist (for development only)
    await create_tables()
    
    # Create a test session
    async with AsyncSessionLocal() as session:
        session: AsyncSession = session
        
        # Create a test company
        company = Company(
            name=f"Test Company {uuid.uuid4()}",
            api_key=f"test_api_key_{uuid.uuid4()}",
            is_active=True,
            metadata={"test": True}
        )
        session.add(company)
        await session.commit()
        await session.refresh(company)
        
        print(f"Created test company: {company}")
        
        # Create a test document
        document = CompanyDocument(
            doc_id=f"test_doc_{uuid.uuid4()}",
            company_id=company.id,
            filename="test_document.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/path/to/test_document.pdf",
            processing_status=ProcessingStatus.PENDING,
            metadata={"test": True}
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        
        print(f"Created test document: {document}")
        
        # Test query
        companies = await session.execute("SELECT * FROM companies")
        for company_row in companies:
            print(f"Found company in database: {company_row}")
        
        # Cleanup
        if input("Delete test data? (y/n): ").lower() == "y":
            await session.delete(document)
            await session.delete(company)
            await session.commit()
            print("Test data deleted.")


if __name__ == "__main__":
    asyncio.run(test_models())
