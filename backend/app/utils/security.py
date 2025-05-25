"""
Security utilities for API key generation and hashing
"""
import secrets
import bcrypt


def generate_api_key() -> str:
    """Generate a secure 32-character hexadecimal API key"""
    return secrets.token_hex(16)  # 16 bytes = 32 hex characters


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt"""
    # Convert string to bytes for bcrypt
    api_key_bytes = api_key.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(api_key_bytes, salt)
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    """Verify an API key against its hash"""
    try:
        # Convert inputs to bytes for bcrypt
        api_key_bytes = api_key.encode('utf-8')
        hashed_bytes = hashed_api_key.encode('utf-8')
        # Verify using bcrypt
        return bcrypt.checkpw(api_key_bytes, hashed_bytes)
    except Exception:
        return False
