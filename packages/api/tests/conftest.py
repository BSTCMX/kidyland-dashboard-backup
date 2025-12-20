"""
Pytest configuration and shared fixtures.

Enhanced with robust factories and utilities for comprehensive testing.
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
import uuid

# Set test environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")

# Now import app modules (they will use the env vars)
from database import Base, get_db
from models.user import User, UserRole
from models.sucursal import Sucursal
from models.service import Service
from models.product import Product
from models.package import Package
from models.sale import Sale
from models.timer import Timer
from models.day_start import DayStart
from core.security import get_password_hash

# Import test utilities
from tests.utils import factories
from tests.utils import jwt_helpers

# Test database URL (in-memory SQLite for speed, or PostgreSQL for integration)
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
# For integration tests with real PostgreSQL:
# TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/kidyland_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with SAVEPOINT support.
    
    Uses nested transactions (SAVEPOINT) to allow services that use
    db.begin() to work correctly even when fixtures have committed.
    
    Architecture:
    - Outer transaction at connection level (rolled back at test end)
    - Initial SAVEPOINT (nested transaction) for test operations
    - Event listener restarts SAVEPOINT after each commit
    - Services can use db.begin() which creates nested SAVEPOINTs
    """
    # Create async engine for testing
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
        poolclass=StaticPool if "sqlite" in TEST_DATABASE_URL else None,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Create connection with outer transaction
    async with engine.connect() as connection:
        # Start outer transaction (rolled back at test end for isolation)
        transaction = await connection.begin()
        
        # Create session bound to connection
        # Factories use flush() instead of commit(), so no transaction is started automatically
        # This allows services to use db.begin() without conflicts
        session = async_session(bind=connection)
        
        # Wrap db.begin() to use begin_nested() when there's already a transaction active
        # This allows get_current_user() to start a transaction, and services can still use db.begin()
        original_begin = session.begin
        original_commit = session.commit
        
        # Track if we're in a nested transaction
        _in_nested_transaction = False
        
        def begin_with_nested_fallback():
            """
            Begin transaction, using begin_nested() if there's already an active transaction.
            
            This allows get_current_user() to start a transaction, and services can still
            use db.begin() without conflicts by creating a SAVEPOINT.
            """
            nonlocal _in_nested_transaction
            if session.in_transaction():
                # Already in a transaction (e.g., from get_current_user())
                # Use begin_nested() to create a SAVEPOINT
                _in_nested_transaction = True
                return session.begin_nested()
            else:
                # No active transaction, use normal begin()
                _in_nested_transaction = False
                return original_begin()
        
        async def commit_with_nested_handling():
            """
            Commit transaction, but don't actually commit if we're in a nested transaction.
            
            When using begin_nested(), commit() closes the SAVEPOINT, which causes issues
            with refresh(). Instead, we flush() but don't commit, letting the context manager
            handle the commit when exiting.
            """
            nonlocal _in_nested_transaction
            if _in_nested_transaction and session.in_transaction():
                # In nested transaction, just flush() - don't commit
                # The context manager will handle the commit when exiting
                await session.flush()
            else:
                # Normal transaction, commit normally
                await original_commit()
                _in_nested_transaction = False
        
        # Replace methods with our wrappers
        session.begin = begin_with_nested_fallback
        session.commit = commit_with_nested_handling
        
        try:
            yield session
        finally:
            # Restore original begin method
            session.begin = original_begin
            # Rollback any pending changes
            try:
                await session.rollback()
            except Exception:
                pass
            # Rollback outer transaction (cleans up all changes)
            try:
                await transaction.rollback()
            except Exception:
                pass
            try:
                await session.close()
            except Exception:
                pass

    # Cleanup: Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ============================================================================
# USER FIXTURES (using factories)
# ============================================================================

