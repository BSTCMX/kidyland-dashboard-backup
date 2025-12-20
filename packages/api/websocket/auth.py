"""
WebSocket authentication helper.

Reuses authentication logic from utils.auth for WebSocket connections.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import WebSocket, WebSocketDisconnect
from models.user import User
from core.security import verify_token
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def authenticate_websocket(
    websocket: WebSocket,
    token: str
) -> Optional[User]:
    """
    Authenticate a WebSocket connection using JWT token.
    
    Args:
        websocket: WebSocket connection
        token: JWT token string
        
    Returns:
        User object if authenticated, None otherwise
        
    Note:
        Closes WebSocket connection if authentication fails.
    """
    try:
        # Verify token
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=1008, reason="Invalid token")
            return None
        
        # Extract username
        username = payload.get("sub")
        if not username:
            await websocket.close(code=1008, reason="Invalid token")
            return None
        
        # Get user from database (exclude soft-deleted users)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(
                    User.username == username,
                    User.deleted_at.is_(None)  # Exclude soft-deleted users
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                await websocket.close(code=1008, reason="User not found")
                return None
            
            return user
            
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=1011, reason="Authentication error")
        return None































