"""
Integration tests for Sales endpoints.

Tests cover:
- POST /sales - Create sale
- GET /sales - List sales with filters
- GET /sales/{id} - Get specific sale
- GET /sales/today/list - Get today's sales
- POST /sales/{id}/extend - Extend timer
- POST /sales/{id}/print - Print ticket

Covers permissions, validations, business rules, and edge cases.
"""
import pytest
import uuid
from datetime import date, datetime, timedelta
from httpx import AsyncClient, ASGITransport
from main import app
from models.user import User
from models.sucursal import Sucursal
from models.service import Service
from models.product import Product
from models.sale import Sale
from models.timer import Timer
from database import get_db
from core.security import create_access_token


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def override_get_db(test_db):
    """Override get_db dependency for testing."""
    async def _get_db():
        yield test_db
    return _get_db


@pytest.fixture(autouse=True)
async def setup_dependencies(override_get_db):
    """Setup dependency overrides before each test."""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_auth_token(user: User) -> str:
    """
    Create JWT authentication token for a user.
    
    Args:
        user: User model instance to create token for
        
    Returns:
        JWT token string for Authorization header
    """
    return create_access_token(data={"sub": user.username})


# ============================================================================
# TEST CREATE SALE ENDPOINTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestCreateSaleEndpoints:
    """Tests for POST /sales endpoint."""
    
    async def test_create_sale_with_service_recepcion(
        self,
    test_db,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
        """Test creating a sale with service item as recepcion role."""
        token = get_auth_token(test_user)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_user.id),  # Required by schema, router will override with current_user
            "tipo": "service",
            "subtotal_cents": 1000,
            "discount_cents": 0,
            "total_cents": 1000,
            "payment_method": "cash",
            "child_name": "Test Child",  # Required for service sales
            "items": [
                {
                    "type": "service",
                    "ref_id": str(test_service.id),
                    "quantity": 1,
                    "unit_price_cents": 1000,
                    "subtotal_cents": 1000,
                    "duration_minutes": 60,
                }
            ],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
            
            if response.status_code != 200:
                error_detail = response.json() if response.status_code < 500 else {"detail": "Internal server error"}
                print(f"\n=== ERROR DEBUG ===")
                print(f"Status: {response.status_code}")
                print(f"Error detail: {error_detail}")
                print(f"Request payload keys: {list(sale_data.keys())}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json() if response.status_code < 500 else 'Internal error'}"
            data = response.json()
            assert "sale_id" in data
            assert "timer_id" in data
            assert data["timer_id"] is not None  # Timer should be created
            assert "sale" in data
            assert "timer" in data
    
    async def test_create_sale_with_service_kidibar(
        self,
        test_db,
        test_kidibar: User,
        test_sucursal: Sucursal,
        test_service: Service,
    ):
        """Test creating a sale with service item as kidibar role."""
        token = get_auth_token(test_kidibar)
        
        sale_data = {
                "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_kidibar.id),  # Required by schema, router will override
                "tipo": "service",
                "subtotal_cents": 1000,
                "discount_cents": 0,
                "total_cents": 1000,
                "payment_method": "cash",
                "child_name": "Test Child",
                "items": [
                    {
                        "type": "service",
                        "ref_id": str(test_service.id),
                        "quantity": 1,
                        "unit_price_cents": 1000,
                        "subtotal_cents": 1000,
                        "duration_minutes": 60,
                    }
                ],
            }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "sale_id" in data
            assert "timer_id" in data
    
    async def test_create_sale_forbidden_super_admin(
        self,
        test_db,
        test_superadmin: User,
        test_sucursal: Sucursal,
    ):
        """Test creating a sale is forbidden for super_admin role."""
        token = get_auth_token(test_superadmin)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_superadmin.id),  # Required by schema, router will override
            "tipo": "service",
            "subtotal_cents": 1000,
            "total_cents": 1000,
            "payment_method": "cash",
            "items": [],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        assert response.status_code == 403
    
    async def test_create_sale_forbidden_admin_viewer(
        self,
        test_db,
        test_admin_viewer: User,
        test_sucursal: Sucursal,
    ):
        """Test creating a sale is forbidden for admin_viewer role."""
        token = get_auth_token(test_admin_viewer)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_admin_viewer.id),  # Required by schema, router will override
            "tipo": "product",
            "subtotal_cents": 500,
            "total_cents": 500,
            "payment_method": "cash",
            "items": [],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        assert response.status_code == 403
    
    async def test_create_sale_forbidden_monitor(
        self,
        test_db,
        test_monitor: User,
        test_sucursal: Sucursal,
    ):
        """Test creating a sale is forbidden for monitor role."""
        token = get_auth_token(test_monitor)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_monitor.id),  # Required by schema, router will override
            "tipo": "product",
            "subtotal_cents": 500,
            "total_cents": 500,
            "payment_method": "cash",
            "items": [],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        assert response.status_code == 403
    
    async def test_create_sale_with_product_no_timer(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_product: Product,
    ):
        """Test creating a sale with product item does not create timer."""
        token = get_auth_token(test_user)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_user.id),  # Required by schema, router will override
            "tipo": "product",
            "subtotal_cents": 500,
            "discount_cents": 0,
            "total_cents": 500,
            "payment_method": "cash",
            "payer_name": "Test Customer",
            "items": [
                {
                    "type": "product",
                    "ref_id": str(test_product.id),
                    "quantity": 1,
                    "unit_price_cents": 500,
                    "subtotal_cents": 500,
                }
            ],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "sale_id" in data
        assert data["timer_id"] is None  # No timer for product sales
    
    async def test_create_sale_with_multiple_items(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_service: Service,
        test_product: Product,
    ):
        """Test creating a sale with multiple items (service + product)."""
        token = get_auth_token(test_user)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_user.id),  # Required by schema, router will override
            "tipo": "service",
            "subtotal_cents": 1500,
            "discount_cents": 0,
            "total_cents": 1500,
            "payment_method": "cash",
            "child_name": "Test Child",
            "items": [
                {
                    "type": "service",
                    "ref_id": str(test_service.id),
                    "quantity": 1,
                    "unit_price_cents": 1000,
                    "subtotal_cents": 1000,
                    "duration_minutes": 60,
                },
                {
                    "type": "product",
                    "ref_id": str(test_product.id),
                    "quantity": 1,
                    "unit_price_cents": 500,
                    "subtotal_cents": 500,
                }
            ],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "sale_id" in data
        assert data["timer_id"] is not None  # Timer created for service
    
    async def test_create_sale_with_start_delay(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_service: Service,
    ):
        """Test creating a sale with start_delay_minutes creates scheduled timer."""
        token = get_auth_token(test_user)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_user.id),  # Required by schema, router will override
            "tipo": "service",
            "subtotal_cents": 1000,
            "discount_cents": 0,
            "total_cents": 1000,
            "payment_method": "cash",
            "child_name": "Test Child",
            "items": [
                {
                    "type": "service",
                    "ref_id": str(test_service.id),
                    "quantity": 1,
                    "unit_price_cents": 1000,
                    "subtotal_cents": 1000,
                    "duration_minutes": 60,
                    "start_delay_minutes": 15,
                }
            ],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "timer_id" in data
        assert data["timer"] is not None
        # Timer should be scheduled, not active
        assert data["timer"]["status"] == "scheduled"
    
    async def test_create_sale_with_child_age(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_service: Service,
    ):
        """Test creating a sale with child_age is stored in timer."""
        token = get_auth_token(test_user)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_user.id),  # Required by schema, router will override
            "tipo": "service",
            "subtotal_cents": 1000,
            "discount_cents": 0,
            "total_cents": 1000,
            "payment_method": "cash",
            "child_name": "Test Child",
            "child_age": 5,
            "items": [
                {
                    "type": "service",
                    "ref_id": str(test_service.id),
                    "quantity": 1,
                    "unit_price_cents": 1000,
                    "subtotal_cents": 1000,
                    "duration_minutes": 60,
                }
            ],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "timer_id" in data
        assert data["timer"]["child_age"] == 5
    
    async def test_create_sale_with_payer_signature(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_service: Service,
    ):
        """Test creating a sale with payer_signature is stored."""
        token = get_auth_token(test_user)
        
        # Base64 encoded signature (mock)
        signature = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_user.id),  # Required by schema, router will override
            "tipo": "service",
            "subtotal_cents": 1000,
            "discount_cents": 0,
            "total_cents": 1000,
            "payment_method": "cash",
            "child_name": "Test Child",
            "payer_signature": signature,
            "items": [
                {
                    "type": "service",
                    "ref_id": str(test_service.id),
                    "quantity": 1,
                    "unit_price_cents": 1000,
                    "subtotal_cents": 1000,
                    "duration_minutes": 60,
                }
            ],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "sale_id" in data
            # Verify signature is stored (check via GET in same client context)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client2:
                sale_response = await client2.get(
                    f"/sales/{data['sale_id']}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert sale_response.status_code == 200
                sale_data_response = sale_response.json()
                assert sale_data_response["payer_signature"] == signature
    
    async def test_create_sale_requires_authentication(
        self,
        test_db,
    ):
        """Test creating a sale requires authentication."""
        sale_data = {
            "sucursal_id": str(uuid.uuid4()),
            "usuario_id": str(uuid.uuid4()),  # Required by schema, router will override (but test requires auth)
                "tipo": "product",
                "subtotal_cents": 500,
                "total_cents": 500,
                "payment_method": "cash",
                "items": [],
            }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                json=sale_data,
            )
        
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
    
    async def test_create_sale_empty_items(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
    ):
        """Test creating a sale with empty items list."""
        token = get_auth_token(test_user)
        
        sale_data = {
            "sucursal_id": str(test_sucursal.id),
            "usuario_id": str(test_user.id),  # Required by schema, router will override
            "tipo": "product",
            "subtotal_cents": 0,
            "discount_cents": 0,
            "total_cents": 0,
            "payment_method": "cash",
            "items": [],
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                json=sale_data,
            )
        
        # Empty items may be valid (e.g., discount-only sale)
        # Service should handle this appropriately
        assert response.status_code in [200, 400]


