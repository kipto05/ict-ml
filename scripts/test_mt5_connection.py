import os
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

MT5_PATH = os.getenv("MT5_PATH")

if not mt5.initialize(path=MT5_PATH):
    print("❌ MT5 initialize failed")
    print(mt5.last_error())
    exit()

info = mt5.account_info()
if info is None:
    print("❌ Account info failed")
else:
    print("✅ MT5 CONNECTED VIA .env")
    print(f"Login: {info.login}")
    print(f"Balance: {info.balance}")
    print(f"Server: {info.server}")

mt5.shutdown()
