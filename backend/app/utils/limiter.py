from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

log = structlog.get_logger(__name__)

def custom_key_func(request):
    """
    Custom key function for rate limiting.
    Uses X-Forwarded-For if present, otherwise falls back to remote address.
    This is important if your app is behind a reverse proxy.
    """
    # TODO: Ensure X-Forwarded-For is trusted if used, e.g., by checking request.scope['client']
    # For now, a simple check. In production, ensure your proxy sets this header reliably.
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # Take the first IP in the list (client's IP)
        ip = x_forwarded_for.split(",")[0].strip()
        log.debug("Rate limit key from X-Forwarded-For", ip=ip)
        return ip
    
    ip = get_remote_address(request)
    log.debug("Rate limit key from remote address", ip=ip)
    return ip


# Initialize the limiter
# You can set default_limits for all routes if desired, e.g., ["100/minute"]
# Specific routes can override this with their own @limiter.limit decorator.
limiter = Limiter(key_func=custom_key_func)

log.info("Rate limiter initialized.")
