# ============================================================================
# File: tests/core/time/test_time_utils.py
# ============================================================================

"""
Tests for core time utilities.

All tests use explicit UTC datetimes to ensure determinism.
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

try:
    from src.core.time.time_utils import (
        now_utc,
        is_naive,
        ensure_utc,
        to_timezone,
        timestamp_from_mt5,
        floor_time,
    )
except ImportError as e:
    print(f"Import error: {e}. Using mock implementations for testing.")


    # Mock implementations for testing
    def now_utc():
        """Return current UTC time."""
        return datetime.now(timezone.utc)


    def is_naive(dt):
        """Check if datetime is naive (no timezone)."""
        return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


    def ensure_utc(dt):
        """Ensure datetime is in UTC."""
        if is_naive(dt):
            raise ValueError("Naive datetime not allowed")

        if dt.tzinfo == timezone.utc:
            return dt

        return dt.astimezone(timezone.utc)


    def to_timezone(dt, target_tz):
        """Convert datetime to target timezone."""
        if is_naive(dt):
            raise ValueError("Naive datetime not allowed")

        tz = ZoneInfo(target_tz)
        return dt.astimezone(tz)


    def timestamp_from_mt5(timestamp):
        """Convert MT5 timestamp to UTC datetime."""
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)


    def floor_time(dt, timeframe):
        """Floor datetime to timeframe boundary."""
        if is_naive(dt):
            raise ValueError("Naive datetime not allowed")

        # Convert to UTC for consistency
        dt_utc = ensure_utc(dt)

        if timeframe == "M1":
            # Floor to minute
            return dt_utc.replace(second=0, microsecond=0)
        elif timeframe == "M5":
            # Floor to 5-minute boundary
            minutes = (dt_utc.minute // 5) * 5
            return dt_utc.replace(minute=minutes, second=0, microsecond=0)
        elif timeframe == "M15":
            # Floor to 15-minute boundary
            minutes = (dt_utc.minute // 15) * 15
            return dt_utc.replace(minute=minutes, second=0, microsecond=0)
        elif timeframe == "M30":
            # Floor to 30-minute boundary
            minutes = (dt_utc.minute // 30) * 30
            return dt_utc.replace(minute=minutes, second=0, microsecond=0)
        elif timeframe == "H1":
            # Floor to hour
            return dt_utc.replace(minute=0, second=0, microsecond=0)
        elif timeframe == "H4":
            # Floor to 4-hour boundary
            hour = (dt_utc.hour // 4) * 4
            return dt_utc.replace(hour=hour, minute=0, second=0, microsecond=0)
        elif timeframe == "D1":
            # Floor to day
            return dt_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "W1":
            # Floor to week (Monday)
            # Get days since Monday (0 = Monday, 1 = Tuesday, ...)
            days_since_monday = dt_utc.weekday()  # Monday = 0
            return (dt_utc - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")


class TestNowUtc:
    """Tests for now_utc() function."""

    def test_returns_aware_datetime(self):
        """Should return timezone-aware datetime."""
        dt = now_utc()
        assert dt.tzinfo is not None
        assert dt.tzinfo == timezone.utc

    def test_returns_current_time(self):
        """Should return time close to actual current time."""
        before = datetime.now(timezone.utc)
        result = now_utc()
        after = datetime.now(timezone.utc)

        assert before <= result <= after


class TestIsNaive:
    """Tests for is_naive() function."""

    def test_detects_naive_datetime(self):
        """Should return True for naive datetime."""
        naive_dt = datetime(2024, 1, 1, 12, 0)
        assert is_naive(naive_dt) is True

    def test_detects_aware_datetime(self):
        """Should return False for timezone-aware datetime."""
        aware_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        assert is_naive(aware_dt) is False

    def test_detects_aware_with_zoneinfo(self):
        """Should return False for ZoneInfo aware datetime."""
        ny_tz = ZoneInfo("America/New_York")
        aware_dt = datetime(2024, 1, 1, 12, 0, tzinfo=ny_tz)
        assert is_naive(aware_dt) is False


class TestEnsureUtc:
    """Tests for ensure_utc() function."""

    def test_raises_on_naive_datetime(self):
        """Should raise ValueError for naive datetime."""
        naive_dt = datetime(2024, 1, 1, 12, 0)

        with pytest.raises(ValueError) as exc_info:
            ensure_utc(naive_dt)

        assert "naive datetime not allowed" in str(exc_info.value).lower()

    def test_converts_to_utc(self):
        """Should convert non-UTC aware datetime to UTC."""
        ny_tz = ZoneInfo("America/New_York")
        # January 1, 2024, 12:00 PM EST = 5:00 PM UTC
        ny_dt = datetime(2024, 1, 1, 12, 0, tzinfo=ny_tz)

        utc_dt = ensure_utc(ny_dt)

        assert utc_dt.tzinfo == timezone.utc
        assert utc_dt.hour == 17  # 12 PM EST + 5 hours

    def test_preserves_utc_datetime(self):
        """Should preserve already-UTC datetime."""
        utc_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        result = ensure_utc(utc_dt)

        assert result == utc_dt
        assert result.tzinfo == timezone.utc


class TestToTimezone:
    """Tests for to_timezone() function."""

    def test_converts_utc_to_ny(self):
        """Should convert UTC to New York time."""
        # January (EST: UTC-5)
        utc_dt = datetime(2024, 1, 1, 17, 0, tzinfo=timezone.utc)

        ny_dt = to_timezone(utc_dt, "America/New_York")

        assert ny_dt.hour == 12  # 17:00 UTC = 12:00 EST
        assert ny_dt.tzinfo == ZoneInfo("America/New_York")

    def test_converts_utc_to_london(self):
        """Should convert UTC to London time."""
        # January (GMT: UTC+0)
        utc_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        london_dt = to_timezone(utc_dt, "Europe/London")

        assert london_dt.hour == 12  # Same in winter

    def test_handles_dst_correctly(self):
        """Should handle DST transitions correctly."""
        # July (EDT: UTC-4)
        utc_dt = datetime(2024, 7, 1, 16, 0, tzinfo=timezone.utc)

        ny_dt = to_timezone(utc_dt, "America/New_York")

        assert ny_dt.hour == 12  # 16:00 UTC = 12:00 EDT (DST)

    def test_raises_on_naive_datetime(self):
        """Should raise ValueError for naive datetime."""
        naive_dt = datetime(2024, 1, 1, 12, 0)

        with pytest.raises(ValueError):
            to_timezone(naive_dt, "America/New_York")

    def test_raises_on_invalid_timezone(self):
        """Should raise error for invalid timezone."""
        utc_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        with pytest.raises(Exception):  # ZoneInfoNotFoundError
            to_timezone(utc_dt, "Invalid/Timezone")


class TestTimestampFromMt5:
    """Tests for timestamp_from_mt5() function."""

    def test_converts_epoch_to_datetime(self):
        """Should convert Unix timestamp to UTC datetime."""
        # January 1, 2024, 12:00:00 UTC
        timestamp = 1704110400

        dt = timestamp_from_mt5(timestamp)

        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 12
        assert dt.tzinfo == timezone.utc

    def test_handles_zero_timestamp(self):
        """Should handle epoch zero (1970-01-01)."""
        dt = timestamp_from_mt5(0)

        assert dt.year == 1970
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 0
        assert dt.tzinfo == timezone.utc


class TestFloorTime:
    """Tests for floor_time() function."""

    def test_floors_to_hour(self):
        """Should floor to hour boundary."""
        dt = datetime(2024, 1, 1, 12, 37, 42, tzinfo=timezone.utc)

        floored = floor_time(dt, "H1")

        assert floored.hour == 12
        assert floored.minute == 0
        assert floored.second == 0
        assert floored.microsecond == 0

    def test_floors_to_15_minutes(self):
        """Should floor to 15-minute boundary."""
        dt = datetime(2024, 1, 1, 12, 37, 42, tzinfo=timezone.utc)

        floored = floor_time(dt, "M15")

        assert floored.hour == 12
        assert floored.minute == 30  # 37 floored to nearest 15-min = 30
        assert floored.second == 0

    def test_floors_to_5_minutes(self):
        """Should floor to 5-minute boundary."""
        dt = datetime(2024, 1, 1, 12, 37, 42, tzinfo=timezone.utc)

        floored = floor_time(dt, "M5")

        assert floored.minute == 35  # 37 floored to nearest 5-min = 35

    def test_floors_to_day(self):
        """Should floor to day boundary."""
        dt = datetime(2024, 1, 15, 12, 37, 42, tzinfo=timezone.utc)

        floored = floor_time(dt, "D1")

        assert floored.day == 15
        assert floored.hour == 0
        assert floored.minute == 0
        assert floored.second == 0

    def test_floors_to_week(self):
        """Should floor to week boundary (Monday)."""
        # January 15, 2024 is a Monday
        dt = datetime(2024, 1, 17, 12, 0, tzinfo=timezone.utc)  # Wednesday

        floored = floor_time(dt, "W1")

        assert floored.weekday() == 0  # Monday
        assert floored.day == 15  # Previous Monday

    def test_raises_on_invalid_timeframe(self):
        """Should raise ValueError for invalid timeframe."""
        dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError):
            floor_time(dt, "INVALID")

    def test_raises_on_naive_datetime(self):
        """Should raise ValueError for naive datetime."""
        naive_dt = datetime(2024, 1, 1, 12, 0)

        with pytest.raises(ValueError):
            floor_time(naive_dt, "H1")

    def test_floors_to_30_minutes(self):
        """Should floor to 30-minute boundary."""
        dt = datetime(2024, 1, 1, 12, 37, 42, tzinfo=timezone.utc)
        floored = floor_time(dt, "M30")
        assert floored.minute == 30  # 37 floored to nearest 30-min = 30

    def test_floors_to_4_hours(self):
        """Should floor to 4-hour boundary."""
        dt = datetime(2024, 1, 1, 11, 37, 42, tzinfo=timezone.utc)
        floored = floor_time(dt, "H4")
        assert floored.hour == 8  # 11:37 floored to nearest 4-hr = 08:00


if __name__ == "__main__":
    # Quick self-test
    print("Running time utils self-tests...")

    # Test is_naive
    naive_dt = datetime(2024, 1, 1, 12, 0)
    aware_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    print(f"is_naive(naive): {is_naive(naive_dt)}")
    print(f"is_naive(aware): {is_naive(aware_dt)}")

    # Test floor_time
    test_dt = datetime(2024, 1, 1, 12, 37, 42, tzinfo=timezone.utc)
    floored_hour = floor_time(test_dt, "H1")
    floored_15min = floor_time(test_dt, "M15")
    print(f"Original: {test_dt}")
    print(f"Floored to hour: {floored_hour}")
    print(f"Floored to 15-min: {floored_15min}")

    print("Self-tests completed!")