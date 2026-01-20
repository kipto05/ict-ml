# ============================================================================
# File: src/core/time/time_utils.py
# ============================================================================

"""
Core time utilities for timezone-safe datetime operations.

All functions enforce UTC as the internal standard.
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Optional
import re


def now_utc() -> datetime:
    """
    Get current UTC time as aware datetime.

    Returns:
        Current UTC datetime with timezone info

    Example:
        >>> dt = now_utc()
        >>> dt.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def is_naive(dt: datetime) -> bool:
    """
    Check if datetime is naive (lacks timezone info).

    Args:
        dt: Datetime to check

    Returns:
        True if naive, False if timezone-aware

    Example:
        >>> is_naive(datetime.now())
        True
        >>> is_naive(now_utc())
        False
    """
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware and in UTC.

    Raises ValueError if datetime is naive to prevent silent errors.

    Args:
        dt: Datetime to convert

    Returns:
        UTC datetime

    Raises:
        ValueError: If datetime is naive

    Example:
        >>> utc_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        >>> ensure_utc(utc_dt)
        datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    """
    if is_naive(dt):
        raise ValueError(
            f"Naive datetime not allowed: {dt}. "
            "All datetimes must be timezone-aware. "
            "Use datetime.now(timezone.utc) or dt.replace(tzinfo=timezone.utc)"
        )

    return dt.astimezone(timezone.utc)


def to_timezone(dt: datetime, tz_name: str) -> datetime:
    """
    Convert UTC datetime to specified timezone.

    Args:
        dt: UTC datetime
        tz_name: Target timezone name (e.g., 'America/New_York')

    Returns:
        Datetime in target timezone

    Raises:
        ValueError: If datetime is naive
        ZoneInfoNotFoundError: If timezone name is invalid

    Example:
        >>> utc_dt = datetime(2024, 1, 1, 17, 0, tzinfo=timezone.utc)
        >>> ny_dt = to_timezone(utc_dt, 'America/New_York')
        >>> ny_dt.hour
        12  # 5 hours behind UTC in winter
    """
    utc_dt = ensure_utc(dt)
    target_tz = ZoneInfo(tz_name)
    return utc_dt.astimezone(target_tz)


def timestamp_from_mt5(mt5_time: int) -> datetime:
    """
    Convert MT5 timestamp (Unix epoch seconds) to UTC datetime.

    MT5 returns timestamps as Unix epoch (seconds since 1970-01-01 UTC).

    Args:
        mt5_time: MT5 timestamp in seconds

    Returns:
        UTC-aware datetime

    Example:
        >>> timestamp_from_mt5(1704117600)
        datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    """
    return datetime.fromtimestamp(mt5_time, tz=timezone.utc)


def floor_time(dt: datetime, timeframe: str) -> datetime:
    """
    Floor datetime to timeframe boundary.

    Useful for normalizing bar timestamps.

    Args:
        dt: Datetime to floor
        timeframe: Timeframe string (e.g., 'H1', 'M15', 'D1')

    Returns:
        Floored datetime

    Raises:
        ValueError: If timeframe is invalid

    Example:
        >>> dt = datetime(2024, 1, 1, 12, 37, 42, tzinfo=timezone.utc)
        >>> floor_time(dt, 'H1')
        datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        >>> floor_time(dt, 'M15')
        datetime.datetime(2024, 1, 1, 12, 30, 0, tzinfo=datetime.timezone.utc)
    """
    dt = ensure_utc(dt)

    # Parse timeframe
    match = re.match(r'([MHDW])(\d+)', timeframe)
    if not match:
        raise ValueError(f"Invalid timeframe format: {timeframe}")

    unit, value = match.groups()
    value = int(value)

    # Floor based on unit
    if unit == 'M':  # Minutes
        minutes = (dt.minute // value) * value
        return dt.replace(minute=minutes, second=0, microsecond=0)
    elif unit == 'H':  # Hours
        hours = (dt.hour // value) * value
        return dt.replace(hour=hours, minute=0, second=0, microsecond=0)
    elif unit == 'D':  # Days
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif unit == 'W':  # Weeks
        days_since_monday = dt.weekday()
        return (dt - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        raise ValueError(f"Unknown timeframe unit: {unit}")
