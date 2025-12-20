"""
Integration tests for WebSocket endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient
from main import app
from models.user import User
from models.sucursal import Sucursal
from core.security import create_access_token


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.websocket
async def test_websocket_connection_requires_auth(test_db, test_sucursal: Sucursal):
    """Test that WebSocket connection requires authentication."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    # Try to connect without token
    with pytest.raises(Exception):  # WebSocket will close with error
        with client.websocket_connect(
            f"/ws/timers?sucursal_id={test_sucursal.id}"
        ) as websocket:
            pass
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.websocket
async def test_websocket_connection_with_valid_token(
    test_db,
    test_user: User,
    test_sucursal: Sucursal,
):
    """Test WebSocket connection with valid token."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create token
    token = create_access_token(data={"sub": test_user.username})
    
    client = TestClient(app)
    
    # Connect with valid token
    with client.websocket_connect(
        f"/ws/timers?token={token}&sucursal_id={test_sucursal.id}"
    ) as websocket:
        # Connection should be established
        # Receive ping or initial message
        data = websocket.receive_json()
        assert data is not None
    
    app.dependency_overrides.clear()
































