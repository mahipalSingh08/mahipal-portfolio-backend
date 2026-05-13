"""Rate limiting configuration for the application."""
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

logger = logging.getLogger(__name__)


def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP from the request.
    
    In production (Render, Nginx, etc.), the request passes through a reverse proxy.
    The real client IP is available in the X-Forwarded-For header.
    Falls back to the direct socket IP if the header is not present.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For format: "client_ip, proxy1_ip, proxy2_ip"
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip

    # Fallback to the direct connection IP (works for localhost / direct connections)
    return get_remote_address(request)


def create_limiter() -> Limiter:
    """Create and configure the rate limiter with optional Redis backend."""
    from app.config import get_settings

    settings = get_settings()

    storage_uri = None
    if settings.redis_url:
        storage_uri = settings.redis_url
        logger.info("Rate limiter using Redis storage at %s", storage_uri)

    return Limiter(
        key_func=_get_client_ip,
        storage_uri=storage_uri,
    )


# Initialize rate limiter - can be imported by any module without circular imports
limiter = create_limiter()
