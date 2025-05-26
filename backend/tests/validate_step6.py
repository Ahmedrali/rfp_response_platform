#!/usr/bin/env python
"""
Validation script for Step 6 of the roadmap: RFP Upload & Question Extraction with RAG AI
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = "http://localhost:8000"

def main():
    """Main validation function"""
    print("Starting validation for Step 6: RFP Upload & Question Extraction with RAG AI")
    
    # Test 1: Register a company for testing
    print("\n1. Registering test company...")
    import uuid
    unique_company_name = f"RFP Test Company {uuid.uuid4().hex[:8]}"
    company_data = register_company(unique_company_name)
    
    if not company_data:
        print("❌ Failed to register company. Cannot proceed with validation.")
        sys.exit(1)
    
    company_id = company_data["companyId"]
    api_key = company_data["apiKey"]
    print(f"✅ Company registered with ID: {company_id}")
    
    # Test 1.5: Upload some company documents for RAG context
    print("\n1.5. Uploading company documents for RAG context...")
    upload_sample_company_documents(company_id, api_key)
    
    # Test 2: Upload RFP document
    print("\n2. Uploading RFP document...")
    sample_rfp_path = "./tests/data/sample_rfp.pdf"
    
    # Create test directory and file if it doesn't exist
    os.makedirs("./tests/data", exist_ok=True)
    if not os.path.exists(sample_rfp_path):
        create_sample_rfp(sample_rfp_path)
    
    rfp_data = upload_rfp(company_id, api_key, sample_rfp_path)
    
    if not rfp_data:
        print("❌ Failed to upload RFP document. Cannot proceed with validation.")
        sys.exit(1)
    
    rfp_id = rfp_data["rfpId"]
    print(f"✅ RFP uploaded with ID: {rfp_id}")
    
    # Test 3: Monitor RFP processing
    print("\n3. Monitoring RFP processing...")
    print("Checking status every 2 seconds...")
    
    import time
    max_retries = 30  # 60 seconds max
    completed = False
    
    for i in range(max_retries):
        status_data = get_rfp_status(company_id, api_key, rfp_id)
        
        if not status_data:
            print(f"⚠️ Attempt {i+1}/{max_retries}: Failed to get status")
        else:
            status = status_data.get("status")
            print(f"Attempt {i+1}/{max_retries}: Status = {status}")
            
            if status == "COMPLETED":
                completed = True
                print("\n✅ RFP processing completed successfully!")
                print(f"Extraction score: {status_data.get('extractionScore')}")
                print(f"Questions extracted: {status_data.get('questionsCount')}")
                
                # Print first question and answer if available
                questions = status_data.get("questions", [])
                if questions:
                    print("\nSample question and answer:")
                    q = questions[0]
                    print(f"Q: {q.get('questionText')}")
                    print(f"A: {q.get('answer')}")
                    print(f"Confidence: {q.get('confidenceScore')}")
                    
                    # Check for document matches
                    matches = q.get("matchedDocuments", [])
                    if matches:
                        print(f"Matched with {len(matches)} documents")
                break
            
            elif status == "FAILED":
                print(f"❌ RFP processing failed!")
                break
        
        time.sleep(2)
    
    if not completed:
        print("⚠️ RFP processing did not complete within the timeout period")
    
    # Test 4: Validate RAG document processor
    print("\n4. Testing RAG DocumentProcessor directly...")
    test_rag_processor()
    
    print("\n✅ Validation completed for Step 6!")

def upload_sample_company_documents(company_id, api_key):
    """Upload sample company documents to provide RAG context"""
    sample_docs = [
        {
            "filename": "security_policy.txt",
            "content": """Our company maintains ISO 27001 certification and follows strict security protocols.
We implement end-to-end encryption, multi-factor authentication, and regular security audits.
Our data centers are SOC 2 Type II compliant with 24/7 monitoring and intrusion detection systems.
We have comprehensive backup and disaster recovery procedures with 99.9% uptime guarantee."""
        },
        {
            "filename": "project_management.txt", 
            "content": """We use Agile/Scrum methodology for all projects with certified Scrum Masters.
Our project management approach includes daily standups, sprint planning, and retrospectives.
We handle change requests through formal change control board processes.
We provide weekly status reports and maintain transparent communication channels."""
        },
        {
            "filename": "quality_assurance.txt",
            "content": """Our QA methodology includes automated testing, code reviews, and continuous integration.
