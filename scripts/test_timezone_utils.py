import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

try:
    # Try to import from your project
    from src.core.time import is_naive, ensure_utc

    print("✓ Successfully imported from src.core.time.time_utils")
except ImportError as e:
    print(f"✗ Could not import from src: {e}")
    print("Using built-in implementations...")


    # Define the functions locally
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


def test_timezone_utilities():
    """Test the is_naive and ensure_utc functions."""

    print("=" * 60)
    print("TIMEZONE UTILITIES TEST")
    print("=" * 60)



    # Test Case 1: Naive datetime
    print("\n" + "=" * 30)
    print("TEST 1: Naive Datetime")
    print("=" * 30)

    naive_dt = datetime(2024, 1, 15, 12, 0, 0)
    print(f"Datetime: {naive_dt}")
    print(f"Is naive? {is_naive(naive_dt)}")
    print(f"Timezone: {naive_dt.tzinfo}")

    try:
        utc_dt = ensure_utc(naive_dt)
        print(f"✓ Successfully converted to UTC: {utc_dt}")
    except ValueError as e:
        print(f"✗ Error: {e}")

    # Test Case 2: UTC datetime
    print("\n" + "=" * 30)
    print("TEST 2: UTC Datetime")
    print("=" * 30)

    utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    print(f"Datetime: {utc_dt}")
    print(f"Is naive? {is_naive(utc_dt)}")
    print(f"Timezone: {utc_dt.tzinfo}")

    try:
        result = ensure_utc(utc_dt)
        print(f"✓ Already UTC: {result}")
        print(f"  Same object? {result is utc_dt}")
    except ValueError as e:
        print(f"✗ Error: {e}")

    # Test Case 3: New York timezone (EST)
    print("\n" + "=" * 30)
    print("TEST 3: New York Time (EST)")
    print("=" * 30)

    ny_tz = ZoneInfo("America/New_York")
    ny_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ny_tz)
    print(f"Datetime: {ny_dt}")
    print(f"Is naive? {is_naive(ny_dt)}")
    print(f"Local time (NY): {ny_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        result = ensure_utc(ny_dt)
        print(f"✓ Converted to UTC: {result}")
        print(f"  UTC equivalent: {result.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except ValueError as e:
        print(f"✗ Error: {e}")

    # Test Case 4: London timezone (GMT/BST)
    print("\n" + "=" * 30)
    print("TEST 4: London Time (Summer - BST)")
    print("=" * 30)

    london_tz = ZoneInfo("Europe/London")
    london_dt = datetime(2024, 7, 15, 12, 0, 0, tzinfo=london_tz)
    print(f"Datetime: {london_dt}")
    print(f"Is naive? {is_naive(london_dt)}")
    print(f"Local time (London): {london_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        result = ensure_utc(london_dt)
        print(f"✓ Converted to UTC: {result}")
        print(f"  UTC equivalent: {result.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except ValueError as e:
        print(f"✗ Error: {e}")

    # Test Case 5: Tokyo timezone (no DST)
    print("\n" + "=" * 30)
    print("TEST 5: Tokyo Time (JST)")
    print("=" * 30)

    tokyo_tz = ZoneInfo("Asia/Tokyo")
    tokyo_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=tokyo_tz)
    print(f"Datetime: {tokyo_dt}")
    print(f"Is naive? {is_naive(tokyo_dt)}")
    print(f"Local time (Tokyo): {tokyo_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        result = ensure_utc(tokyo_dt)
        print(f"✓ Converted to UTC: {result}")
        print(f"  UTC equivalent: {result.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except ValueError as e:
        print(f"✗ Error: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    test_cases = [
        ("Naive", datetime(2024, 1, 15, 12, 0, 0)),
        ("UTC", datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)),
        ("New York", datetime(2024, 1, 15, 12, 0, 0, tzinfo=ny_tz)),
        ("London", datetime(2024, 7, 15, 12, 0, 0, tzinfo=london_tz)),
        ("Tokyo", datetime(2024, 1, 15, 12, 0, 0, tzinfo=tokyo_tz)),
    ]

    for name, dt in test_cases:
        is_naive_result = is_naive(dt)
        can_convert = not is_naive_result
        status = "✓" if can_convert else "✗"
        print(f"{status} {name:10} | Naive: {is_naive_result:5} | Convertible: {can_convert}")


def demonstrate_practical_use():
    """Show practical examples of why timezone handling matters."""

    print("\n" + "=" * 60)
    print("PRACTICAL EXAMPLE: Trading Session Times")
    print("=" * 60)

    # Create a naive datetime (common mistake)
    naive_order_time = datetime(2024, 1, 15, 14, 30, 0)
    print(f"\nTrader enters order at: {naive_order_time}")
    print(f"Is this timezone-aware? {not(is_naive(naive_order_time))}")

    # Try to convert to UTC (will fail)
    try:
        utc_time = ensure_utc(naive_order_time)
        print(f"Converted to UTC: {utc_time}")
    except ValueError as e:
        print(f"❌ Problem: {e}")
        print("  This would cause issues in a trading system!")
        print("  Is it 14:30 in London? New York? Tokyo?")

    # Correct approach: Specify timezone
    print("\n--- Correct Approach ---")

    # Trader in New York
    ny_tz = ZoneInfo("America/New_York")
    ny_order_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=ny_tz)
    print(f"Trader in NY enters order at: {ny_order_time}")
    print(f"  Local: {ny_order_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        utc_time = ensure_utc(ny_order_time)
        print(f"  Converted to UTC: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  This is: {utc_time.hour}:{utc_time.minute:02d} UTC")
    except ValueError as e:
        print(f"  Error: {e}")

    # Same local time in London
    print("\n--- Same Local Time, Different Timezone ---")

    london_tz = ZoneInfo("Europe/London")
    london_order_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=london_tz)
    print(f"Trader in London enters order at: {london_order_time}")
    print(f"  Local: {london_order_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        utc_time = ensure_utc(london_order_time)
        print(f"  Converted to UTC: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  This is: {utc_time.hour}:{utc_time.minute:02d} UTC")
    except ValueError as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("KEY TAKEAWAYS:")
    print("=" * 60)
    print("1. Always use timezone-aware datetimes in trading systems")
    print("2. Store and transmit all times in UTC")
    print("3. Convert to local time only for display purposes")
    print("4. Never assume a datetime is in a specific timezone")


if __name__ == "__main__":
    test_timezone_utilities()
    demonstrate_practical_use()