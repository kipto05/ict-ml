import pandas as pd
import pytest
from datetime import datetime, timezone

from src.data.streaming.mt5_streamer import MT5Streamer
from src.data.models import MarketBar
from src.data.streaming.event_bus import EventType


# ------------------------------------------------------------------
# FIXTURES
# ------------------------------------------------------------------

@pytest.fixture
def fake_mt5_connector(mocker):
    mt5 = mocker.Mock()

    index = pd.date_range(
        start="2024-01-01 10:00:00",
        periods=1,
        freq="min",
        tz=timezone.utc
    )

    df = pd.DataFrame(
        {
            "open": [1.1000],
            "high": [1.1050],
            "low": [1.0950],
            "close": [1.1020],
            "tick_volume": [100],
            "spread": [10],
        },
        index=index
    )

    mt5.get_bars.return_value = df
    return mt5


@pytest.fixture
def streamer(fake_mt5_connector):
    return MT5Streamer(
        mt5_connector=fake_mt5_connector,
        account_id=999999,
        broker="JustMarkets"
    )


# ------------------------------------------------------------------
# TESTS
# ------------------------------------------------------------------

def test_subscribe_and_unsubscribe(streamer):
    streamer.subscribe_symbol("EURUSD", "M1")
    assert "EURUSD:M1" in streamer.subscribed_symbols

    streamer.unsubscribe_symbol("EURUSD", "M1")
    assert "EURUSD:M1" not in streamer.subscribed_symbols


def test_new_bar_emits_event(streamer, mocker):
    """
    New bar should be validated and published.
    """

    streamer.subscribe_symbol("EURUSD", "M1")

    mocker.patch(
        "src.data.validation.validator.validate_bar",
        return_value=(True, None)
    )

    publish_mock = mocker.patch(
        "src.data.streaming.mt5_streamer.event_bus.publish",
        return_value=1
    )

    streamer._poll_updates()

    stats = streamer.get_statistics()
    assert stats["bars_streamed"] == 1
    assert stats["bars_rejected"] == 0

    publish_mock.assert_called_once()
    event = publish_mock.call_args[0][0]

    assert event.event_type == EventType.NEW_BAR
    assert event.symbol == "EURUSD"
    assert isinstance(event.data, MarketBar)


def test_duplicate_bar_is_not_emitted(streamer, mocker):
    """
    Same timestamp bar should not be emitted twice.
    """

    streamer.subscribe_symbol("EURUSD", "M1")

    mocker.patch(
        "src.data.validation.validator.validate_bar",
        return_value=(True, None)
    )

    publish_mock = mocker.patch(
        "src.data.streaming.mt5_streamer.event_bus.publish",
        return_value=1
    )

    streamer._poll_updates()
    streamer._poll_updates()  # same bar again

    assert streamer.get_statistics()["bars_streamed"] == 1
    publish_mock.assert_called_once()


def test_invalid_bar_is_rejected(streamer, mocker):
    """
    Invalid bars should not be published.
    """

    streamer.subscribe_symbol("EURUSD", "M1")

    mocker.patch(
        "src.data.validation.validator.validate_bar",
        return_value=(False, "Invalid bar")
    )

    publish_mock = mocker.patch(
        "src.data.streaming.mt5_streamer.event_bus.publish"
    )

    streamer._poll_updates()

    stats = streamer.get_statistics()
    assert stats["bars_streamed"] == 0
    assert stats["bars_rejected"] == 1
    publish_mock.assert_not_called()


def test_empty_mt5_response(streamer):
    """
    Empty MT5 response should be silently ignored.
    """
    streamer.mt5.get_bars.return_value = pd.DataFrame()
    streamer.subscribe_symbol("EURUSD", "M1")

    streamer._poll_updates()

    stats = streamer.get_statistics()
    assert stats["bars_streamed"] == 0
    assert stats["bars_rejected"] == 0
