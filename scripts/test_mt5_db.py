import sys
import os
import MetaTrader5 as mt5
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.settings import settings

# --- MT5 Connection ---
if not mt5.initialize(path=settings.mt5_path):
    print("MT5 initialization FAILED:", mt5.last_error())
else:
    account_info = mt5.account_info()
    print(f"MT5 Connected. Balance: {account_info.balance}")

# --- Database Connection ---
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Create test table if not exists
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS test_mt5_db(
        id SERIAL PRIMARY KEY,
        balance NUMERIC,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """))

    # Insert MT5 account info
    conn.execute(
        text("INSERT INTO test_mt5_db(balance) VALUES(:bal)"),
        {"bal": account_info.balance}
    )

    # Retrieve it
    result = conn.execute(text("SELECT * FROM test_mt5_db ORDER BY id DESC LIMIT 1"))
    print("Database write/read OK:", result.fetchone())

mt5.shutdown()
