"""
Timer Alert Service - Business logic for timer alert detection and processing.

Clean Architecture:
- Separates alert logic from timer service and broadcast service
- Uses existing Timer and Service models
- Handles alert detection based on alerts_config from services
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Set, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from models.timer import Timer
from models.service import Service

logger = logging.getLogger(__name__)


class TimerAlertService:
    """Service for detecting and processing timer alerts based on service configuration."""
    
    # In-memory tracking of sent alerts: Set of (timer_id, alert_minutes) tuples
    # This prevents duplicate alerts but resets on server restart (acceptable trade-off)
    _sent_alerts: Set[Tuple[str, int]] = set()
    
    # In-memory tracking of acknowledged alerts: Set of (timer_id, alert_minutes) tuples
    # When a user acknowledges an alert, it stops being broadcasted
    # Resets on server restart (acceptable trade-off)
    _acknowledged_alerts: Set[Tuple[str, int]] = set()
    
    @staticmethod
    def _get_alert_key(timer_id: str, alert_minutes: int) -> Tuple[str, int]:
        """Generate a unique key for an alert."""
        return (timer_id, alert_minutes)
    
    @staticmethod
    def _is_alert_sent(timer_id: str, alert_minutes: int) -> bool:
        """Check if an alert has already been sent for this timer and threshold."""
        key = TimerAlertService._get_alert_key(timer_id, alert_minutes)
        return key in TimerAlertService._sent_alerts
    
    @staticmethod
    def _mark_alert_sent(timer_id: str, alert_minutes: int) -> None:
        """Mark an alert as sent."""
        key = TimerAlertService._get_alert_key(timer_id, alert_minutes)
        TimerAlertService._sent_alerts.add(key)
    
    @staticmethod
    def _is_alert_acknowledged(timer_id: str, alert_minutes: int) -> bool:
        """Check if an alert has been acknowledged by a user."""
        key = TimerAlertService._get_alert_key(timer_id, alert_minutes)
        return key in TimerAlertService._acknowledged_alerts
    
    @staticmethod
    def acknowledge_alert(timer_id: str, alert_minutes: int) -> None:
        """
        Mark an alert as acknowledged.
        
        This prevents the alert from being broadcasted again.
        
        Args:
            timer_id: Timer ID
            alert_minutes: Alert threshold in minutes
        """
        key = TimerAlertService._get_alert_key(timer_id, alert_minutes)
        TimerAlertService._acknowledged_alerts.add(key)
        logger.info(
            f"Alert acknowledged: timer_id={timer_id}, alert_minutes={alert_minutes}",
            extra={"timer_id": timer_id, "alert_minutes": alert_minutes}
        )
    
    @staticmethod
    def clear_obsolete_alerts_for_timer(timer_id: str, new_time_left_minutes: int) -> None:
        """
        Remove alert tracking for thresholds that no longer apply after timer extension.
        
        When a timer is extended and time_left increases, alerts for thresholds
        that are now greater than the new time_left should be cleared so they
        can potentially trigger again if the timer reaches those thresholds.
        
        However, alerts for thresholds <= new_time_left should be kept as "sent"
        to prevent re-triggering alerts that already fired.
        
        Actually, wait - if we extend from 3 minutes to 63 minutes:
        - Alert for 5 minutes already fired (sent)
        - But now timer has 63 minutes, so alert for 5 minutes shouldn't fire again
        - We want to keep it as "sent" to prevent re-firing
        
        But if we extend from 3 to 63, and there's an alert for 60 minutes:
        - That alert hasn't fired yet
        - It should be able to fire when we reach 60 minutes
        
        So the logic is:
        - Remove from tracking any alert where threshold > new_time_left_minutes
        - Keep alerts where threshold <= new_time_left_minutes (already fired, don't re-fire)
        
        Actually, I think we want to clear ALL alerts for this timer, so that
        alerts can fire again based on the new time_left. This is simpler and more correct.
        
        Args:
            timer_id: Timer ID that was extended
            new_time_left_minutes: New time left in minutes after extension
        """
        # Remove all sent alerts for this timer (they can fire again if thresholds are met)
        TimerAlertService._sent_alerts = {
            (tid, alert_mins)
            for tid, alert_mins in TimerAlertService._sent_alerts
            if tid != timer_id
        }
        
        # Also clear acknowledged alerts (they were acknowledged for the old time, not the new)
        TimerAlertService._acknowledged_alerts = {
            (tid, alert_mins)
            for tid, alert_mins in TimerAlertService._acknowledged_alerts
            if tid != timer_id
        }
        
        logger.info(
            f"Cleared obsolete alerts for extended timer: timer_id={timer_id}, new_time_left={new_time_left_minutes}",
            extra={"timer_id": timer_id, "new_time_left_minutes": new_time_left_minutes}
        )
    
    @staticmethod
    def _should_cleanup_sent_alerts() -> bool:
        """
        Determine if we should cleanup old alert tracking.
        This prevents memory bloat from timers that no longer exist.
        """
        # Cleanup if we have more than 1000 tracked alerts
        return len(TimerAlertService._sent_alerts) > 1000
    
    @staticmethod
    def _cleanup_sent_alerts(active_timer_ids: Set[str]) -> None:
        """
        Remove alert tracking for timers that are no longer active.
        
        Args:
            active_timer_ids: Set of currently active timer IDs
        """
        # Remove alerts for timers that are no longer active
        TimerAlertService._sent_alerts = {
            (timer_id, alert_minutes)
            for timer_id, alert_minutes in TimerAlertService._sent_alerts
            if timer_id in active_timer_ids
        }
    
    @staticmethod
    async def detect_timer_alerts(
        db: AsyncSession,
        timers_data: List[Dict[str, Any]],
        sucursal_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect timer alerts based on alerts_config from services.
        
        Logic:
        1. For each timer, get its service and alerts_config
        2. Check if time_left_minutes matches any minutes_before in alerts_config
        3. If match and alert not sent, create alert message
        4. Track sent alerts to prevent duplicates
        
        Args:
            db: Database session
            timers_data: List of timer dictionaries with time_left_minutes
            sucursal_id: Optional sucursal ID for filtering (not used in detection, kept for API consistency)
            
        Returns:
            List of alert dictionaries ready for WebSocket broadcast
        """
        if not timers_data:
            return []
        
        alerts: List[Dict[str, Any]] = []
        active_timer_ids = {timer["id"] for timer in timers_data}
        
        # Cleanup old alert tracking periodically
        if TimerAlertService._should_cleanup_sent_alerts():
            TimerAlertService._cleanup_sent_alerts(active_timer_ids)
        
        # Get all service IDs from timers
        service_ids = {UUID(timer["service_id"]) for timer in timers_data}
        
        if not service_ids:
            return []
        
        # Load all services with their alerts_config
        services_query = select(Service).where(Service.id.in_(service_ids))
        services_result = await db.execute(services_query)
        services = {str(service.id): service for service in services_result.scalars().all()}
        
        # Process each timer
        for timer_data in timers_data:
            timer_id = timer_data["id"]
            service_id = timer_data["service_id"]
            time_left_minutes = timer_data.get("time_left_minutes", 0)
            
            # Skip if timer has no time left
            if time_left_minutes <= 0:
                continue
            
            # Get service and its alerts_config
            service = services.get(service_id)
            if not service or not service.alerts_config:
                continue
            
            # Check each alert configuration
            for alert_config in service.alerts_config:
                # Validate alert_config structure
                if not isinstance(alert_config, dict):
                    logger.warning(
                        f"Invalid alert_config format in service {service_id}: {alert_config}",
                        extra={"service_id": service_id, "alert_config": alert_config}
                    )
                    continue
                
                minutes_before = alert_config.get("minutes_before")
                if not isinstance(minutes_before, int):
                    continue
                
                # Check if timer time_left matches this alert threshold exactly
                # Alert triggers only when time_left == minutes_before (exact match)
                # This respects the admin dashboard configuration and prevents multiple alerts
                if time_left_minutes == minutes_before:
                    # Skip if alert has been acknowledged by a user
                    if TimerAlertService._is_alert_acknowledged(timer_id, minutes_before):
                        logger.debug(
                            f"Skipping acknowledged alert: timer_id={timer_id}, alert_minutes={minutes_before}",
                            extra={"timer_id": timer_id, "alert_minutes": minutes_before}
                        )
                        continue
                    
                    # Check if we've already sent this alert
                    if not TimerAlertService._is_alert_sent(timer_id, minutes_before):
                        # Create alert message
                        alert_message = {
                            "type": "timer_alert",
                            "timer": {
                                "id": timer_id,
                                "sale_id": timer_data.get("sale_id"),
                                "service_id": service_id,
                                "time_left_minutes": time_left_minutes,
                                "child_name": timer_data.get("child_name"),
                                "child_age": timer_data.get("child_age"),
                                "status": "alert",
                            },
                            "alert_minutes": minutes_before,
                            "alerts_config": service.alerts_config,  # Include full config for frontend
                        }
                        
                        alerts.append(alert_message)
                        
                        # Mark alert as sent
                        TimerAlertService._mark_alert_sent(timer_id, minutes_before)
                        
                        logger.info(
                            f"Timer alert detected: timer_id={timer_id}, alert_minutes={minutes_before}, time_left={time_left_minutes}",
                            extra={
                                "timer_id": timer_id,
                                "alert_minutes": minutes_before,
                                "time_left_minutes": time_left_minutes,
                                "service_id": service_id,
                            }
                        )
        
        return alerts

