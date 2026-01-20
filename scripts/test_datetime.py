import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.time import is_naive, ensure_utc
from datetime import datetime, timedelta, timezone


dt = datetime(2026, 1,15,12,0,0,tzinfo=timezone.utc)

print(f"Is naive? {is_naive(dt)}")
print(f"Timezone: {dt.tzinfo}")

try:
    utc_dt = ensure_utc(dt)
    print(f"✓ Successfully converted to UTC: {utc_dt}")
except ValueError as e:
    print(f"✗ Error: {e}")