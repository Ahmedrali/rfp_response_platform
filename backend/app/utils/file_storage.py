"""
File storage utilities for secure document handling
"""
import os
import secrets
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
import structlog
import aiofiles

log = structlog.get_logger(__name__)

# Allowed file types and extensions
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/msword",  # .doc
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


class FileStorage:
    """Handles secure file storage operations"""
    
    def __init__(self, base_upload_dir: str = "uploads"):
        """
        Initialize file storage.
        
        Args:
            base_upload_dir: Base directory for file uploads
        """
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(exist_ok=True)
        
    def _get_company_dir(self, company_id: str) -> Path:
        """Get company-specific upload directory"""
        company_dir = self.base_upload_dir / company_id
        company_dir.mkdir(exist_ok=True)
        return company_dir
    
    def _validate_file_type(self, file: UploadFile) -> None:
        """
        Validate file type based on content type and extension.
        
        Args:
            file: FastAPI UploadFile object
            
        Raises:
            HTTPException: If file type is not allowed
        """
        # Check content type
        if file.content_type not in ALLOWED_MIME_TYPES:
            log.warning("Invalid file type", 
                       content_type=file.content_type,
                       filename=file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: PDF, DOCX, DOC"
            )
        
        # Check file extension
        if file.filename:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                log.warning("Invalid file extension", 
                           extension=file_extension,
                           filename=file.filename)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File extension not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
                )
    
    def _validate_file_size(self, file_size: int) -> None:
        """
        Validate file size.
        
        Args:
            file_size: Size of the file in bytes
            
        Raises:
            HTTPException: If file is too large
        """
        if file_size > MAX_FILE_SIZE:
            log.warning("File too large", 
                       file_size=file_size,
                       max_size=MAX_FILE_SIZE)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
    
    def _generate_secure_filename(self, original_filename: str) -> str:
        """
        Generate a secure filename with random prefix.
        
        Args:
            original_filename: Original file name
            
        Returns:
            Secure filename with random prefix
        """
        # Generate random prefix
        random_prefix = secrets.token_hex(16)
        
        # Get file extension
        file_extension = Path(original_filename).suffix.lower()
        
        # Create secure filename
        secure_filename = f"{random_prefix}{file_extension}"
        
        return secure_filename
    
    async def save_file(
        self, 
        file: UploadFile, 
        company_id: str,
        doc_id: str
    ) -> Tuple[str, int]:
        """
        Save uploaded file securely.
        
        Args:
            file: FastAPI UploadFile object
            company_id: Company ID for directory organization
            doc_id: Document ID for filename
            
        Returns:
            Tuple of (file_path, file_size)
            
        Raises:
            HTTPException: If validation fails or file cannot be saved
        """
        try:
            # Read file content to check size
            content = await file.read()
            file_size = len(content)
            
            # Validate file size
            self._validate_file_size(file_size)
            
            # Reset file pointer for validation
            await file.seek(0)
            
            # Validate file type
            self._validate_file_type(file)
            
            # Get company directory
            company_dir = self._get_company_dir(company_id)
            
            # Generate secure filename using doc_id
            file_extension = Path(file.filename).suffix.lower() if file.filename else ""
            secure_filename = f"{doc_id}{file_extension}"
            
            # Full file path
            file_path = company_dir / secure_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            log.info("File saved successfully", 
                    filename=file.filename,
                    secure_filename=secure_filename,
                    file_size=file_size,
                    company_id=company_id)
            
            return str(file_path), file_size
            
        except HTTPException:
            raise
        except Exception as e:
            log.error("Error saving file", 
                     filename=file.filename,
                     company_id=company_id,
                     error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file"
            )
    
    async def delete_file(self, file_path: str) -> None:
        """
        Delete file from storage.
        
        Args:
            file_path: Path to the file to delete
        """
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_path_obj.unlink()
                log.info("File deleted successfully", file_path=file_path)
            else:
                log.warning("File not found for deletion", file_path=file_path)
        except Exception as e:
            log.error("Error deleting file", 
                     file_path=file_path,
                     error=str(e))
            # Don't raise exception for file deletion errors
            # as the database record should still be cleaned up
    
    def get_file_info(self, filename: str) -> Optional[dict]:
        """
        Get file information including MIME type.
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with file information or None
        """
        if not filename:
            return None
            
        file_extension = Path(filename).suffix.lower()
        mime_type, _ = mimetypes.guess_type(filename)
        
        return {
            "extension": file_extension,
            "mime_type": mime_type,
            "is_allowed": file_extension in ALLOWED_EXTENSIONS
        }


# Global file storage instance
file_storage = FileStorage()
