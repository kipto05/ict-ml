import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import from your src directory
    from src.core.time.sessions import TradingSession, session_bounds_utc
    from datetime import date

    print("=== Trading Session Times for January 15, 2024 ===")

    # Get exact session times for a specific date
    date_obj = date(2024, 1, 15)

    for session in TradingSession:
        try:
            start, end = session_bounds_utc(date_obj, session)
            print(f"\n{session.value}:")
            print(f"  Start (UTC): {start.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  End (UTC): {end.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"\n{session.value}: Error - {e}")

except ImportError as e:
    print(f"Import Error: {e}")
    print("\nMake sure you have the correct project structure:")
    print("1. src/core/time/sessions.py should exist")
    print("2. TradingSession enum and session_bounds_utc function should be defined")

    # Show current directory structure
    print("\n=== Current Working Directory ===")
    print(f"Working dir: {os.getcwd()}")
    print(f"Script location: {__file__}")