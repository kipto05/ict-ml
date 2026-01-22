# ============================================================================
# TESTS
# ============================================================================

# File: tests/data/test_models.py
"""Tests for canonical market data models."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from src.data.models import MarketBar, Tick, SymbolInfo


class TestMarketBar:
    """Tests for MarketBar model."""

    def test_valid_bar_creation(self):
        """Should create valid bar."""
        bar = MarketBar(
            symbol="EURUSD",
            timeframe="H1",
            timestamp_utc=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            open=Decimal("1.2345"),
            high=Decimal("1.2350"),
            low=Decimal("1.2340"),
            close=Decimal("1.2348"),
            tick_volume=1500,
            account_id=12345,
            broker="JustMarkets"
        )

        assert bar.symbol == "EURUSD"
        assert bar.open == Decimal("1.2345")

    def test_rejects_naive_datetime(self):
        """Should reject naive datetime."""
        with pytest.raises(ValueError) as exc:
            MarketBar(
                symbol="EURUSD",
                timeframe="H1",
                timestamp_utc=datetime(2024, 1, 15, 12, 0),  # Naive!
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                tick_volume=1500,
            )

        assert "naive datetime" in str(exc.value).lower()

    def test_rejects_invalid_ohlc_open(self):
        """Should reject open outside [low, high]."""
        with pytest.raises(ValueError) as exc:
            MarketBar(
                symbol="EURUSD",
                timeframe="H1",
                timestamp_utc=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                open=Decimal("1.2360"),  # Above high!
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                tick_volume=1500,
            )

        assert "ohlc" in str(exc.value).lower()

    def test_rejects_invalid_ohlc_close(self):
        """Should reject close outside [low, high]."""
        with pytest.raises(ValueError) as exc:
            MarketBar(
                symbol="EURUSD",
                timeframe="H1",
                timestamp_utc=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2335"),  # Below low!
                tick_volume=1500,
            )

        assert "ohlc" in str(exc.value).lower()

    def test_rejects_negative_prices(self):
        """Should reject negative prices."""
        with pytest.raises(ValueError):
            MarketBar(
                symbol="EURUSD",
                timeframe="H1",
                timestamp_utc=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                open=Decimal("-1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                tick_volume=1500,
            )

    def test_from_mt5_bar(self):
        """Should create from MT5 data."""
        mt5_data = {
            'time': 1704110400,
            'open': 1.2345,
            'high': 1.2350,
            'low': 1.2340,
            'close': 1.2348,
            'tick_volume': 1500,
        }

        bar = MarketBar.from_mt5_bar(
            "EURUSD",
            "H1",
            mt5_data,
            12345,
            "JustMarkets"
        )

        assert bar.symbol == "EURUSD"
        assert bar.timestamp_utc.tzinfo == timezone.utc

