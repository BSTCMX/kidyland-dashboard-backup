"""
WebSocket Connection Manager.

Thread-safe connection manager for WebSocket clients.
Maintains connections in-memory, grouped by sucursal_id.
"""
import asyncio
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections in-memory.
    
    Thread-safe for async operations using asyncio.Lock.
    Suitable for single-instance deployments.
    
    Note: For multi-zone/multi-instance deployments, consider Redis pub/sub.
    """
    
    def __init__(self):
        # Dict[sucursal_id, List[WebSocket]]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, sucursal_id: str):
        """
        Connect a WebSocket client for a specific sucursal.
        
        Args:
            websocket: WebSocket connection
            sucursal_id: Sucursal ID to group connections
        """
        async with self._lock:
            if sucursal_id not in self.active_connections:
                self.active_connections[sucursal_id] = []
            self.active_connections[sucursal_id].append(websocket)
            logger.info(
                f"WebSocket connected for sucursal {sucursal_id}. "
                f"Total connections: {len(self.active_connections[sucursal_id])}"
            )
    
    async def disconnect(self, websocket: WebSocket, sucursal_id: str):
        """
        Disconnect a WebSocket client.
        
        Args:
            websocket: WebSocket connection to disconnect
            sucursal_id: Sucursal ID
        """
        async with self._lock:
            if sucursal_id in self.active_connections:
                if websocket in self.active_connections[sucursal_id]:
                    self.active_connections[sucursal_id].remove(websocket)
                    logger.info(
                        f"WebSocket disconnected for sucursal {sucursal_id}. "
                        f"Remaining connections: {len(self.active_connections[sucursal_id])}"
                    )
                
                # Clean up empty lists
                if not self.active_connections[sucursal_id]:
                    del self.active_connections[sucursal_id]
    
    async def broadcast(self, sucursal_id: str, message: dict):
        """
        Broadcast a message to all connected clients for a sucursal.
        
        Args:
            sucursal_id: Sucursal ID to broadcast to
            message: Message dict to send (will be JSON serialized)
        """
        if sucursal_id not in self.active_connections:
            return
        
        # Get a copy of connections to avoid lock contention
        async with self._lock:
            connections = self.active_connections[sucursal_id].copy()
        
        # Send to all connections (outside lock to avoid blocking)
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if sucursal_id in self.active_connections:
                        if ws in self.active_connections[sucursal_id]:
                            self.active_connections[sucursal_id].remove(ws)
    
    async def broadcast_all(self, message: dict):
        """
        Broadcast a message to all connected clients across all sucursales.
        
        Args:
            message: Message dict to send
        """
        async with self._lock:
            all_sucursales = list(self.active_connections.keys())
        
        for sucursal_id in all_sucursales:
            await self.broadcast(sucursal_id, message)
    
    def get_connection_count(self, sucursal_id: str = None) -> int:
        """
        Get the number of active connections.
        
        Args:
            sucursal_id: Optional sucursal ID to filter by
            
        Returns:
            Number of active connections
        """
        if sucursal_id:
            return len(self.active_connections.get(sucursal_id, []))
        else:
            return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()
































