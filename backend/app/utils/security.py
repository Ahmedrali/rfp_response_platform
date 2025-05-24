import secrets
import bcrypt

def generate_api_key(length: int = 32) -> str:
    """
    Generates a secure, random API key.
    Args:
        length: The length of the hex string for the API key.
                A length of 32 will result in a 64-character hex string.
    Returns:
        A securely generated API key.
    """
    return secrets.token_hex(length)

def hash_api_key(api_key: str) -> str:
    """
    Hashes an API key using bcrypt.
    Args:
        api_key: The plain text API key.
    Returns:
        The hashed API key as a string.
    """
    hashed_bytes = bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Verifies a plain text API key against a stored bcrypt hash.
    Args:
        plain_api_key: The plain text API key to verify.
        hashed_api_key: The stored hashed API key.
    Returns:
        True if the key matches, False otherwise.
    """
    return bcrypt.checkpw(plain_api_key.encode('utf-8'), hashed_api_key.encode('utf-8'))
