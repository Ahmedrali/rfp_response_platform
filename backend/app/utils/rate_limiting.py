"""
Rate limiting configuration using slowapi
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
import structlog

log = structlog.get_logger(__name__)

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom rate limit exceeded handler
    """
    log.warning("Rate limit exceeded", 
               client_ip=get_remote_address(request),
               detail=str(exc.detail))
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded: {exc.detail}"
    )
