# ============================================================================
# File: src/data/models.py
# Canonical, immutable market data models
# ============================================================================

"""
Canonical market data models.

All market data (historical, live, backtesting) flows through these models.
They are immutable, typed, and guarantee data integrity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from enum import Enum

from src.core.time.time_utils import ensure_utc, is_naive


class OrderType(Enum):
    """Order types for tick data."""
    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MarketBar:
    """
    Immutable representation of a market candle/bar.

    This is the canonical representation used throughout the system.
    All OHLC data must be converted to this format.

    Attributes:
        symbol: Trading symbol (e.g., 'EURUSD')
        timeframe: Timeframe string (e.g., 'H1', 'M15')
        timestamp_utc: Bar open time in UTC (MUST be timezone-aware)
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        tick_volume: Number of ticks in the bar
        real_volume: Real volume (if available, else 0)
        spread: Average spread in points
        account_id: MT5 account identifier
        broker: Broker name (e.g., 'JustMarkets')

    Invariants:
        - timestamp_utc must be timezone-aware (UTC)
        - low <= open <= high
        - low <= close <= high
        - All prices must be positive
        - tick_volume must be >= 0
    """

    symbol: str
    timeframe: str
    timestamp_utc: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    tick_volume: int
    real_volume: int = 0
    spread: int = 0
    account_id: int = 0
    broker: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Validate invariants immediately upon construction.

        This prevents invalid data from ever existing in the system.

        Raises:
            ValueError: If any invariant is violated
        """
        # CRITICAL: Reject naive datetimes
        if is_naive(self.timestamp_utc):
            raise ValueError(
                f"MarketBar timestamp must be timezone-aware UTC. "
                f"Got naive datetime: {self.timestamp_utc}. "
                f"Use datetime(..., tzinfo=timezone.utc)"
            )

        # Ensure UTC (convert if needed)
        object.__setattr__(self, 'timestamp_utc', ensure_utc(self.timestamp_utc))

        # Validate OHLC relationships
        if not (self.low <= self.open <= self.high):
            raise ValueError(
                f"Invalid OHLC: low ({self.low}) <= open ({self.open}) <= high ({self.high}) violated. "
                f"Symbol: {self.symbol}, Time: {self.timestamp_utc}"
            )

        if not (self.low <= self.close <= self.high):
            raise ValueError(
                f"Invalid OHLC: low ({self.low}) <= close ({self.close}) <= high ({self.high}) violated. "
                f"Symbol: {self.symbol}, Time: {self.timestamp_utc}"
            )

        # Validate positive prices
        if self.open <= 0 or self.high <= 0 or self.low <= 0 or self.close <= 0:
            raise ValueError(
                f"All prices must be positive. Got O:{self.open} H:{self.high} L:{self.low} C:{self.close}"
            )

        # Validate volumes
        if self.tick_volume < 0:
            raise ValueError(f"tick_volume must be >= 0, got {self.tick_volume}")

        if self.real_volume < 0:
            raise ValueError(f"real_volume must be >= 0, got {self.real_volume}")

        # Validate spread
        if self.spread < 0:
            raise ValueError(f"spread must be >= 0, got {self.spread}")

        # Validate symbol
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol cannot be empty")

        # Validate timeframe
        if not self.timeframe or not self.timeframe.strip():
            raise ValueError("timeframe cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'timestamp_utc': self.timestamp_utc.isoformat(),
            'open': str(self.open),
            'high': str(self.high),
            'low': str(self.low),
            'close': str(self.close),
            'tick_volume': self.tick_volume,
            'real_volume': self.real_volume,
            'spread': self.spread,
            'account_id': self.account_id,
            'broker': self.broker,
            'metadata': self.metadata,
        }

    @classmethod
    def from_mt5_bar(
            cls,
            symbol: str,
            timeframe: str,
            mt5_bar: Dict[str, Any],
            account_id: int,
            broker: str = "unknown"
    ) -> 'MarketBar':
        """
        Create MarketBar from MT5 raw data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            mt5_bar: Dictionary with 'time', 'open', 'high', 'low', 'close', etc.
            account_id: MT5 account ID
            broker: Broker name

        Returns:
            Validated MarketBar instance

        Raises:
            ValueError: If data is invalid

        Example:
            >>> mt5_data = {
            ...     'time': 1704110400,
            ...     'open': 1.2345,
            ...     'high': 1.2350,
            ...     'low': 1.2340,
            ...     'close': 1.2348,
            ...     'tick_volume': 1500,
            ...     'real_volume': 0,
            ...     'spread': 2
            ... }
            >>> bar = MarketBar.from_mt5_bar('EURUSD', 'H1', mt5_data, 12345)
        """
        from src.core.time.time_utils import timestamp_from_mt5

        try:
            # Convert timestamp to UTC datetime
            timestamp_utc = timestamp_from_mt5(int(mt5_bar['time']))

            # Convert prices to Decimal for precision
            return cls(
                symbol=symbol,
                timeframe=timeframe,
                timestamp_utc=timestamp_utc,
                open=Decimal(str(mt5_bar['open'])),
                high=Decimal(str(mt5_bar['high'])),
                low=Decimal(str(mt5_bar['low'])),
                close=Decimal(str(mt5_bar['close'])),
                tick_volume=int(mt5_bar.get('tick_volume', 0)),
                real_volume=int(mt5_bar.get('real_volume', 0)),
                spread=int(mt5_bar.get('spread', 0)),
                account_id=account_id,
                broker=broker,
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in MT5 data: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid MT5 bar data: {e}")


@dataclass(frozen=True)
class Tick:
    """
    Immutable representation of a market tick.

    Used for tick-level analysis and ultra-precise entry timing.

    Attributes:
        symbol: Trading symbol
        timestamp_utc: Tick timestamp in UTC
        bid: Bid price
        ask: Ask price
        last: Last trade price
        volume: Tick volume
        flags: Tick flags (buy/sell indicator)
        account_id: MT5 account identifier
        broker: Broker name
    """

    symbol: str
    timestamp_utc: datetime
    bid: Decimal
    ask: Decimal
    last: Decimal = Decimal('0')
    volume: int = 0
    flags: int = 0
    account_id: int = 0
    broker: str = "unknown"

    def __post_init__(self):
        """Validate tick data invariants."""
        if is_naive(self.timestamp_utc):
            raise ValueError(
                f"Tick timestamp must be timezone-aware UTC. "
                f"Got naive datetime: {self.timestamp_utc}"
            )

        object.__setattr__(self, 'timestamp_utc', ensure_utc(self.timestamp_utc))

        # Validate bid/ask relationship
        if self.ask < self.bid:
            raise ValueError(
                f"Invalid tick: ask ({self.ask}) < bid ({self.bid}). "
                f"Symbol: {self.symbol}, Time: {self.timestamp_utc}"
            )

        # Validate positive prices
        if self.bid <= 0 or self.ask <= 0:
            raise ValueError(f"Bid and ask must be positive. Got bid:{self.bid}, ask:{self.ask}")

        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol cannot be empty")

    @property
    def spread(self) -> Decimal:
        """Calculate spread in price units."""
        return self.ask - self.bid

    @property
    def mid(self) -> Decimal:
        """Calculate mid price."""
        return (self.bid + self.ask) / 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'timestamp_utc': self.timestamp_utc.isoformat(),
            'bid': str(self.bid),
            'ask': str(self.ask),
            'last': str(self.last),
            'volume': self.volume,
            'flags': self.flags,
            'account_id': self.account_id,
            'broker': self.broker,
        }


