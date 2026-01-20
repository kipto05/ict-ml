import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Try importing the dst module
    from src.core.time.dst import validate_dst_handling
    from datetime import datetime, timezone

    print("=== DST Transition Test ===")
    print("Testing US Spring Forward on March 10, 2024")

    # Check DST transition
    before = datetime(2024, 3, 10, 6, 0, tzinfo=timezone.utc)
    after = datetime(2024, 3, 10, 8, 0, tzinfo=timezone.utc)

    print(f"\nBefore transition (6:00 UTC): {before}")
    print(f"After transition (8:00 UTC): {after}")

    result = validate_dst_handling(before, after, "America/New_York")

    print("\n=== DST Validation Result ===")
    for key, value in result.items():
        print(f"{key}: {value}")

    # Interpret the results
    print("\n=== Interpretation ===")
    if result.get('transition_detected', False):
        print("✓ DST transition detected!")
        print(f"  Before: {'DST' if result['dst_before'] else 'Standard'} time")
        print(f"  After: {'DST' if result['dst_after'] else 'Standard'} time")

        if result['dst_before'] and not result['dst_after']:
            print("  Type: Fall back (clocks turned back 1 hour)")
        elif not result['dst_before'] and result['dst_after']:
            print("  Type: Spring forward (clocks moved ahead 1 hour)")
    else:
        print("✗ No DST transition detected")

except ImportError as e:
    print(f"Import Error: {e}")

    # Create a mock implementation for testing
    print("\nCreating mock validate_dst_handling for demonstration...")

    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo


    def validate_dst_handling(before_dt, after_dt, timezone_str):
        """Mock DST validation function."""
        tz = ZoneInfo(timezone_str)

        before_local = before_dt.astimezone(tz)
        after_local = after_dt.astimezone(tz)

        dst_before = before_local.dst().seconds > 0 if before_local.dst() else False
        dst_after = after_local.dst().seconds > 0 if after_local.dst() else False

        transition_detected = dst_before != dst_after

        return {
            'transition_detected': transition_detected,
            'dst_before': dst_before,
            'dst_after': dst_after,
            'utc_offset_before': before_local.utcoffset().total_seconds() / 3600,
            'utc_offset_after': after_local.utcoffset().total_seconds() / 3600,
            'local_time_before': before_local.strftime('%Y-%m-%d %H:%M:%S'),
            'local_time_after': after_local.strftime('%Y-%m-%d %H:%M:%S'),
        }


    # Now test with the mock function
    before = datetime(2024, 3, 10, 6, 0, tzinfo=timezone.utc)
    after = datetime(2024, 3, 10, 8, 0, tzinfo=timezone.utc)

    result = validate_dst_handling(before, after, "America/New_York")

    print("\n=== Mock DST Validation Result ===")
    for key, value in result.items():
        print(f"{key}: {value}")