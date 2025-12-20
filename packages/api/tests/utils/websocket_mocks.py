"""
WebSocket mock utilities for testing.

Provides helpers to mock WebSocket connections and messages.
"""
from typing import Callable, Optional, Any
from unittest.mock import AsyncMock, MagicMock


class MockWebSocket:
    """Mock WebSocket connection for testing."""

    def __init__(self):
        self.receive_calls = []
        self.send_calls = []
        self.close_called = False
        self.accept_called = False
        self._receive_queue = []
        self._on_message: Optional[Callable] = None

    async def accept(self):
        """Mock accept connection."""
        self.accept_called = True

    async def receive_text(self) -> str:
        """Mock receive text message."""
        if self._receive_queue:
            return self._receive_queue.pop(0)
        return "{}"

    async def receive_json(self) -> dict:
        """Mock receive JSON message."""
        if self._receive_queue:
            return self._receive_queue.pop(0)
        return {}

    async def send_text(self, text: str):
        """Mock send text message."""
        self.send_calls.append(("text", text))

    async def send_json(self, data: dict):
        """Mock send JSON message."""
        self.send_calls.append(("json", data))
        if self._on_message:
            self._on_message(data)

    async def close(self):
        """Mock close connection."""
        self.close_called = True

    def queue_message(self, message: dict):
        """Queue a message to be received."""
        self._receive_queue.append(message)

    def set_on_message(self, callback: Callable):
        """Set callback for when messages are sent."""
        self._on_message = callback

    def get_sent_messages(self) -> list[dict]:
        """Get all sent JSON messages."""
        return [msg[1] for msg in self.send_calls if msg[0] == "json"]


def create_timer_update_message(
    timer_id: str,
    time_left: int,
    status: str = "active",
    child_name: Optional[str] = None,
) -> dict:
    """Create a timer update WebSocket message."""
    return {
        "type": "timers_update",
        "timers": [
            {
                "timer_id": timer_id,
                "time_left": time_left,
                "status": status,
                "child_name": child_name,
            }
        ],
    }


def create_timer_alert_message(
    timer_id: str,
    time_left: int,
    child_name: Optional[str] = None,
    alert_minutes: Optional[int] = None,
    alerts_config: Optional[list] = None,
) -> dict:
    """
    Create a timer alert WebSocket message.
    
    Args:
        timer_id: Timer ID
        time_left: Time left in minutes
        child_name: Optional child name
        alert_minutes: Which alert triggered (5, 10, or 15 minutes)
        alerts_config: Service alerts configuration
    """
    message = {
        "type": "timer_alert",
        "timer": {
            "timer_id": timer_id,
            "time_left": time_left,
            "status": "alert",
            "child_name": child_name,
        },
    }
    
    if alert_minutes is not None:
        message["alert_minutes"] = alert_minutes
    
    if alerts_config is not None:
        message["alerts_config"] = alerts_config
    
    return message


def create_stock_alert_message(
    product_id: str,
    product_name: str,
    stock_qty: int,
    threshold: int,
) -> dict:
    """Create a stock alert WebSocket message."""
    return {
        "type": "stock_alert",
        "product": {
            "product_id": product_id,
            "product_name": product_name,
            "stock_qty": stock_qty,
            "threshold_alert_qty": threshold,
        },
    }







