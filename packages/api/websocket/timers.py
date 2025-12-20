"""
WebSocket endpoint for real-time timer updates.
"""
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from websocket.manager import manager
from websocket.auth import authenticate_websocket

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/timers")
async def timer_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication"),
    sucursal_id: str = Query(..., description="Sucursal ID to subscribe to")
):
    """
    WebSocket endpoint for real-time timer updates.
    
    Clients connect to receive timer updates for a specific sucursal.
    Updates are sent every 5 seconds via background polling.
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
        sucursal_id: Sucursal ID to subscribe to
        
    Example client connection:
        ws://localhost:8000/ws/timers?token=<jwt_token>&sucursal_id=<uuid>
    """
    await websocket.accept()
    
    # Authenticate
    user = await authenticate_websocket(websocket, token)
    if not user:
        return  # WebSocket already closed by authenticate_websocket
    
    # Validate user has access to sucursal
    if user.sucursal_id and str(user.sucursal_id) != sucursal_id:
        await websocket.close(code=1008, reason="Access denied to this sucursal")
        return
    
    # Connect to manager
    await manager.connect(websocket, sucursal_id)
    
    try:
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client message (ping/pong or other)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle client messages if needed
                # For now, just echo or ignore
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.username}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Disconnect
        await manager.disconnect(websocket, sucursal_id)
































