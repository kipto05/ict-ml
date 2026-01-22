# 1. Load historical data
from src.data.historical.loader import HistoricalDataLoader
from src.data.mt5_connector import MT5Connector

# 2. Stream real-time data
from src.data.streaming.mt5_streamer import MT5Streamer
from src.data.streaming.event_bus import event_bus, EventType
from src.data.mt5_connector import MT5Connector

# 3. Use cache for performance
from src.data.cache.cache_manager import cache_manager
from src.data.repositories.candle_repository import CandleRepository
import datetime


# Define the missing variables
start = datetime.datetime(2024, 1, 1)  # Add start date
end = datetime.datetime(2024, 1, 31)   # Add end date
account_id = 12345                      # Add account_id
repo = CandleRepository()                 # Create repository instance

with MT5Connector() as mt5:
    loader = HistoricalDataLoader(mt5, account_id=12345)
    bars = loader.load_historical_bars("EURUSD", "H1", start, end)
    # All bars are validated MarketBar instances



def on_new_bar(event):
    bar = event.data  # Already validated!
    print(f"New bar: {bar.close}")

event_bus.subscribe(EventType.NEW_BAR, on_new_bar, account_id=12345)

with MT5Connector() as mt5:
    streamer = MT5Streamer(mt5, 12345)
    streamer.subscribe_symbol("EURUSD", "M1")
    streamer.start()


# Check cache first
bars = cache_manager.get_bars("EURUSD", "H1", start, end, account_id)
if not bars:
    # Cache miss - load from database
    bars = repo.get_bars_range("EURUSD", "H1", start, end, account_id)  # Fixed call
    # Cache for next time
    cache_manager.set_bars(bars, "EURUSD", "H1", start, end, account_id)  # Fixed call

