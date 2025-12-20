"""
Cache headers middleware.

Adds optimal cache headers to responses for better performance.
Different cache strategies for static files vs API responses.
"""
import logging
from fastapi import Request

logger = logging.getLogger(__name__)


async def add_cache_headers_middleware(request: Request, call_next):
    """
    Middleware to add cache headers to responses.
    
    Strategy:
    - Static files (JS, CSS, images): Long cache (1 year) with versioning
    - API responses: No cache (always fresh)
    - HTML files: Short cache (no-cache, must-revalidate)
    """
    response = await call_next(request)
    
    # Only add headers if not already set
    if "cache-control" in response.headers:
        return response
    
    path = request.url.path.lower()
    
    # Static assets - aggressive caching (browser cache)
    if any(path.endswith(ext) for ext in [".js", ".css", ".woff", ".woff2", ".ttf", ".eot", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp"]):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        response.headers["Vary"] = "Accept-Encoding"
    
    # HTML files - no cache (always revalidate)
    elif path.endswith(".html") or path == "/" or not path.startswith("/api"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    # API endpoints - no cache (always fresh data)
    elif path.startswith("/api") or path.startswith("/auth") or path.startswith("/exports") or path.startswith("/reports"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    # Default: short cache
    else:
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    
    return response

