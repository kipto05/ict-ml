# ============================================================================
# File: src/core/time/usage_examples.py -> Basic time utilities
# ============================================================================

from src.core.time import now_utc, ensure_utc, to_timezone, floor_time
from datetime import datetime, timezone

# Get current UTC time (always use this!)
current = now_utc()
print(current)  # 2024-01-15 14:30:45+00:00

# Convert to New York time
ny_time = to_timezone(current, "America/New_York")
print(ny_time)  # 2024-01-15 09:30:45-05:00 (EST in winter)

# Floor to hour boundary
dt = datetime(2024, 1, 15, 12, 37, 42, tzinfo=timezone.utc)
floored = floor_time(dt, "H1")
print(floored)  # 2024-01-15 12:00:00+00:00

# Floor to 15-minute boundary
floored_15m = floor_time(dt, "M15")
print(floored_15m)  # 2024-01-15 12:30:00+00:00


# ============================================================================
# File: src/core/time/usage_examples.py -> Session detection
# ============================================================================

from src.core.time import (
    get_active_sessions,
    get_primary_session,
    is_killzone,
    TradingSession
)
from datetime import datetime, timezone

# Check active sessions
dt = datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)
active = get_active_sessions(dt)
print(active)  # [<TradingSession.LONDON>, <TradingSession.NEW_YORK>]

# Get primary session (prioritizes NY > London > Asia)
primary = get_primary_session(dt)
print(primary)  # <TradingSession.NEW_YORK>

# Check if in killzone
dt_killzone = datetime(2024, 1, 15, 3, 30, tzinfo=timezone.utc)
in_london_kz = is_killzone(dt_killzone, TradingSession.LONDON)
print(in_london_kz)  # True (London killzone: 2 AM - 5 AM London time)

# Check specific session
from src.core.time import is_in_session
in_london = is_in_session(dt, TradingSession.LONDON)
print(in_london)  # True
# ============================================================================
# File: src/core/time/usage_examples.py -> DST handling
# ============================================================================
from src.core.time import is_dst, get_dst_transition_dates
from datetime import datetime, timezone

# Check if DST is active
winter_dt = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
summer_dt = datetime(2024, 7, 15, 12, 0, tzinfo=timezone.utc)

print(is_dst(winter_dt, "America/New_York"))  # False (EST)
print(is_dst(summer_dt, "America/New_York"))  # True (EDT)

# Get DST transition dates for a year
transitions = get_dst_transition_dates(2024, "America/New_York")
for dt, transition_type in transitions:
    print(f"{transition_type}: {dt}")
# Output:
# start: 2024-03-10 07:00:00+00:00 (Spring forward)
# end: 2024-11-03 06:00:00+00:00 (Fall back)

# ============================================================================
# File: src/core/time/usage_examples.py -> Integration with MT5 Data
# ============================================================================

from src.core.time import timestamp_from_mt5, ensure_utc, is_in_session
from src.core.time import TradingSession

# Convert MT5 timestamp to UTC
mt5_timestamp = 1704110400  # From MT5 data
dt_utc = timestamp_from_mt5(mt5_timestamp)

# Check which session this candle belongs to
if is_in_session(dt_utc, TradingSession.LONDON):
    print("London session candle")
elif is_in_session(dt_utc, TradingSession.NEW_YORK):
    print("New York session candle")