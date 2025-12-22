"""
Security headers middleware.

Adds essential security headers to all responses for protection against common attacks.
Follows Clean Architecture: Reusable middleware following existing patterns.

Security headers added:
- X-Frame-Options: Prevents clickjacking attacks
- X-Content-Type-Options: Prevents MIME type sniffing
- Referrer-Policy: Controls referrer information
- Strict-Transport-Security (HSTS): Enforces HTTPS (production only)
"""
import logging
from fastapi import Request
from core.config import settings

logger = logging.getLogger(__name__)


async def add_security_headers_middleware(request: Request, call_next):
    """
    Middleware to add security headers to responses.
    
    Clean Architecture: Reusable middleware following cache_headers pattern.
    Adds essential security headers without breaking existing functionality.
    
    Headers added:
    - X-Frame-Options: DENY (prevents clickjacking)
    - X-Content-Type-Options: nosniff (prevents MIME sniffing)
    - Referrer-Policy: strict-origin-when-cross-origin (controls referrer)
    - Strict-Transport-Security: Only in production with HTTPS
    
    Strategy:
    - Only add headers if not already set (allows overrides if needed)
    - HSTS only in production (requires HTTPS)
    - All headers are safe and won't break functionality
    """
    response = await call_next(request)
    
    # X-Frame-Options: Prevents clickjacking attacks
    # DENY: Page cannot be displayed in a frame
    if "x-frame-options" not in response.headers:
        response.headers["X-Frame-Options"] = "DENY"
    
    # X-Content-Type-Options: Prevents MIME type sniffing
    # nosniff: Browser must respect Content-Type header
    if "x-content-type-options" not in response.headers:
        response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Referrer-Policy: Controls referrer information
    # strict-origin-when-cross-origin: Full URL for same-origin, origin only for cross-origin HTTPS
    if "referrer-policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Strict-Transport-Security (HSTS): Enforces HTTPS
    # Only in production with HTTPS (requires valid SSL certificate)
    # max-age=31536000 = 1 year
    # includeSubDomains = Apply to all subdomains
    if settings.is_production and "strict-transport-security" not in response.headers:
        # Only add HSTS if request is HTTPS (check scheme)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

