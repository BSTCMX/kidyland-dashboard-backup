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


async def periodic_timer_broadcast_task(
    interval_seconds: int = 30,
    business_hours_start: int = 13,
    business_hours_end: int = 22,
    timezone_str: str = "America/Mexico_City"
):
    """
    Background task optimizado para broadcast de timers via WebSocket.
    
    Optimizaciones:
    - Intervalo aumentado a 30s (balance UX/costo)
    - Solo ejecuta en horario laboral (configurable)
    - Solo ejecuta si hay conexiones WebSocket activas
    - Timezone-aware (horarios en CDMX)
    
    Args:
        interval_seconds: Segundos entre polling (default: 30)
        business_hours_start: Hora inicio horario laboral en CDMX (default: 1 PM)
        business_hours_end: Hora fin horario laboral en CDMX (default: 10 PM)
        timezone_str: Timezone para horario laboral (default: America/Mexico_City)
    """
    import os
    from datetime import datetime, timezone as dt_timezone
    from zoneinfo import ZoneInfo
    
    # Obtener configuración de env vars (sin hardcodeo)
    interval_seconds = int(os.getenv("TIMER_BROADCAST_INTERVAL", str(interval_seconds)))
    business_hours_start = int(os.getenv("BUSINESS_HOURS_START", str(business_hours_start)))
    business_hours_end = int(os.getenv("BUSINESS_HOURS_END", str(business_hours_end)))
    timezone_str = os.getenv("BUSINESS_TIMEZONE", timezone_str)
    
    logger.info(
        f"Starting periodic timer broadcast task: "
        f"interval={interval_seconds}s, "
        f"business_hours={business_hours_start}-{business_hours_end} {timezone_str}"
    )
    
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            
            # OPTIMIZACIÓN 1: Verificar horario laboral en CDMX
            now_utc = datetime.now(dt_timezone.utc)
            now_local = now_utc.astimezone(ZoneInfo(timezone_str))
            current_hour = now_local.hour
            
            if current_hour < business_hours_start or current_hour >= business_hours_end:
                # Fuera de horario laboral, skip iteration
                # Esto permite que la DB se suspenda fuera de horario
                logger.debug(
                    f"Outside business hours ({current_hour}:00), skipping broadcast",
                    extra={
                        "current_hour": current_hour,
                        "business_hours": f"{business_hours_start}-{business_hours_end}"
                    }
                )
                continue
            
            # OPTIMIZACIÓN 2: Solo ejecutar si hay conexiones WebSocket activas
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


