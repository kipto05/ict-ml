import datetime
from typing import List, Optional
import pytz

from src.data.models import MarketBar
from src.data.repositories.candle_repository import CandleRepository
from src.data.cache.cache_manager import cache_manager
from src.data.historical.loader import HistoricalDataLoader
from src.data.mt5_connector import MT5Connector
from src.data.streaming.mt5_streamer import MT5Streamer
from src.data.streaming.event_bus import event_bus, EventType
from src.data.streaming.event_bus import MarketEvent


# ---------------------------------------------------------------------------
# Time configuration
# ---------------------------------------------------------------------------

start = datetime.datetime(2024, 1, 1)
end = datetime.datetime(2024, 1, 31)
account_id = 12345

utc_tz = pytz.UTC
local_tz = pytz.timezone("America/New_York")

start_utc = local_tz.localize(start).astimezone(utc_tz) if start.tzinfo is None else start.astimezone(utc_tz)
end_utc = local_tz.localize(end).astimezone(utc_tz) if end.tzinfo is None else end.astimezone(utc_tz)


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

repo = CandleRepository()


# ---------------------------------------------------------------------------
# CACHE-FIRST DATA LOADER
# ---------------------------------------------------------------------------

def get_bars_with_cache_fallback(
        symbol: str,
        timeframe: str,
        start: datetime.datetime,
        end: datetime.datetime,
        account_id: int,
        cache_ttl: int = 300,
        force_refresh: bool = False,
        save_to_db: bool = True,
        use_timezone_conversion: bool = True
) -> List[MarketBar]:

    if start >= end:
        raise ValueError("Start time must be before end time")

    query_start = start_utc if use_timezone_conversion else start
    query_end = end_utc if use_timezone_conversion else end

    # -------------------------------------------------------------------
    # 1. CACHE FIRST
    # -------------------------------------------------------------------
    if not force_refresh:
        bars = cache_manager.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start,
            end_time=end,
            account_id=account_id
        )

        if bars:
            print(f"Cache HIT: {len(bars)} bars")
            return bars

    print("Cache MISS → checking database")

    # -------------------------------------------------------------------
    # 2. DATABASE
    # -------------------------------------------------------------------
    try:
        bars = repo.get_bars_range(symbol, timeframe, start, end, account_id)

        if bars:
            cache_manager.set_bars(
                bars=bars,
                symbol=symbol,
                timeframe=timeframe,
                start_time=start,
                end_time=end,
                account_id=account_id,
                ttl_seconds=cache_ttl
            )
            print(f"Loaded {len(bars)} bars from database")
            return bars

    except Exception as db_error:
        print(f"Database error: {db_error}")

    print("Database MISS → falling back to MT5")

    # -------------------------------------------------------------------
    # 3. MT5 FALLBACK
    # -------------------------------------------------------------------
    with MT5Connector() as mt5:
        loader = HistoricalDataLoader(mt5, account_id)
        bars = loader.load_historical_bars(
            symbol, timeframe, query_start, query_end
        )

        if not bars:
            return []

        if save_to_db:
            try:
                repo.save_bars(bars)
            except Exception as e:
                print(f"Warning: DB save failed: {e}")

        cache_manager.set_bars(
            bars=bars,
            symbol=symbol,
            timeframe=timeframe,
            start_time=start,
            end_time=end,
            account_id=account_id,
            ttl_seconds=cache_ttl
        )

        print(f"Loaded & cached {len(bars)} bars from MT5")
        return bars


# ---------------------------------------------------------------------------
# USAGE EXAMPLE
# ---------------------------------------------------------------------------

bars = get_bars_with_cache_fallback(
    symbol="EURUSD",
    timeframe="H1",
    start=start,
    end=end,
    account_id=account_id
)

print(f"Retrieved {len(bars)} bars")


# ---------------------------------------------------------------------------
# STREAMING
# ---------------------------------------------------------------------------

def on_new_bar(event: MarketEvent):
    bar = event.data
    print(f"New bar: {bar.symbol} {bar.timeframe} Close={bar.close}")


def start_streaming_with_retry(
        symbols: List[str],
        timeframes: List[str],
        account_id: int,
        retries: int = 3
) -> Optional[MT5Streamer]:

    for attempt in range(retries):
        try:
            event_bus.subscribe(EventType.NEW_BAR, on_new_bar, account_id=account_id)

            with MT5Connector() as mt5:
                streamer = MT5Streamer(mt5, account_id)
                for symbol, tf in zip(symbols, timeframes):
                    streamer.subscribe_symbol(symbol, tf)

                streamer.start()
                return streamer

        except ConnectionError:
            print(f"Retry {attempt + 1}/{retries}")

    return None
