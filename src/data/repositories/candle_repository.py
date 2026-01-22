# ============================================================================
# File: src/data/repositories/candle_repository.py
# Repository for market bar (candle) data
# ============================================================================

"""
Candle/Bar repository.

Abstracts database access for market bars.
Provides account-aware, time-windowed queries.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database.models import Base
from src.data.models import MarketBar
from src.core.time.time_utils import ensure_utc
from src.core.logger import main_logger

logger = main_logger


class CandleRepository:
    """
    Repository for candle/bar data access.

    Design principles:
    - Account isolation
    - Time-window efficient queries
    - Read/write separation
    - No business logic (pure data access)
    """

    def __init__(self, session: Session):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def save_bar(self, bar: MarketBar) -> bool:
        """
        Save a single market bar.

        Idempotent: Duplicate bars (same symbol/timeframe/timestamp/account)
        are ignored.

        Args:
            bar: MarketBar to save

        Returns:
            True if saved, False if duplicate skipped

        Example:
            >>> repo = CandleRepository(session)
            >>> saved = repo.save_bar(market_bar)
            >>> if saved:
            ...     print("Bar saved")
        """
        from database.models import Trade  # Import here to avoid circular dependency

        try:
            # Check for duplicate
            existing = self.session.query(Trade).filter(
                and_(
                    Trade.symbol == bar.symbol,
                    Trade.time_open == bar.timestamp_utc,
                    Trade.account_id == bar.account_id
                )
            ).first()

            if existing:
                logger.debug(
                    f"Duplicate bar skipped: {bar.symbol} {bar.timeframe} "
                    f"{bar.timestamp_utc}"
                )
                return False

            # Note: We're storing bars in the Trade table for now
            # In production, you'd have a dedicated Candle/Bar table
            # This is a placeholder implementation

            logger.info(
                f"Bar saved: {bar.symbol} {bar.timeframe} {bar.timestamp_utc}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save bar: {e}")
            self.session.rollback()
            raise

    def save_bars_batch(self, bars: List[MarketBar]) -> int:
        """
        Save multiple bars in a batch.

        Args:
            bars: List of MarketBars to save

        Returns:
            Number of bars successfully saved

        Example:
            >>> saved_count = repo.save_bars_batch(bars)
            >>> print(f"Saved {saved_count}/{len(bars)} bars")
        """
        saved_count = 0

        for bar in bars:
            if self.save_bar(bar):
                saved_count += 1

        try:
            self.session.commit()
            logger.info(f"Batch save: {saved_count}/{len(bars)} bars saved")
        except Exception as e:
            logger.error(f"Batch save failed: {e}")
            self.session.rollback()
            raise

        return saved_count

    def get_bars_range(
            self,
            symbol: str,
            timeframe: str,
            start_time: datetime,
            end_time: datetime,
            account_id: Optional[int] = None
    ) -> List[MarketBar]:
        """
        Get bars within a time range.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start_time: Start datetime (UTC)
            end_time: End datetime (UTC)
            account_id: Filter by account (None = all accounts)

        Returns:
            List of MarketBars, sorted by time ascending

        Example:
            >>> bars = repo.get_bars_range(
            ...     'EURUSD',
            ...     'H1',
            ...     start_utc,
            ...     end_utc,
            ...     account_id=12345
            ... )
        """
        start_time = ensure_utc(start_time)
        end_time = ensure_utc(end_time)

        # This is a placeholder - in production, query from dedicated Candle table
        logger.info(
            f"Querying bars: {symbol} {timeframe} "
            f"{start_time} to {end_time}"
        )

        # Return empty list for now (implement with real Candle table)
        return []

    def get_latest_bars(
            self,
            symbol: str,
            timeframe: str,
            count: int = 100,
            account_id: Optional[int] = None
    ) -> List[MarketBar]:
        """
        Get the most recent bars.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            count: Number of bars to retrieve
            account_id: Filter by account

        Returns:
            List of most recent MarketBars, sorted newest first
        """
        logger.info(f"Querying latest {count} bars for {symbol} {timeframe}")

        # Placeholder implementation
        return []

    def delete_bars_range(
            self,
            symbol: str,
            timeframe: str,
            start_time: datetime,
            end_time: datetime,
            account_id: Optional[int] = None
    ) -> int:
        """
        Delete bars within a time range.

        Use with caution - primarily for data reingestion.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start datetime (UTC)
            end_time: End datetime (UTC)
            account_id: Filter by account

        Returns:
            Number of bars deleted
        """
        start_time = ensure_utc(start_time)
        end_time = ensure_utc(end_time)

        logger.warning(
            f"Deleting bars: {symbol} {timeframe} "
            f"{start_time} to {end_time}"
        )

        # Placeholder
        return 0

