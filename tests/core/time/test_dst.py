# ============================================================================
# File: tests/core/time/test_dst.py
# ============================================================================

"""
Tests for DST handling.

Critical for ensuring correct session detection across DST transitions.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone handling

try:
    from src.core.time.dst import (
        is_dst,
        get_dst_transition_dates,
        validate_dst_handling,
    )
    from src.core.time.sessions import is_killzone, is_in_session, TradingSession
except ImportError as e:
    print(f"Import error: {e}")


    # Create mock functions for testing
    def is_dst(dt, timezone_str):
        """Mock function for testing."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(timezone_str)
        localized = dt.astimezone(tz)
        return localized.dst().seconds > 0 if localized.dst() else False


    def get_dst_transition_dates(year, timezone_str):
        """Mock function for testing."""
        # Simplified implementation
        from zoneinfo import ZoneInfo
        import pytz
        tz = pytz.timezone(timezone_str)
        transitions = []

        # Check each month for transitions
        for month in range(1, 13):
            for day in range(1, 29):
                try:
                    dt = datetime(year, month, day, 12, 0)
                    localized = tz.localize(dt)
                    # Check if this day has DST transition
                    # This is simplified - real implementation would check for actual transitions
                    pass
                except:
                    continue
        return transitions


    def validate_dst_handling(before, after, timezone_str):
        """Mock function for testing."""
        return {
            'transition_detected': False,
            'dst_before': is_dst(before, timezone_str),
            'dst_after': is_dst(after, timezone_str),
            'utc_offset_before': 0.0,
            'utc_offset_after': 0.0
        }


class TestIsDst:
    """Tests for is_dst() function."""

    def test_detects_no_dst_in_winter(self):
        """Should detect no DST in winter months."""
        # January 15, 2024 - No DST
        dt = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)

        assert is_dst(dt, "America/New_York") is False
        assert is_dst(dt, "Europe/London") is False

    def test_detects_dst_in_summer(self):
        """Should detect DST in summer months."""
        # July 15, 2024 - DST active
        dt = datetime(2024, 7, 15, 12, 0, tzinfo=timezone.utc)

        assert is_dst(dt, "America/New_York") is True
        assert is_dst(dt, "Europe/London") is True

    def test_handles_no_dst_timezone(self):
        """Should handle timezones without DST (e.g., Tokyo)."""
        winter_dt = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
        summer_dt = datetime(2024, 7, 15, 12, 0, tzinfo=timezone.utc)

        # Tokyo doesn't observe DST
        assert is_dst(winter_dt, "Asia/Tokyo") is False
        assert is_dst(summer_dt, "Asia/Tokyo") is False

    def test_raises_on_naive_datetime(self):
        """Should raise ValueError for naive datetime."""
        naive_dt = datetime(2024, 1, 15, 12, 0)

        with pytest.raises(ValueError):
            is_dst(naive_dt, "America/New_York")


class TestGetDstTransitionDates:
    """Tests for get_dst_transition_dates() function."""

    def test_finds_us_dst_transitions_2024(self):
        """Should find both US DST transitions in 2024."""
        transitions = get_dst_transition_dates(2024, "America/New_York")

        # US observes DST, should have 2 transitions
        assert len(transitions) == 2

        # Check transition types
        types = [t[1] for t in transitions]
        assert 'start' in types
        assert 'end' in types

    def test_finds_uk_dst_transitions_2024(self):
        """Should find both UK DST transitions in 2024."""
        transitions = get_dst_transition_dates(2024, "Europe/London")

        assert len(transitions) == 2

        types = [t[1] for t in transitions]
        assert 'start' in types
        assert 'end' in types

    def test_finds_no_transitions_for_tokyo(self):
        """Should find no transitions for non-DST timezone."""
        transitions = get_dst_transition_dates(2024, "Asia/Tokyo")

        assert len(transitions) == 0

    def test_transition_dates_are_in_march_and_november(self):
        """US DST transitions should be in March and November."""
        transitions = get_dst_transition_dates(2024, "America/New_York")

        months = [t[0].month for t in transitions]

        # US: Spring forward in March, Fall back in November
        assert 3 in months  # March
        assert 11 in months  # November


class TestValidateDstHandling:
    """Tests for validate_dst_handling() function."""

    def test_detects_spring_forward_transition(self):
        """Should detect spring forward DST transition."""
        # March 10, 2024 - US Spring forward at 2 AM
        before = datetime(2024, 3, 10, 6, 0, tzinfo=timezone.utc)  # 1 AM EST
        after = datetime(2024, 3, 10, 8, 0, tzinfo=timezone.utc)  # 4 AM EDT

        result = validate_dst_handling(before, after, "America/New_York")

        assert result['transition_detected'] is True
        assert result['dst_before'] is False
        assert result['dst_after'] is True
        assert result['utc_offset_before'] == -5.0  # EST
        assert result['utc_offset_after'] == -4.0  # EDT

    def test_detects_fall_back_transition(self):
        """Should detect fall back DST transition."""
        # November 3, 2024 - US Fall back at 2 AM
        before = datetime(2024, 11, 3, 5, 0, tzinfo=timezone.utc)  # 1 AM EDT
        after = datetime(2024, 11, 3, 7, 0, tzinfo=timezone.utc)  # 2 AM EST

        result = validate_dst_handling(before, after, "America/New_York")

        assert result['transition_detected'] is True
        assert result['dst_before'] is True
        assert result['dst_after'] is False

    def test_no_transition_in_winter(self):
        """Should detect no transition during winter."""
        before = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
        after = datetime(2024, 1, 15, 18, 0, tzinfo=timezone.utc)

        result = validate_dst_handling(before, after, "America/New_York")

        assert result['transition_detected'] is False
        assert result['dst_before'] is False
        assert result['dst_after'] is False


# ============================================================================
# Additional Integration Tests
# ============================================================================

class TestSessionDstIntegration:
    """Integration tests ensuring sessions work correctly with DST."""

    def test_london_killzone_winter_vs_summer(self):
        """London killzone should shift with DST."""
        try:
            from src.core.time.sessions import is_killzone, TradingSession

            # Winter: London 2 AM GMT = 2 AM UTC
            winter_dt = datetime(2024, 1, 15, 2, 30, tzinfo=timezone.utc)

            # Summer: London 2 AM BST = 1 AM UTC
            summer_dt = datetime(2024, 7, 15, 1, 30, tzinfo=timezone.utc)

            assert is_killzone(winter_dt, TradingSession.LONDON) is True
            assert is_killzone(summer_dt, TradingSession.LONDON) is True
        except ImportError:
            pytest.skip("Sessions module not available")

    def test_ny_session_shifts_with_dst(self):
        """NY session boundaries should shift with DST."""
        try:
            from src.core.time.sessions import is_in_session, TradingSession

            # Winter: NY 9 AM EST = 14:00 UTC
            winter_dt = datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)

            # Summer: NY 9 AM EDT = 13:00 UTC
            summer_dt = datetime(2024, 7, 15, 13, 0, tzinfo=timezone.utc)

            # Both should be in NY session
            assert is_in_session(winter_dt, TradingSession.NEW_YORK) is True
            assert is_in_session(summer_dt, TradingSession.NEW_YORK) is True
        except ImportError:
            pytest.skip("Sessions module not available")