# ============================================================================
# TEST GET SALES ENDPOINTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestGetSalesEndpoints:
    """Tests for GET /sales endpoint."""
    
    async def test_get_sales_success_recepcion(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_sale: Sale,
    ):
        """Test getting sales as recepcion role."""
        token = get_auth_token(test_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    async def test_get_sales_with_filters(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_sale: Sale,
    ):
        """Test getting sales with filters (sucursal_id, start_date, end_date, tipo)."""
        token = get_auth_token(test_user)
        today = date.today()
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Filter by sucursal_id
            response = await client.get(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                params={"sucursal_id": str(test_sucursal.id)},
            )
            assert response.status_code == 200
            
            # Filter by date range
            response = await client.get(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "start_date": today.isoformat(),
                    "end_date": today.isoformat(),
                },
            )
            assert response.status_code == 200
            
            # Filter by tipo
            response = await client.get(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                params={"tipo": "service"},
            )
            assert response.status_code == 200
    
    async def test_get_sales_pagination(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
    ):
        """Test getting sales with pagination (skip, limit)."""
        token = get_auth_token(test_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sales",
                headers={"Authorization": f"Bearer {token}"},
                params={"skip": 0, "limit": 10},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


# ============================================================================
# TEST GET SALE ENDPOINTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestGetSaleEndpoints:
    """Tests for GET /sales/{id} endpoint."""
    
    async def test_get_sale_success(
        self,
        test_db,
        test_user: User,
        test_sale: Sale,
    ):
        """Test getting a specific sale."""
        token = get_auth_token(test_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/sales/{test_sale.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_sale.id)
    
    async def test_get_sale_not_found(
        self,
        test_db,
        test_user: User,
    ):
        """Test getting a non-existent sale."""
        token = get_auth_token(test_user)
        fake_id = str(uuid.uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/sales/{fake_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 404


# ============================================================================
# TEST GET TODAY SALES ENDPOINTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestGetTodaySalesEndpoints:
    """Tests for GET /sales/today/list endpoint."""
    
    async def test_get_today_sales_success(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_sale: Sale,
    ):
        """Test getting today's sales."""
        # Update sale date to today
        test_sale.created_at = datetime.combine(date.today(), datetime.min.time())
        await test_db.commit()
        
        token = get_auth_token(test_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sales/today/list",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# TEST EXTEND TIMER ENDPOINTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestExtendTimerEndpoints:
    """Tests for POST /sales/{id}/extend endpoint."""
    
    async def test_extend_timer_success(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_service: Service,
    ):
        """Test extending a timer successfully."""
        # Create sale with timer
        from tests.utils import factories
        
        sale = await factories.create_test_sale(
            db=test_db,
            sucursal_id=test_sucursal.id,
            user_id=test_user.id,
            total_cents=1000,
        )
        
        timer = await factories.create_test_timer(
            db=test_db,
            sale_id=sale.id,
            service_id=test_service.id,
        )
        
        await test_db.commit()
        await test_db.rollback()  # Clear transaction state
        
        token = get_auth_token(test_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/sales/{sale.id}/extend",
                headers={"Authorization": f"Bearer {token}"},
                params={"minutes": 30},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "end_at" in data
    
    async def test_extend_timer_forbidden_kidibar(
        self,
        test_db,
        test_kidibar: User,
        test_sucursal: Sucursal,
        test_service: Service,
    ):
        """Test extending a timer is forbidden for kidibar role."""
        from tests.utils import factories
        
        sale = await factories.create_test_sale(
            db=test_db,
            sucursal_id=test_sucursal.id,
            user_id=test_kidibar.id,
            total_cents=1000,
        )
        
        timer = await factories.create_test_timer(
            db=test_db,
            sale_id=sale.id,
            service_id=test_service.id,
        )
        
        await test_db.commit()
        await test_db.rollback()
        
        token = get_auth_token(test_kidibar)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/sales/{sale.id}/extend",
                headers={"Authorization": f"Bearer {token}"},
                params={"minutes": 30},
            )
        
        assert response.status_code == 403
    
    async def test_extend_timer_no_timer(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
    ):
        """Test extending a timer when sale has no timer."""
        from tests.utils import factories
        
        sale = await factories.create_test_sale(
            db=test_db,
            sucursal_id=test_sucursal.id,
            user_id=test_user.id,
            total_cents=500,
        )
        
        await test_db.commit()
        await test_db.rollback()
        
        token = get_auth_token(test_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/sales/{sale.id}/extend",
                headers={"Authorization": f"Bearer {token}"},
                params={"minutes": 30},
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "Timer not found" in data["detail"]


# ============================================================================
# TEST PRINT TICKET ENDPOINTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestPrintTicketEndpoints:
    """Tests for POST /sales/{id}/print endpoint."""
    
    async def test_print_ticket_success(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_service: Service,
    ):
        """Test printing a ticket successfully."""
        from tests.utils import factories
        
        # Create a sale with items
        sale = await factories.create_test_sale(
            db=test_db,
            sucursal_id=test_sucursal.id,
            user_id=test_user.id,
            total_cents=1000,
        )
        
        # Create a sale item for the ticket
        from models.sale_item import SaleItem
        sale_item = SaleItem(
            sale_id=sale.id,
            type="service",
            ref_id=test_service.id,
            quantity=1,
            unit_price_cents=1000,
            subtotal_cents=1000,
        )
        test_db.add(sale_item)
        await test_db.flush()
        await test_db.commit()
        await test_db.rollback()  # Clear transaction state for test
        
        token = get_auth_token(test_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/sales/{sale.id}/print",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        # Verify HTML content
        html = response.text
        assert "KIDYLAND" in html
        assert "Ticket de Venta" in html
        assert test_service.name in html  # Service name should be in ticket
        # Reception (service) ticket must show signature block
        assert "Firma del adulto responsable" in html
        assert "¡Gracias por su compra!" in html

    async def test_print_ticket_product_no_signature_block(
        self,
        test_db,
        test_user: User,
        test_sucursal: Sucursal,
        test_product: Product,
    ):
        """Product (kidibar) ticket must NOT show signature block; only thanks message."""
        from tests.utils import factories
        from models.sale_item import SaleItem

        sale = await factories.create_test_sale(
            db=test_db,
            sucursal_id=test_sucursal.id,
            user_id=test_user.id,
            tipo="product",
            total_cents=500,
        )
        sale_item = SaleItem(
            sale_id=sale.id,
            type="product",
            ref_id=test_product.id,
            quantity=1,
            unit_price_cents=500,
            subtotal_cents=500,
        )
        test_db.add(sale_item)
        await test_db.flush()
        await test_db.commit()
        await test_db.rollback()

        token = get_auth_token(test_user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/sales/{sale.id}/print",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        html = response.text
        assert "KIDYLAND" in html
        assert "¡Gracias por su compra!" in html
        assert "Firma del adulto responsable" not in html

    async def test_print_ticket_not_found(
        self,
        test_db,
        test_user: User,
    ):
        """Test printing a ticket for non-existent sale."""
        token = get_auth_token(test_user)
        fake_id = str(uuid.uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/sales/{fake_id}/print",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 404
