# ============================================================================
# tests/unit/test_utils.py - Utility Functions Tests
# ============================================================================

"""
Unit tests for utility functions.
"""

import pytest
from datetime import datetime
import pytz
from src.core.utils import (
    to_ny_time,
    is_killzone,
    pips_to_price,
    price_to_pips,
    calculate_lot_size,
    safe_divide,
    validate_symbol
)
from src.core.constants import Killzone


class TestUtilityFunctions:
    """Test utility functions."""

    def test_to_ny_time(self):
        """Test timezone conversion to NY time."""
        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.utc)
        ny_time = to_ny_time(utc_time)

        assert ny_time.tzinfo.zone == 'America/New_York'

    def test_pips_to_price(self):
        """Test pips to price conversion."""
        # Standard pair
        price = pips_to_price(10, "EURUSD")
        assert price == 0.0010

        # JPY pair
        price_jpy = pips_to_price(10, "USDJPY")
        assert price_jpy == 0.10

    def test_price_to_pips(self):
        """Test price to pips conversion."""
        # Standard pair
        pips = price_to_pips(0.0010, "EURUSD")
        assert pips == 10.0

        # JPY pair
        pips_jpy = price_to_pips(0.10, "USDJPY")
        assert pips_jpy == 10.0

    def test_calculate_lot_size(self):
        """Test position size calculation."""
        lot_size = calculate_lot_size(
            account_balance=10000,
            risk_percent=1.0,
            stop_loss_pips=20,
            symbol="EURUSD"
        )

        assert isinstance(lot_size, float)
        assert lot_size > 0
        assert lot_size < 10  # Sanity check

    def test_safe_divide(self):
        """Test safe division."""
        # Normal division
        assert safe_divide(10, 2) == 5.0

        # Division by zero
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=999) == 999

    def test_validate_symbol(self):
        """Test symbol validation."""
        assert validate_symbol("EURUSD") is True
        assert validate_symbol("GBPJPY") is True
        assert validate_symbol("eurusd") is False  # lowercase
        assert validate_symbol("EUR") is False  # too short
        assert validate_symbol("EURUSD1") is False  # contains number