@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user (recepcion role)."""
    return await factories.create_recepcion_user(
        db=test_db,
        username="testuser",
        password="TestPass123",
    )


@pytest.fixture
async def test_superadmin(test_db: AsyncSession) -> User:
    """Create a test super admin user."""
    return await factories.create_super_admin(
        db=test_db,
        username="superadmin",
        password="AdminPass123",
    )


@pytest.fixture
async def test_admin_viewer(test_db: AsyncSession) -> User:
    """Create a test admin viewer user."""
    return await factories.create_admin_viewer(
        db=test_db,
        username="adminviewer",
        password="ViewerPass123",
    )


@pytest.fixture
async def test_kidibar(test_db: AsyncSession) -> User:
    """Create a test kidibar user."""
    return await factories.create_kidibar_user(
        db=test_db,
        username="testkidibar",
        password="KidibarPass123",
    )


@pytest.fixture
async def test_monitor(test_db: AsyncSession) -> User:
    """Create a test monitor user."""
    return await factories.create_monitor_user(
        db=test_db,
        username="testmonitor",
        password="MonitorPass123",
    )


# ============================================================================
# SUCURSAL FIXTURES
# ============================================================================

@pytest.fixture
async def test_sucursal(test_db: AsyncSession) -> Sucursal:
    """Create a test sucursal."""
    return await factories.create_test_sucursal(
        db=test_db,
        name="Test Sucursal",
        address="Test Address",
    )


# ============================================================================
# CATALOG FIXTURES
# ============================================================================

@pytest.fixture
async def test_service(test_db: AsyncSession, test_sucursal: Sucursal) -> Service:
    """Create a test service."""
    return await factories.create_test_service(
        db=test_db,
        sucursal_id=test_sucursal.id,
        name="Test Service",
    )


@pytest.fixture
async def test_product(test_db: AsyncSession, test_sucursal: Sucursal) -> Product:
    """Create a test product."""
    return await factories.create_test_product(
        db=test_db,
        sucursal_id=test_sucursal.id,
        name="Test Product",
    )


@pytest.fixture
async def test_package(test_db: AsyncSession, test_sucursal: Sucursal) -> Package:
    """Create a test package."""
    return await factories.create_test_package(
        db=test_db,
        sucursal_id=test_sucursal.id,
        name="Test Package",
    )


# ============================================================================
# BUSINESS LOGIC FIXTURES
# ============================================================================

@pytest.fixture
async def test_sale(
    test_db: AsyncSession,
    test_sucursal: Sucursal,
    test_user: User,
) -> Sale:
    """Create a test sale."""
    return await factories.create_test_sale(
        db=test_db,
        sucursal_id=test_sucursal.id,
        user_id=test_user.id,
    )


@pytest.fixture
async def test_timer(
    test_db: AsyncSession,
    test_sale: Sale,
    test_service: Service,
) -> Timer:
    """Create a test timer."""
    return await factories.create_test_timer(
        db=test_db,
        sale_id=test_sale.id,
        service_id=test_service.id,
        duration_minutes=60,
    )


@pytest.fixture
async def test_day_start(
    test_db: AsyncSession,
    test_sucursal: Sucursal,
    test_user: User,
) -> DayStart:
    """Create a test day start."""
    return await factories.create_test_day_start(
        db=test_db,
        sucursal_id=test_sucursal.id,
        user_id=test_user.id,
        initial_cash_cents=10000,
    )


# ============================================================================
# JWT TOKEN FIXTURES
# ============================================================================

@pytest.fixture
def super_admin_token(test_superadmin: User) -> str:
    """Create JWT token for super admin."""
    return jwt_helpers.create_super_admin_token(
        user_id=str(test_superadmin.id),
        username=test_superadmin.username,
    )


@pytest.fixture
def admin_viewer_token(test_admin_viewer: User) -> str:
    """Create JWT token for admin viewer."""
    return jwt_helpers.create_admin_viewer_token(
        user_id=str(test_admin_viewer.id),
        username=test_admin_viewer.username,
    )


@pytest.fixture
def recepcion_token(test_user: User) -> str:
    """Create JWT token for recepcion."""
    return jwt_helpers.create_recepcion_token(
        user_id=str(test_user.id),
        username=test_user.username,
    )


@pytest.fixture
def kidibar_token(test_kidibar: User) -> str:
    """Create JWT token for kidibar."""
    return jwt_helpers.create_kidibar_token(
        user_id=str(test_kidibar.id),
        username=test_kidibar.username,
    )


@pytest.fixture
def monitor_token(test_monitor: User) -> str:
    """Create JWT token for monitor."""
    return jwt_helpers.create_monitor_token(
        user_id=str(test_monitor.id),
        username=test_monitor.username,
    )


@pytest.fixture
def expired_token(test_user: User) -> str:
    """Create an expired JWT token for testing."""
    return jwt_helpers.create_expired_jwt_token(
        user_id=str(test_user.id),
        username=test_user.username,
        role=test_user.role,
    )


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def auth_headers_super_admin(super_admin_token: str) -> dict:
    """Get auth headers for super admin."""
    return jwt_helpers.get_auth_headers(super_admin_token)


@pytest.fixture
def auth_headers_admin_viewer(admin_viewer_token: str) -> dict:
    """Get auth headers for admin viewer."""
    return jwt_helpers.get_auth_headers(admin_viewer_token)


@pytest.fixture
def auth_headers_recepcion(recepcion_token: str) -> dict:
    """Get auth headers for recepcion."""
    return jwt_helpers.get_auth_headers(recepcion_token)


@pytest.fixture
def auth_headers_kidibar(kidibar_token: str) -> dict:
    """Get auth headers for kidibar."""
    return jwt_helpers.get_auth_headers(kidibar_token)


@pytest.fixture
def auth_headers_monitor(monitor_token: str) -> dict:
    """Get auth headers for monitor."""
    return jwt_helpers.get_auth_headers(monitor_token)


# ============================================================================
# DEPENDENCY OVERRIDE FIXTURES
# ============================================================================

@pytest.fixture
def override_get_db(test_db: AsyncSession):
    """Override get_db dependency for testing."""
    async def _get_db():
        yield test_db
    return _get_db
