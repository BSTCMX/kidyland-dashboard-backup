"""
Rate limiting middleware using slowapi.

Provides rate limiting to prevent abuse and ensure fair usage.
"""
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Create limiter instance
# Uses client IP address for rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],  # Default: 1000 requests per hour per IP
    headers_enabled=True,  # Include rate limit info in response headers
)

# Rate limit configuration
# Can be customized per endpoint using @limiter.limit() decorator
RATE_LIMITS = {
    "default": "1000/hour",
    "auth": "10/minute",  # Stricter limits for auth endpoints
    "api": "500/hour",
    "exports": "20/hour",  # Strict limits for exports (resource-intensive)
}

