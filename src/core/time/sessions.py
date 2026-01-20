# ============================================================================
# File: src/core/time/sessions.py
# ============================================================================

"""
Trading session detection with DST awareness.

Sessions are defined in their local timezones and automatically
adjust for Daylight Saving Time transitions.
"""

from datetime import datetime, time, date, timedelta
from zoneinfo import ZoneInfo
from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.core.time.time_utils import ensure_utc, to_timezone


class TradingSession(Enum):
    """Trading session definitions."""
    ASIA = "asia"
    LONDON = "london"
    NEW_YORK = "new_york"


@dataclass(frozen=True)
class SessionConfig:
    """Session configuration with timezone and time windows."""
    name: TradingSession
    timezone: str
    start_time: time
    end_time: time
    killzone_start: Optional[time] = None
    killzone_end: Optional[time] = None


# Session definitions (local times in their respective timezones)
SESSION_CONFIGS = {
    TradingSession.ASIA: SessionConfig(
        name=TradingSession.ASIA,
        timezone="Asia/Tokyo",
        start_time=time(0, 0),
        end_time=time(9, 0),
        killzone_start=time(0, 0),
        killzone_end=time(3, 0),
    ),
    TradingSession.LONDON: SessionConfig(
        name=TradingSession.LONDON,
        timezone="Europe/London",
        start_time=time(8, 0),
        end_time=time(17, 0),
        killzone_start=time(2, 0),  # 2 AM - 5 AM London time
        killzone_end=time(5, 0),
    ),
    TradingSession.NEW_YORK: SessionConfig(
        name=TradingSession.NEW_YORK,
        timezone="America/New_York",
        start_time=time(8, 0),
        end_time=time(17, 0),
        killzone_start=time(8, 30),  # 8:30 AM - 11:00 AM NY time
        killzone_end=time(11, 0),
    ),
}


def session_bounds_utc(
        date_obj: date,
        session: TradingSession
) -> Tuple[datetime, datetime]:
    """
    Get session start and end times in UTC for a given date.

    Automatically handles DST transitions.

    Args:
        date_obj: Date for which to get session bounds
        session: Trading session

    Returns:
        Tuple of (start_utc, end_utc)

    Example:
        >>> from datetime import date
        >>> start, end = session_bounds_utc(date(2024, 1, 15), TradingSession.LONDON)
        >>> start.hour  # London 8 AM in winter = 8 AM UTC
        8
        >>> # In summer (BST), London 8 AM = 7 AM UTC
    """
    config = SESSION_CONFIGS[session]
    tz = ZoneInfo(config.timezone)

    # Create session start and end in local timezone
    start_local = datetime.combine(date_obj, config.start_time, tzinfo=tz)
    end_local = datetime.combine(date_obj, config.end_time, tzinfo=tz)

    # Handle session that crosses midnight
    if config.end_time < config.start_time:
        end_local += timedelta(days=1)

    # Convert to UTC
    start_utc = start_local.astimezone(ZoneInfo("UTC"))
    end_utc = end_local.astimezone(ZoneInfo("UTC"))

    return start_utc, end_utc


def is_in_session(dt_utc: datetime, session: TradingSession) -> bool:
    """
    Check if UTC datetime falls within a trading session.

    Args:
        dt_utc: UTC datetime to check
        session: Trading session

    Returns:
        True if datetime is within session

    Raises:
        ValueError: If datetime is naive

    Example:
        >>> utc_dt = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        >>> is_in_session(utc_dt, TradingSession.LONDON)
        True
    """
    dt_utc = ensure_utc(dt_utc)
    date_obj = dt_utc.date()

    # Check current day and previous day (for sessions crossing midnight)
    for date_to_check in [date_obj, date_obj - timedelta(days=1)]:
        start_utc, end_utc = session_bounds_utc(date_to_check, session)
        if start_utc <= dt_utc < end_utc:
            return True

    return False


def get_active_sessions(dt_utc: datetime) -> List[TradingSession]:
    """
    Get all active trading sessions for a given UTC datetime.

    Multiple sessions can be active simultaneously (e.g., London/NY overlap).

    Args:
        dt_utc: UTC datetime

    Returns:
        List of active sessions

    Example:
        >>> # During London/NY overlap
        >>> dt = datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc)
        >>> sessions = get_active_sessions(dt)
        >>> TradingSession.LONDON in sessions
        True
        >>> TradingSession.NEW_YORK in sessions
        True
    """
    dt_utc = ensure_utc(dt_utc)

    active = []
    for session in TradingSession:
        if is_in_session(dt_utc, session):
            active.append(session)

    return active


def get_primary_session(dt_utc: datetime) -> Optional[TradingSession]:
    """
    Get primary (most relevant) trading session for a UTC datetime.

    Priority order: New York > London > Asia

    Args:
        dt_utc: UTC datetime

    Returns:
        Primary session or None if no session is active

    Example:
        >>> dt = datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)
        >>> get_primary_session(dt)
        <TradingSession.NEW_YORK: 'new_york'>
    """
    active = get_active_sessions(dt_utc)

    if not active:
        return None

    # Priority order
    priority = [TradingSession.NEW_YORK, TradingSession.LONDON, TradingSession.ASIA]

    for session in priority:
        if session in active:
            return session

    return active[0]


def is_killzone(dt_utc: datetime, session: TradingSession) -> bool:
    """
    Check if UTC datetime falls within a session's killzone.

    Killzones are high-probability trading windows within sessions.

    Args:
        dt_utc: UTC datetime
        session: Trading session

    Returns:
        True if datetime is within killzone

    Example:
        >>> # London killzone: 2 AM - 5 AM London time
        >>> dt = datetime(2024, 1, 15, 3, 0, tzinfo=timezone.utc)
        >>> is_killzone(dt, TradingSession.LONDON)
        True
    """
    dt_utc = ensure_utc(dt_utc)
    config = SESSION_CONFIGS[session]

    if config.killzone_start is None or config.killzone_end is None:
        return False

    # Convert to session's local timezone
    local_dt = to_timezone(dt_utc, config.timezone)
    local_time = local_dt.time()

    # Check if within killzone hours
    if config.killzone_end > config.killzone_start:
        # Normal case: killzone within same day
        return config.killzone_start <= local_time < config.killzone_end
    else:
        # Killzone crosses midnight
        return local_time >= config.killzone_start or local_time < config.killzone_end