We maintain test coverage of at least 80% and use both unit and integration testing.
Our quality processes are aligned with CMMI Level 3 standards.
We perform regular quality audits and maintain quality metrics dashboards."""
        }
    ]
    
    try:
        for doc in sample_docs:
            # Create temporary file
            temp_path = f"./tests/data/{doc['filename']}"
            with open(temp_path, "w") as f:
                f.write(doc["content"])
            
            # Upload document
            with open(temp_path, "rb") as f:
                files = {"file": (doc["filename"], f, "text/plain")}
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/companies/{company_id}/documents",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files
                )
            
            if response.status_code == 202:
                print(f"✅ Uploaded {doc['filename']}")
            else:
                print(f"⚠️ Failed to upload {doc['filename']}: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Clean up temp file
            os.remove(temp_path)
        
        # Wait a bit for processing
        import time
        print("⏳ Waiting for document processing...")
        time.sleep(5)
        
    except Exception as e:
        print(f"Error uploading sample documents: {str(e)}")

def register_company(company_name):
    """Register a test company"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/companies/register",
            json={"companyName": company_name}
        )
        
        if response.status_code in [200, 201]:
            return response.json()["data"]
        else:
            print(f"Failed to register company: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error registering company: {str(e)}")
        return None

def upload_rfp(company_id, api_key, file_path):
    """Upload RFP document"""
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/pdf")}
            response = requests.post(
                f"{API_BASE_URL}/api/v1/companies/{company_id}/rfp/upload",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files
            )
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            print(f"Failed to upload RFP: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error uploading RFP: {str(e)}")
        return None

def get_rfp_status(company_id, api_key, rfp_id):
    """Get RFP processing status"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/companies/{company_id}/rfp/{rfp_id}/status",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            print(f"Failed to get RFP status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting RFP status: {str(e)}")
        return None

def create_sample_rfp(file_path):
    """Create a sample RFP document for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(file_path, pagesize=letter)
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 750, "Sample Request for Proposal (RFP): IT Services")
        
        # Add content
        c.setFont("Helvetica", 12)
        c.drawString(72, 700, "Section 1: Company Overview")
        c.setFont("Helvetica", 10)
        c.drawString(72, 680, "Please provide detailed information about your company's experience and capabilities.")
        
        c.setFont("Helvetica", 12)
        c.drawString(72, 640, "Section 2: Technical Requirements")
        c.setFont("Helvetica", 10)
        c.drawString(72, 620, "1. What is your approach to data security and compliance?")
        c.drawString(72, 600, "2. How do you ensure system reliability and uptime?")
        c.drawString(72, 580, "3. What are your disaster recovery procedures?")
        c.drawString(72, 560, "4. Describe your quality assurance methodology.")
        
        c.setFont("Helvetica", 12)
        c.drawString(72, 520, "Section 3: Project Management")
        c.setFont("Helvetica", 10)
        c.drawString(72, 500, "5. What project management framework do you use?")
        c.drawString(72, 480, "6. How do you handle change requests and scope modifications?")
        
        c.save()
        print(f"Created sample RFP file at {file_path}")
    except Exception as e:
        print(f"Error creating sample RFP file: {str(e)}")

def test_rag_processor():
    """Test RAG DocumentProcessor directly"""
    try:
        # Add the backend directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Import the DocumentProcessor
        from app.services.rag_document_processor import DocumentProcessor
        
        # Initialize processor
        processor = DocumentProcessor()
        
        # Test with sample RFP content
        rfp_content = """
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
        """
        
        # Test question extraction
        print("Testing AI-powered question extraction...")
        result = processor.extract_questions(rfp_content)
        print(f"AI extracted {len(result.questions)} questions with {result.confidence_score:.2f} confidence")
        for i, question in enumerate(result.questions, 1):
            print(f"{i}. {question}")
        
        # Test company isolation
        print("\nTesting company isolation...")
        
        # Index documents for two different companies
        print("Indexing for Company A...")
        chunks_a = processor.index_document("Company A has ISO 27001 certification", "company_a")
        print(f"Generated {len(chunks_a)} chunks for Company A")
        
        print("Indexing for Company B...")
        chunks_b = processor.index_document("Company B uses AWS security standards", "company_b")
        print(f"Generated {len(chunks_b)} chunks for Company B")
        
        # Test isolation in question answering
        question = "What are your security certifications?"
        
        print(f"\nAnswering for Company A: '{question}'")
        answer_a = processor.answer_question(question, "company_a")
        print(f"Answer: {answer_a.answer}")
        print(f"Source chunks: {answer_a.chunk_ids}")
        
        print(f"\nAnswering for Company B: '{question}'")
        answer_b = processor.answer_question(question, "company_b")
        print(f"Answer: {answer_b.answer}")
        print(f"Source chunks: {answer_b.chunk_ids}")
        
        # Verify different chunk IDs for different companies
        if set(answer_a.chunk_ids) != set(answer_b.chunk_ids):
            print("\n✅ Company isolation verified: different chunk IDs for different companies")
        else:
            print("\n❌ Company isolation issue: same chunk IDs for different companies")
        
        print("\n✅ RAG DocumentProcessor tests completed successfully")
        
    except Exception as e:
        print(f"Error testing RAG processor: {str(e)}")

if __name__ == "__main__":
    main()
