# ============================================================================
# File: src/core/time/__init__.py
# ============================================================================

"""
Time handling module for ICT Trading Bot.

This module provides timezone-safe time utilities, session detection,
and DST handling for accurate trading analysis.
"""

from src.core.time.time_utils import (
    now_utc,
    ensure_utc,
    to_timezone,
    timestamp_from_mt5,
    floor_time,
    is_naive,
)

from src.core.time.sessions import (
    TradingSession,
    get_active_sessions,
    get_primary_session,
    is_killzone,
    is_in_session,
    session_bounds_utc,
)

from src.core.time.dst import (
    is_dst,
    get_dst_transition_dates,
    validate_dst_handling,
)

__all__ = [
    # Time utilities
    'now_utc',
    'ensure_utc',
    'to_timezone',
    'timestamp_from_mt5',
    'floor_time',
    'is_naive',
    # Session detection
    'TradingSession',
    'get_active_sessions',
    'get_primary_session',
    'is_killzone',
    'is_in_session',
    'session_bounds_utc',
    # DST handling
    'is_dst',
    'get_dst_transition_dates',
    'validate_dst_handling',
]







