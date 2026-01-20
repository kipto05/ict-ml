# File: src/core/time/visualization.py

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


from datetime import datetime, timedelta, timezone
from src.core.time import get_active_sessions, is_killzone, TradingSession
import pandas as pd


def visualize_sessions(start_date: datetime, hours: int = 24):
    """
    Create a visualization of active sessions over time.

    Args:
        start_date: Start datetime (UTC)
        hours: Number of hours to visualize

    Returns:
        DataFrame with session activity
    """
    data = []
    current = start_date
    end = start_date + timedelta(hours=hours)

    while current < end:
        active = get_active_sessions(current)

        row = {
            'utc_time': current,
            'asia': TradingSession.ASIA in active,
            'london': TradingSession.LONDON in active,
            'new_york': TradingSession.NEW_YORK in active,
            'london_kz': is_killzone(current, TradingSession.LONDON),
            'ny_kz': is_killzone(current, TradingSession.NEW_YORK),
            'overlap': len(active) > 1,
        }
        data.append(row)

        current += timedelta(minutes=15)

    return pd.DataFrame(data)


# Usage
start = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
df = visualize_sessions(start, hours=24)
print(df)

# Can export for plotting:
df.to_csv('C:/Users/hp/PycharmProjects/QUANT TRADING/files/session_visualization.csv')