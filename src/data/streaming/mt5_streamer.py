# ============================================================================
# File: src/data/streaming/mt5_streamer.py
# Real-time MT5 data streamer
# ============================================================================

"""
Real-time MT5 data streamer.

Streams validated market data from MT5 to the event bus.
"""

from typing import Dict, Set, Any
from datetime import datetime
import time
import threading

from src.data.models import MarketBar, Tick
from src.data.validation import validator
from src.data.streaming.event_bus import event_bus, EventType, MarketEvent
from src.data.mt5_connector import MT5Connector
from src.core.time.time_utils import timestamp_from_mt5
from src.core.logger import main_logger

logger = main_logger


class MT5Streamer:
    """
    Real-time market data streamer.

    Features:
    - Multi-symbol streaming
    - Automatic validation
    - Event-driven architecture
    - Thread-safe
    """

    def __init__(
            self,
            mt5_connector: MT5Connector,
            account_id: int,
            broker: str = "JustMarkets"
    ):
        """
        Initialize streamer.

        Args:
            mt5_connector: Connected MT5 instance
            account_id: MT5 account ID
            broker: Broker name
        """
        self.mt5 = mt5_connector
        self.account_id = account_id
        self.broker = broker

        # Streaming state
        self.is_streaming = False
        self.subscribed_symbols: Set[str] = set()

        # Last bar cache (to detect new bars)
        self._last_bar_time: Dict[str, datetime] = {}

        # Statistics
        self.bars_streamed = 0
        self.bars_rejected = 0

    def subscribe_symbol(
            self,
            symbol: str,
            timeframe: str = "M1"
    ) -> None:
        """
        Subscribe to symbol updates.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe to stream

        Example:
            >>> streamer = MT5Streamer(mt5, account_id=12345)
            >>> streamer.subscribe_symbol('EURUSD', 'M1')
            >>> streamer.start()
        """
        key = f"{symbol}:{timeframe}"
        self.subscribed_symbols.add(key)
        logger.info(f"Subscribed to {symbol} {timeframe}")

    def unsubscribe_symbol(self, symbol: str, timeframe: str = "M1") -> None:
        """Unsubscribe from symbol updates."""
        key = f"{symbol}:{timeframe}"
        self.subscribed_symbols.discard(key)
        logger.info(f"Unsubscribed from {symbol} {timeframe}")

    def start(self, poll_interval: float = 1.0) -> None:
        """
        Start streaming.

        Args:
            poll_interval: Polling interval in seconds

        Note:
            This is a blocking call. Run in separate thread for async.
        """
        if self.is_streaming:
            logger.warning("Streamer already running")
            return

        self.is_streaming = True
        logger.info("MT5 Streamer started")

        try:
            while self.is_streaming:
                self._poll_updates()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Streamer interrupted")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop streaming."""
        self.is_streaming = False
        logger.info("MT5 Streamer stopped")

    def _poll_updates(self) -> None:
        """Poll MT5 for updates and emit events."""
        for symbol_key in list(self.subscribed_symbols):
            try:
                symbol, timeframe = symbol_key.split(':')
                self._check_symbol_update(symbol, timeframe)
            except Exception as e:
                logger.error(f"Error polling {symbol_key}: {e}")

    def _check_symbol_update(self, symbol: str, timeframe: str) -> None:
        """Check for new bars on a symbol."""
        try:
            # Get latest bar
            df = self.mt5.get_bars(symbol, timeframe, count=1)

            if df.empty:
                return

            # Convert to MarketBar
            row = df.iloc[0]
            bar_data = {
                'time': int(df.index[0].timestamp()),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'tick_volume': int(row.get('tick_volume', 0)),
                'real_volume': int(row.get('real_volume', 0)),
                'spread': int(row.get('spread', 0)),
            }

            bar = MarketBar.from_mt5_bar(
                symbol=symbol,
                timeframe=timeframe,
                mt5_bar=bar_data,
                account_id=self.account_id,
                broker=self.broker
            )

            # Check if this is a new bar
            key = f"{symbol}:{timeframe}"
            last_time = self._last_bar_time.get(key)

            if last_time is None or bar.timestamp_utc > last_time:
                # New bar detected
                self._process_new_bar(bar)
                self._last_bar_time[key] = bar.timestamp_utc

        except Exception as e:
            logger.error(f"Error checking {symbol} {timeframe}: {e}")

    def _process_new_bar(self, bar: MarketBar) -> None:
        """Process and emit new bar."""
        # Validate bar
        is_valid, reason = validator.validate_bar(bar, strict=False)

        if not is_valid:
            self.bars_rejected += 1
            logger.warning(f"Bar rejected in stream: {reason}")
            return

        # Bar is valid - emit event
        event = MarketEvent(
            event_type=EventType.NEW_BAR,
            symbol=bar.symbol,
            account_id=bar.account_id,
            timestamp=bar.timestamp_utc,
            data=bar,
        )

        subscribers_notified = event_bus.publish(event)
        self.bars_streamed += 1

        logger.debug(
            f"New bar: {bar.symbol} {bar.timeframe} {bar.timestamp_utc} "
            f"(notified {subscribers_notified} subscribers)"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get streamer statistics."""
        return {
            'is_streaming': self.is_streaming,
            'subscribed_symbols': len(self.subscribed_symbols),
            'bars_streamed': self.bars_streamed,
            'bars_rejected': self.bars_rejected,
        }

