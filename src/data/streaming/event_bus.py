# ============================================================================
# File: src/data/streaming/event_bus.py
# Event bus for market data distribution
# ============================================================================

"""
Event bus for distributing market data events.

Allows multiple consumers to subscribe to market data streams.
"""

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio
import logging

from src.core.logger import main_logger

logger = main_logger


class EventType(Enum):
    """Market data event types."""
    NEW_BAR = "new_bar"
    NEW_TICK = "new_tick"
    BAR_UPDATE = "bar_update"
    CONNECTION_STATUS = "connection_status"


@dataclass
class MarketEvent:
    """Market data event."""
    event_type: EventType
    symbol: str
    account_id: int
    timestamp: datetime
    data: Any
    metadata: Dict[str, Any] = None


class EventBus:
    """
    Event bus for market data distribution.

    Features:
    - Multiple subscribers per event type
    - Account-aware routing
    - Async event delivery
    """

    def __init__(self):
        """Initialize event bus."""
        # subscribers[event_type][account_id] = [callbacks]
        self._subscribers: Dict[EventType, Dict[int, List[Callable]]] = {}

        # Statistics
        self.events_published = 0
        self.events_delivered = 0

    def subscribe(
            self,
            event_type: EventType,
            callback: Callable,
            account_id: Optional[int] = None
    ) -> None:
        """
        Subscribe to events.

        Args:
            event_type: Type of events to subscribe to
            callback: Function to call when event occurs
            account_id: Filter by account (None = all accounts)

        Example:
            >>> def on_new_bar(event: MarketEvent):
            ...     print(f"New bar: {event.data}")
            >>> bus.subscribe(EventType.NEW_BAR, on_new_bar, account_id=12345)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = {}

        # Use -1 for "all accounts"
        key = account_id if account_id is not None else -1

        if key not in self._subscribers[event_type]:
            self._subscribers[event_type][key] = []

        self._subscribers[event_type][key].append(callback)

        logger.info(
            f"Subscriber added: {event_type.value} "
            f"(account: {account_id or 'all'})"
        )

    def publish(self, event: MarketEvent) -> int:
        """
        Publish event to subscribers.

        Args:
            event: MarketEvent to publish

        Returns:
            Number of subscribers notified
        """
        self.events_published += 1

        if event.event_type not in self._subscribers:
            return 0

        subscribers_for_type = self._subscribers[event.event_type]

        # Get subscribers for this account and "all accounts" subscribers
        account_subscribers = subscribers_for_type.get(event.account_id, [])
        all_account_subscribers = subscribers_for_type.get(-1, [])

        all_subscribers = account_subscribers + all_account_subscribers

        # Notify all subscribers
        for callback in all_subscribers:
            try:
                callback(event)
                self.events_delivered += 1
            except Exception as e:
                logger.error(
                    f"Error in event subscriber: {e} "
                    f"(Event: {event.event_type.value})"
                )

        return len(all_subscribers)

    def unsubscribe_all(self, account_id: Optional[int] = None) -> None:
        """
        Unsubscribe all callbacks.

        Args:
            account_id: If specified, only unsubscribe for this account
        """
        if account_id is None:
            self._subscribers.clear()
            logger.info("All subscribers cleared")
        else:
            for event_type in self._subscribers:
                if account_id in self._subscribers[event_type]:
                    del self._subscribers[event_type][account_id]
            logger.info(f"Subscribers cleared for account {account_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        subscriber_count = sum(
            len(subs)
            for event_subs in self._subscribers.values()
            for subs in event_subs.values()
        )

        return {
            'events_published': self.events_published,
            'events_delivered': self.events_delivered,
            'subscriber_count': subscriber_count,
        }


# Global event bus
event_bus = EventBus()