@dataclass(frozen=True)
class SymbolInfo:
    """
    Immutable symbol specification.

    Contains contract specifications needed for calculations.

    Attributes:
        symbol: Trading symbol
        digits: Decimal places
        point: Point size (minimum price change)
        tick_size: Tick size
        tick_value: Tick value in account currency
        contract_size: Contract size (lot size)
        volume_min: Minimum volume
        volume_max: Maximum volume
        volume_step: Volume step
        currency_base: Base currency
        currency_profit: Profit currency
        currency_margin: Margin currency
        spread_typical: Typical spread in points
        account_id: MT5 account identifier
        broker: Broker name
    """

    symbol: str
    digits: int
    point: Decimal
    tick_size: Decimal
    tick_value: Decimal
    contract_size: Decimal
    volume_min: Decimal
    volume_max: Decimal
    volume_step: Decimal
    currency_base: str = ""
    currency_profit: str = ""
    currency_margin: str = ""
    spread_typical: int = 0
    account_id: int = 0
    broker: str = "unknown"

    def __post_init__(self):
        """Validate symbol info."""
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol cannot be empty")

        if self.digits < 0:
            raise ValueError(f"digits must be >= 0, got {self.digits}")

        if self.point <= 0:
            raise ValueError(f"point must be > 0, got {self.point}")

        if self.contract_size <= 0:
            raise ValueError(f"contract_size must be > 0, got {self.contract_size}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'digits': self.digits,
            'point': str(self.point),
            'tick_size': str(self.tick_size),
            'tick_value': str(self.tick_value),
            'contract_size': str(self.contract_size),
            'volume_min': str(self.volume_min),
            'volume_max': str(self.volume_max),
            'volume_step': str(self.volume_step),
            'currency_base': self.currency_base,
            'currency_profit': self.currency_profit,
            'currency_margin': self.currency_margin,
            'spread_typical': self.spread_typical,
            'account_id': self.account_id,
            'broker': self.broker,
        }




