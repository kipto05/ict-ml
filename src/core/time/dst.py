# ============================================================================
# File: src/core/time/dst.py
# ============================================================================

"""
Daylight Saving Time (DST) utilities.

Provides functions to detect DST transitions and validate DST handling.
"""

from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import List, Tuple

from src.core.time.time_utils import ensure_utc


def is_dst(dt_utc: datetime, tz_name: str) -> bool:
    """
    Check if datetime is during Daylight Saving Time in given timezone.

    Args:
        dt_utc: UTC datetime
        tz_name: Timezone name (e.g., 'America/New_York')

    Returns:
        True if DST is active

    Example:
        >>> # January - no DST
        >>> dt = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
        >>> is_dst(dt, 'America/New_York')
        False

        >>> # July - DST active
        >>> dt = datetime(2024, 7, 15, 12, 0, tzinfo=timezone.utc)
        >>> is_dst(dt, 'America/New_York')
        True
    """
    dt_utc = ensure_utc(dt_utc)
    tz = ZoneInfo(tz_name)
    local_dt = dt_utc.astimezone(tz)

    # DST is active if the UTC offset includes DST adjustment
    return local_dt.dst() is not None and local_dt.dst().total_seconds() != 0


def get_dst_transition_dates(year: int, tz_name: str) -> List[Tuple[datetime, str]]:
    """
    Get DST transition dates for a given year and timezone.

    Args:
        year: Year to check
        tz_name: Timezone name

    Returns:
        List of (transition_datetime_utc, transition_type) tuples
        transition_type is either 'start' or 'end'

    Example:
        >>> transitions = get_dst_transition_dates(2024, 'America/New_York')
        >>> len(transitions)
        2  # Spring forward, Fall back
    """
    tz = ZoneInfo(tz_name)
    transitions = []

    # Check each day of the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    current_date = start_date
    prev_dst = None

    while current_date <= end_date:
        # Check at noon UTC to avoid edge cases
        dt_utc = datetime.combine(current_date, datetime.min.time(), tzinfo=timezone.utc)
        dt_utc = dt_utc.replace(hour=12)

        current_dst = is_dst(dt_utc, tz_name)

        if prev_dst is not None and current_dst != prev_dst:
            # DST transition detected
            transition_type = 'start' if current_dst else 'end'

            # Find exact transition time (usually 2 AM local time)
            # Search hour by hour on transition day
            for hour in range(24):
                check_dt = dt_utc.replace(hour=hour)
                if is_dst(check_dt, tz_name) == current_dst:
                    transitions.append((check_dt, transition_type))
                    break

        prev_dst = current_dst
        current_date += timedelta(days=1)

    return transitions


def validate_dst_handling(
        dt_before: datetime,
        dt_after: datetime,
        tz_name: str
) -> dict:
    """
    Validate DST handling around a transition.

    Useful for testing DST correctness.

    Args:
        dt_before: UTC datetime before transition
        dt_after: UTC datetime after transition
        tz_name: Timezone name

    Returns:
        Dictionary with DST validation info

    Example:
        >>> before = datetime(2024, 3, 10, 6, 0, tzinfo=timezone.utc)  # Before spring forward
        >>> after = datetime(2024, 3, 10, 8, 0, tzinfo=timezone.utc)   # After spring forward
        >>> result = validate_dst_handling(before, after, 'America/New_York')
        >>> result['transition_detected']
        True
    """
    dt_before = ensure_utc(dt_before)
    dt_after = ensure_utc(dt_after)

    dst_before = is_dst(dt_before, tz_name)
    dst_after = is_dst(dt_after, tz_name)

    tz = ZoneInfo(tz_name)
    local_before = dt_before.astimezone(tz)
    local_after = dt_after.astimezone(tz)
    return {
        'transition_detected': dst_before != dst_after,
        'dst_before': dst_before,
        'dst_after': dst_after,
        'utc_offset_before': local_before.utcoffset().total_seconds() / 3600,
        'utc_offset_after': local_after.utcoffset().total_seconds() / 3600,
        'local_time_before': local_before.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'local_time_after': local_after.strftime('%Y-%m-%d %H:%M:%S %Z'),
    }

