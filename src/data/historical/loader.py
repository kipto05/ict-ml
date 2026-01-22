# ============================================================================
# File: src/data/historical/loader.py
# Historical data ingestion pipeline
# ============================================================================

"""
Historical data ingestion pipeline.

Responsibilities:
- Fetch historical data from MT5
- Convert to canonical MarketBar format
- Validate all data
- Store to database (idempotent)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from src.data.models import MarketBar
from src.data.validation import validator, ValidationError
from src.data.mt5_connector import MT5Connector
from src.core.time.time_utils import ensure_utc
from src.core.logger import main_logger

logger = main_logger


class HistoricalDataLoader:
    """
    Loads historical market data from MT5.

    Features:
    - Idempotent ingestion (can be run multiple times safely)
    - Automatic data validation
    - Gap detection and logging
    - Progress tracking
    """

    def __init__(
            self,
            mt5_connector: MT5Connector,
            account_id: int,
            broker: str = "JustMarkets"
    ):
        """
        Initialize loader.

        Args:
            mt5_connector: Connected MT5Connector instance
            account_id: MT5 account ID
            broker: Broker name
        """
        self.mt5 = mt5_connector
        self.account_id = account_id
        self.broker = broker

        # Statistics
        self.bars_fetched = 0
        self.bars_validated = 0
        self.bars_rejected = 0

    def load_historical_bars(
            self,
            symbol: str,
            timeframe: str,
            start_date: datetime,
            end_date: datetime,
            validate: bool = True,
            strict_validation: bool = True
    ) -> List[MarketBar]:
        """
        Load historical bars from MT5.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (e.g., 'H1', 'M15')
            start_date: Start datetime (UTC)
            end_date: End datetime (UTC)
            validate: If True, validate all bars
            strict_validation: If True, apply strict validation rules

        Returns:
            List of validated MarketBars

        Raises:
            ValueError: If dates are invalid
            ConnectionError: If MT5 connection fails

        Example:
            >>> loader = HistoricalDataLoader(mt5, account_id=12345)
            >>> bars = loader.load_historical_bars(
            ...     'EURUSD',
            ...     'H1',
            ...     datetime(2024, 1, 1, tzinfo=timezone.utc),
            ...     datetime(2024, 1, 31, tzinfo=timezone.utc)
            ... )
            >>> len(bars)
            744  # ~31 days * 24 hours
        """
        # Ensure UTC
        start_date = ensure_utc(start_date)
        end_date = ensure_utc(end_date)

        # Validate date range
        if start_date >= end_date:
            raise ValueError(f"start_date ({start_date}) must be < end_date ({end_date})")

        logger.info(
            f"Loading historical data: {symbol} {timeframe} "
            f"from {start_date} to {end_date}"
        )

        try:
            # Fetch bars from MT5
            df = self.mt5.get_bars_range(symbol, timeframe, start_date, end_date)

            if df.empty:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return []

            self.bars_fetched = len(df)
            logger.info(f"Fetched {self.bars_fetched} bars from MT5")

            # Convert to MarketBar objects
            bars = []
            for idx, row in df.iterrows():
                try:
                    bar_data = {
                        'time': int(idx.timestamp()),
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

                    # Validate if requested
                    if validate:
                        is_valid, reason = validator.validate_bar(bar, strict=strict_validation)
                        if not is_valid:
                            self.bars_rejected += 1
                            logger.warning(f"Bar rejected: {reason}")
                            continue

                    bars.append(bar)
                    self.bars_validated += 1

                except Exception as e:
                    logger.error(f"Error converting bar at {idx}: {e}")
                    self.bars_rejected += 1
                    continue

            # Validate sequence
            if validate and len(bars) > 1:
                is_valid, errors = validator.validate_bar_sequence(bars, allow_gaps=True)
                if not is_valid:
                    logger.warning(f"Sequence validation errors: {errors}")

            logger.info(
                f"Historical load complete: "
                f"{self.bars_validated} validated, "
                f"{self.bars_rejected} rejected"
            )

            return bars

        except Exception as e:
            logger.error(f"Historical data load failed: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Get loader statistics."""
        return {
            'bars_fetched': self.bars_fetched,
            'bars_validated': self.bars_validated,
            'bars_rejected': self.bars_rejected,
            'rejection_rate': (
                self.bars_rejected / self.bars_fetched
                if self.bars_fetched > 0 else 0.0
            ),
        }

    def reset_statistics(self):
        """Reset loader statistics."""
        self.bars_fetched = 0
        self.bars_validated = 0
        self.bars_rejected = 0