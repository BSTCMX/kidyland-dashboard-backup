"""
Timer Broadcast Service - Background task for broadcasting timer updates via WebSocket.

Clean Architecture:
- Separates background task logic from WebSocket and timer services
- Uses existing TimerService and ConnectionManager
- Handles periodic polling and broadcasting
"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from services.timer_service import TimerService
from services.timer_alert_service import TimerAlertService
from websocket.manager import manager
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def periodic_timer_broadcast_task(interval_seconds: int = 5):
    """
    Background task that periodically polls active timers and broadcasts updates via WebSocket.
    
    This task:
    1. Polls every interval_seconds (default: 5 seconds)
    2. Gets active sucursales with WebSocket connections
    3. Queries active timers for each sucursal
    4. Broadcasts timer updates to connected WebSocket clients
    
    Args:
        interval_seconds: Seconds between polling iterations (default: 5)
    """
    logger.info(
        f"Starting periodic timer broadcast task: interval={interval_seconds}s"
    )
    
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            
            # Get active sucursales with WebSocket connections
            active_sucursales = list(manager.active_connections.keys())
            
            if not active_sucursales:
                # No active connections, skip iteration
                logger.debug(
                    "No active WebSocket connections, skipping broadcast",
                    extra={"active_sucursales_count": 0}
                )
                continue
            
            logger.debug(
                f"Broadcasting timer updates to {len(active_sucursales)} sucursales",
                extra={
                    "active_sucursales_count": len(active_sucursales),
                    "sucursales": list(active_sucursales)
                }
            )
            
            # Process each sucursal
            async with AsyncSessionLocal() as db:
                try:
                    for sucursal_id in active_sucursales:
                        try:
                            # Get active timers with time_left for this sucursal
                            timers_data = await TimerService.get_timers_with_time_left(
                                db=db,
                                sucursal_id=sucursal_id
                            )
                            
                            # Format and broadcast timer updates
                            update_message = {
                                "type": "timers_update",
                                "timers": timers_data,
                                "sucursal_id": sucursal_id
                            }
                            await manager.broadcast(sucursal_id, update_message)
                            
                            # Detect and broadcast timer alerts
                            alerts = await TimerAlertService.detect_timer_alerts(
                                db=db,
                                timers_data=timers_data,
                                sucursal_id=sucursal_id
                            )
                            
                            # Send each alert as a separate message
                            for alert in alerts:
                                alert_message = {
                                    **alert,  # Include all alert data (type, timer, alert_minutes, alerts_config)
                                    "sucursal_id": sucursal_id
                                }
                                await manager.broadcast(sucursal_id, alert_message)
                                
                                logger.debug(
                                    f"Broadcasted timer alert: timer_id={alert['timer']['id']}, alert_minutes={alert['alert_minutes']}",
                                    extra={
                                        "sucursal_id": sucursal_id,
                                        "timer_id": alert["timer"]["id"],
                                        "alert_minutes": alert["alert_minutes"],
                                        "message_type": "timer_alert"
                                    }
                                )
                            
                            # Log summary
                            logger.debug(
                                f"Broadcasted {len(timers_data)} timers and {len(alerts)} alerts to sucursal {sucursal_id}",
                                extra={
                                    "sucursal_id": sucursal_id,
                                    "timers_count": len(timers_data),
                                    "alerts_count": len(alerts),
                                    "message_types": ["timers_update", "timer_alert"] if alerts else ["timers_update"]
                                }
                            )
                            
                        except Exception as e:
                            # Log error but continue with other sucursales
                            logger.error(
                                f"Error broadcasting timers for sucursal {sucursal_id}: {e}",
                                exc_info=True
                            )
                            continue
                    
                finally:
                    # Ensure session is closed
                    await db.close()
                    
        except asyncio.CancelledError:
            logger.info("Periodic timer broadcast task cancelled")
            break
        except Exception as e:
            logger.error(
                f"Error in periodic timer broadcast task: {e}",
                exc_info=True
            )
            # Continue running even if one iteration fails
            # Wait a bit before retrying to avoid tight loop on persistent errors
            await asyncio.sleep(10)


