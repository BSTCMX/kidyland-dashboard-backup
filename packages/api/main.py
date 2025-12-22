"""
Kidyland API - Main FastAPI application.

Clean Architecture:
- Modular router organization
- Dependency injection for database and auth
- CORS and middleware configuration
- Health check endpoint
- Background tasks for periodic cleanup
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import routers - only include working ones for now
from routers import auth, users, catalog, reports, exports, permissions, sales, timers, operations
# Temporarily comment out routers with missing services
# from routers import admin
from websocket import timers as ws_timers

# Import cleanup service for background tasks
from services.cleanup_service import periodic_cleanup_task
from services.timer_broadcast_service import periodic_timer_broadcast_task
from services.timer_activation_service import periodic_timer_activation_task

# Import configuration (Clean Architecture: config in core)
from core.config import settings, get_cors_origins, get_static_files_dir, get_cors_headers
from database import get_db

# Import rate limiting (Clean Architecture: middleware in middleware package)
from middleware.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from middleware.bot_protection import bot_protection_middleware
from middleware.cache_headers import add_cache_headers_middleware
from middleware.static_files import CompressedStaticFiles

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    
    Handles startup and shutdown events:
    - Startup: Start background tasks (periodic cleanup, timer broadcast, timer activation)
    - Shutdown: Cancel background tasks gracefully
    """
    # Startup: Start background tasks
    logger.info("Starting background tasks...")
    cleanup_task = asyncio.create_task(periodic_cleanup_task(interval_hours=24, retention_days=30))
    timer_broadcast_task = asyncio.create_task(periodic_timer_broadcast_task(interval_seconds=5))
    timer_activation_task = asyncio.create_task(periodic_timer_activation_task(interval_seconds=15))
    logger.info("Background tasks started")
    
    yield
    
    # Shutdown: Cancel background tasks
    logger.info("Shutting down background tasks...")
    cleanup_task.cancel()
    timer_broadcast_task.cancel()
    timer_activation_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("Cleanup task cancelled successfully")
    try:
        await timer_broadcast_task
    except asyncio.CancelledError:
        logger.info("Timer broadcast task cancelled successfully")
    try:
        await timer_activation_task
    except asyncio.CancelledError:
        logger.info("Timer activation task cancelled successfully")
    logger.info("Background tasks shut down")


# Create FastAPI app instance with lifespan
app = FastAPI(
    title="Kidyland API",
    description="Backend API for Kidyland system",
    version="1.0.0",
    lifespan=lifespan,
)

# Initialize rate limiter (required by slowapi)
app.state.limiter = limiter

# Add bot protection middleware (before CORS to catch bots early)
@app.middleware("http")
async def bot_protection(request: Request, call_next):
    """Bot protection middleware - blocks known bots and crawlers."""
    return await bot_protection_middleware(request, call_next)

# Add cache headers middleware (after bot protection, before static files)
@app.middleware("http")
async def cache_headers(request: Request, call_next):
    """Cache headers middleware - adds optimal cache headers to responses."""
    return await add_cache_headers_middleware(request, call_next)

# Add security headers middleware (after cache headers, before CORS)
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Security headers middleware - adds essential security headers to responses."""
    from middleware.security_headers import add_security_headers_middleware
    return await add_security_headers_middleware(request, call_next)

# Configure CORS dynamically based on environment
# Clean Architecture: Configuration logic in core.config
# - Development: Allows all origins ["*"] for local development convenience
# - Production: Uses ALLOWED_ORIGINS env var (comma-separated list)
cors_origins = get_cors_origins()

# Note: allow_credentials=True is incompatible with allow_origins=["*"]
# In development, we use ["*"] so credentials must be False
# In production, if specific origins are used, credentials can be True if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # Set to False when using wildcard origins ["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# Global exception handlers to ensure CORS headers are always included
# Note: This handler is called first, but we'll override 404 handling below
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=get_cors_headers()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
        headers=get_cors_headers()
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with CORS headers."""
    logger.warning(
        f"Rate limit exceeded for IP {request.client.host if request.client else 'unknown'} on path {request.url.path}",
        extra={
            "ip": request.client.host if request.client else "unknown",
            "path": request.url.path,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "error": "rate_limit_exceeded"
        },
        headers=get_cors_headers({
            "Retry-After": str(exc.retry_after) if hasattr(exc, "retry_after") else "60",
        })
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler_spa(request: Request, exc: StarletteHTTPException):
    """Handle 404 errors - serve index.html for SPA routing if it's a frontend route."""
    # If it's a 404 and not an API route, serve index.html for SPA routing
    if exc.status_code == 404:
        path = request.url.path
        
        # Skip API routes, docs, and static file requests
        if (
            not path.startswith("/api") and
            not path.startswith("/auth") and
            not path.startswith("/docs") and
            not path.startswith("/openapi.json") and
            not path.startswith("/_app") and
            not path.startswith("/ffmpeg-core") and
            not "." in path.split("/")[-1]  # No file extension (likely a route)
        ):
            # Try to serve index.html for SPA routing
            static_dir = get_static_files_dir()
            static_path = Path(static_dir)
            index_html = static_path / "index.html"
            
            if index_html.exists():
                from fastapi.responses import FileResponse
                return FileResponse(
                    str(index_html),
                    headers={
                        "Cache-Control": "no-cache, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                    }
                )
    
    # For other HTTP exceptions, use the existing handler logic
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=get_cors_headers()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers and logging."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later."},
        headers=get_cors_headers()
    )

# Include routers - only working ones
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(catalog.router)
app.include_router(reports.router)
app.include_router(exports.router)
app.include_router(permissions.router)
app.include_router(sales.router)
app.include_router(timers.router)
app.include_router(operations.router)
# Temporarily commented out until services are implemented
# app.include_router(admin.router)
app.include_router(ws_timers.router)


@app.get("/health")
async def health_check(db = Depends(get_db)):
    """
    Health check endpoint with database connectivity verification.
    
    Returns:
        - 200: All systems healthy (API + DB)
        - 503: Service unhealthy (DB connection failed)
    """
    from sqlalchemy import text
    
    try:
        # Simple query to verify database connectivity
        # Using text() with no parameters is safe here (static query)
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
        
        return {
            "status": "healthy",
            "service": "kidyland-api",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed - database connection error: {e}", exc_info=True)
        # Return JSONResponse for error case to set proper status code
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "kidyland-api",
                "database": "disconnected",
                "error": "Database connection failed"
            },
            headers=get_cors_headers()
        )


# Mount static files AFTER all API routes
# This ensures API routes take precedence over static file serving
# Clean Architecture: Static files configuration in one place
static_dir = get_static_files_dir()
static_path = Path(static_dir)

# Only mount static files if directory exists (for development flexibility)
if static_path.exists() and static_path.is_dir():
    # Mount static files with html=True for SPA routing
    # html=True makes StaticFiles serve index.html for directories
    # SPA routing for unknown routes is handled by the 404 exception handler above
    app.mount(
        "/",
        CompressedStaticFiles(directory=str(static_path), html=True),
        name="static"
    )
    logger.info(f"Static files mounted from: {static_dir}")
else:
    logger.warning(f"Static files directory not found: {static_dir}. Static files will not be served.")
