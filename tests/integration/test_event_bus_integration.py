from datetime import datetime, timezone
import pytest

from src.data.streaming.event_bus import (
    event_bus,
    EventType,
    MarketEvent,
)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

class EventRecorder:
    """Records received events."""
    def __init__(self):
        self.events = []

    def handler(self, event: MarketEvent):
        self.events.append(event)


@pytest.fixture(autouse=True)
def clean_event_bus():
    """
    Ensure a clean bus for every test.
    """
    event_bus.unsubscribe_all()
    event_bus.events_published = 0
    event_bus.events_delivered = 0
    yield
    event_bus.unsubscribe_all()


def create_event(
    event_type=EventType.NEW_BAR,
    symbol="EURUSD",
    account_id=123,
):
    return MarketEvent(
        event_type=event_type,
        symbol=symbol,
        account_id=account_id,
        timestamp=datetime.now(timezone.utc),
        data={"price": 1.2345},
    )


# ---------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------

def test_single_subscriber_receives_event():
    recorder = EventRecorder()

    event_bus.subscribe(
        event_type=EventType.NEW_BAR,
        callback=recorder.handler,
        account_id=123,
    )

    event = create_event(account_id=123)
    count = event_bus.publish(event)

    assert count == 1
    assert len(recorder.events) == 1
    assert recorder.events[0] == event


def test_multiple_subscribers_same_account():
    r1 = EventRecorder()
    r2 = EventRecorder()

    event_bus.subscribe(EventType.NEW_BAR, r1.handler, account_id=123)
    event_bus.subscribe(EventType.NEW_BAR, r2.handler, account_id=123)

    event = create_event(account_id=123)
    count = event_bus.publish(event)

    assert count == 2
    assert len(r1.events) == 1
    assert len(r2.events) == 1


def test_all_accounts_subscriber_receives_event():
    recorder = EventRecorder()

    event_bus.subscribe(
        event_type=EventType.NEW_BAR,
        callback=recorder.handler,
        account_id=None,  # all accounts
    )

    event = create_event(account_id=999)
    count = event_bus.publish(event)

    assert count == 1
    assert recorder.events[0].account_id == 999


def test_specific_and_all_account_subscribers():
    specific = EventRecorder()
    global_sub = EventRecorder()

    event_bus.subscribe(EventType.NEW_BAR, specific.handler, account_id=123)
    event_bus.subscribe(EventType.NEW_BAR, global_sub.handler, account_id=None)

    event = create_event(account_id=123)
    count = event_bus.publish(event)

    assert count == 2
    assert len(specific.events) == 1
    assert len(global_sub.events) == 1


def test_account_isolated_delivery():
    recorder = EventRecorder()

    event_bus.subscribe(EventType.NEW_BAR, recorder.handler, account_id=123)

    event = create_event(account_id=999)
    count = event_bus.publish(event)

    assert count == 0
    assert recorder.events == []


def test_event_type_isolated_delivery():
    recorder = EventRecorder()

    event_bus.subscribe(EventType.NEW_TICK, recorder.handler, account_id=123)

    event = create_event(event_type=EventType.NEW_BAR, account_id=123)
    count = event_bus.publish(event)

    assert count == 0
    assert recorder.events == []


def test_subscriber_exception_does_not_break_bus():
    recorder = EventRecorder()

    def bad_handler(event):
        raise RuntimeError("boom")

    event_bus.subscribe(EventType.NEW_BAR, bad_handler, account_id=123)
    event_bus.subscribe(EventType.NEW_BAR, recorder.handler, account_id=123)

    event = create_event(account_id=123)
    count = event_bus.publish(event)

    assert count == 2
    assert len(recorder.events) == 1


def test_unsubscribe_all_clears_subscribers():
    recorder = EventRecorder()

    event_bus.subscribe(EventType.NEW_BAR, recorder.handler, account_id=123)
    event_bus.unsubscribe_all()

    event = create_event(account_id=123)
    count = event_bus.publish(event)

    assert count == 0
    assert recorder.events == []


def test_statistics_are_correct():
    recorder = EventRecorder()

    event_bus.subscribe(EventType.NEW_BAR, recorder.handler, account_id=123)

    event = create_event(account_id=123)
    event_bus.publish(event)

    stats = event_bus.get_statistics()

    assert stats["events_published"] == 1
    assert stats["events_delivered"] == 1
    assert stats["subscriber_count"] == 1
