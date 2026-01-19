"""
Database configuration with Neon connection via SQLAlchemy Async.

Connection strings:
- Local: Uses Neon Local Connect (postgresql+asyncpg://neon:npg@localhost:5432/<database_name>)
- Production: Uses Neon Serverless with SSL required (postgresql://...?sslmode=require)

Note: DATABASE_URL must use postgresql+asyncpg:// protocol for async operations.
asyncpg requires SSL to be configured via connect_args, not as URL parameter.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import settings
import ssl
import re

# Convert DATABASE_URL to async format if needed
# postgresql:// -> postgresql+asyncpg://
# postgres:// -> postgresql+asyncpg://
async_database_url = settings.DATABASE_URL

# Check if SSL is required (sslmode=require in URL)
ssl_required = "sslmode=require" in async_database_url.lower()

# Remove sslmode and channel_binding from URL (asyncpg doesn't accept them as URL params)
# They will be configured via connect_args instead
async_database_url = re.sub(r'[?&]sslmode=[^&]*', '', async_database_url)
async_database_url = re.sub(r'[?&]channel_binding=[^&]*', '', async_database_url)
# Clean up any trailing ? or & after removing params
async_database_url = re.sub(r'[?&]+$', '', async_database_url)

if async_database_url.startswith("postgresql://"):
    async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif async_database_url.startswith("postgres://"):
    async_database_url = async_database_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Configure SSL for asyncpg if required
connect_args = {
    # Force UTC timezone for all PostgreSQL sessions
    # This ensures that TIMESTAMP WITH TIME ZONE columns are returned in UTC
    # and all datetime calculations are consistent
    # asyncpg uses server_settings dictionary, not options string
    "server_settings": {
        "timezone": "UTC"
    }
}
if ssl_required:
    # asyncpg requires SSL context for secure connections
    # For Neon Serverless, we need SSL but can be more permissive in development
    # In production, use proper certificate verification
    ssl_context = ssl.create_default_context()
    # For development, we can disable hostname checking if certificates fail
    # This is safe for Neon as they use valid certificates
    # If certificate verification fails, use a more permissive context
    import os
    if os.getenv("ENVIRONMENT", "development") == "development":
        # Development: more permissive SSL (still encrypted, but no hostname check)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

# Create async engine with optimized connection pooling for Neon scale to zero
engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,  # Validate connections before use
    pool_size=2,  # Reduced from default 5 to minimize idle connections
    max_overflow=3,  # Maximum 5 total connections (2 + 3)
    pool_recycle=1800,  # Recycle connections every 30 minutes to allow scale to zero
    pool_timeout=30,  # Timeout after 30 seconds when getting connection from pool
    echo=False,  # Set to True for SQL query logging in development
    connect_args=connect_args if connect_args else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for getting async database session.
    
    Usage:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Model))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
