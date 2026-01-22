
# File: tests/data/test_validation.py
"""Tests for market data validation."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from src.data.models import MarketBar
from src.data.validation import DataValidator


class TestDataValidator:
    """Tests for DataValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DataValidator()

    @pytest.fixture
    def valid_bar(self):
        """Create valid bar."""
        return MarketBar(
            symbol="EURUSD",
            timeframe="H1",
            timestamp_utc=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            open=Decimal("1.2345"),
            high=Decimal("1.2350"),
            low=Decimal("1.2340"),
            close=Decimal("1.2348"),
            tick_volume=1500,
        )

    def test_validates_correct_bar(self, validator, valid_bar):
        """Should validate correct bar."""
        is_valid, reason = validator.validate_bar(valid_bar)
        assert is_valid is True
        assert reason is None

    def test_rejects_unrealistic_range(self, validator):
        """Should reject bar with unrealistic price range."""
        bar = MarketBar(
            symbol="EURUSD",
            timeframe="H1",
            timestamp_utc=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            open=Decimal("1.2345"),
            high=Decimal("2.0000"),  # Unrealistic!
            low=Decimal("0.5000"),
            close=Decimal("1.5000"),
            tick_volume=1500,
        )

        is_valid, reason = validator.validate_bar(bar)
        assert is_valid is False
        assert "unrealistic" in reason.lower()

    def test_sequence_validation_monotonic(self, validator):
        """Should validate monotonic time ordering."""
        bar1 = MarketBar(
            symbol="EURUSD",
            timeframe="H1",
            timestamp_utc=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            open=Decimal("1.2345"),
            high=Decimal("1.2350"),
            low=Decimal("1.2340"),
            close=Decimal("1.2348"),
            tick_volume=1500,
        )

        bar2 = MarketBar(
            symbol="EURUSD",
            timeframe="H1",
            timestamp_utc=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            open=Decimal("1.2348"),
            high=Decimal("1.2355"),
            low=Decimal("1.2345"),
            close=Decimal("1.2352"),
            tick_volume=1600,
        )

        is_valid, errors = validator.validate_bar_sequence([bar1, bar2])
        assert is_valid is True
        assert len(errors) == 0

