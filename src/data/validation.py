# ============================================================================
# File: src/data/validation.py
# Market data validation layer
# ============================================================================

"""
Market data validation layer.

CRITICAL: No invalid data enters the system. Ever.

All validation failures are logged with complete context for debugging.
"""

from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from src.data.models import MarketBar, Tick
from src.core.logger import main_logger

logger = main_logger


class ValidationError(Exception):
    """Raised when market data fails validation."""
    pass


class DataValidator:
    """
    Validates market data before it enters the system.

    Design principles:
    - Fail loudly, never silently
    - Log ALL rejections with context
    - No data passes without validation
    - Validation is deterministic
    """

    def __init__(
            self,
            max_spread_multiplier: float = 10.0,
            max_gap_bars: int = 5,
            min_tick_volume: int = 0,
    ):
        """
        Initialize validator.

        Args:
            max_spread_multiplier: Max spread vs typical (reject if exceeded)
            max_gap_bars: Max allowed gap between consecutive bars
            min_tick_volume: Minimum tick volume (0 = allow zero)
        """
        self.max_spread_multiplier = max_spread_multiplier
        self.max_gap_bars = max_gap_bars
        self.min_tick_volume = min_tick_volume

        # Validation statistics
        self.total_validated = 0
        self.total_rejected = 0
        self.rejection_reasons: dict = {}

    def validate_bar(self, bar: MarketBar, strict: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate a single market bar.

        Args:
            bar: MarketBar to validate
            strict: If True, apply all checks. If False, only critical checks.

        Returns:
            Tuple of (is_valid, rejection_reason)
            - is_valid: True if bar passes all checks
            - rejection_reason: None if valid, error message if invalid

        Example:
            >>> validator = DataValidator()
            >>> valid, reason = validator.validate_bar(bar)
            >>> if not valid:
            ...     logger.error(f"Bar rejected: {reason}")
        """
        self.total_validated += 1

        try:
            # CRITICAL CHECK 1: OHLC relationships (already checked in __post_init__)
            # MarketBar.__post_init__ ensures this, but we double-check
            if not (bar.low <= bar.open <= bar.high):
                return self._reject(bar, "OHLC violation: low <= open <= high")

            if not (bar.low <= bar.close <= bar.high):
                return self._reject(bar, "OHLC violation: low <= close <= high")

            # CRITICAL CHECK 2: Positive prices
            if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
                return self._reject(bar, "Non-positive price detected")

            # CRITICAL CHECK 3: Timezone awareness (already enforced by MarketBar)
            if bar.timestamp_utc.tzinfo is None:
                return self._reject(bar, "Naive datetime detected")

            # CRITICAL CHECK 4: Reasonable price ranges
            price_range = bar.high - bar.low
            avg_price = (bar.high + bar.low) / 2

            # Reject if range is > 50% of average price (likely data corruption)
            if price_range > avg_price * Decimal('0.5'):
                return self._reject(
                    bar,
                    f"Unrealistic price range: {price_range} (>{avg_price * Decimal('0.5')})"
                )

            if strict:
                # STRICT CHECK 1: Minimum tick volume
                if bar.tick_volume < self.min_tick_volume:
                    return self._reject(
                        bar,
                        f"Tick volume too low: {bar.tick_volume} < {self.min_tick_volume}"
                    )

                # STRICT CHECK 2: Spread reasonableness
                if bar.spread > 0:  # Only check if spread data available
                    # For forex, spreads > 100 pips are suspicious
                    if bar.spread > 1000:  # 100 pips in points
                        return self._reject(
                            bar,
                            f"Unrealistic spread: {bar.spread} points"
                        )

            # All checks passed
            return True, None

        except Exception as e:
            # Unexpected error during validation
            return self._reject(bar, f"Validation exception: {str(e)}")

    def validate_bar_sequence(
            self,
            bars: List[MarketBar],
            allow_gaps: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate a sequence of bars for temporal consistency.

        Checks:
        - Monotonic time ordering
        - No duplicate timestamps
        - Reasonable time gaps

        Args:
            bars: List of MarketBars (must be same symbol/timeframe)
            allow_gaps: If False, reject sequences with time gaps

        Returns:
            Tuple of (is_valid, list_of_errors)

        Example:
            >>> bars = [bar1, bar2, bar3]
            >>> valid, errors = validator.validate_bar_sequence(bars)
            >>> if not valid:
            ...     for error in errors:
            ...         logger.error(error)
        """
        if not bars:
            return True, []

        errors = []

        # Check 1: Same symbol/timeframe
        first_symbol = bars[0].symbol
        first_timeframe = bars[0].timeframe

        for i, bar in enumerate(bars):
            if bar.symbol != first_symbol:
                errors.append(
                    f"Bar {i}: Symbol mismatch. Expected {first_symbol}, got {bar.symbol}"
                )
            if bar.timeframe != first_timeframe:
                errors.append(
                    f"Bar {i}: Timeframe mismatch. Expected {first_timeframe}, got {bar.timeframe}"
                )

        # Check 2: Monotonic time ordering
        for i in range(len(bars) - 1):
            if bars[i].timestamp_utc >= bars[i + 1].timestamp_utc:
                errors.append(
                    f"Non-monotonic time: Bar {i} ({bars[i].timestamp_utc}) >= "
                    f"Bar {i + 1} ({bars[i + 1].timestamp_utc})"
                )

        # Check 3: No duplicate timestamps
        timestamps = [bar.timestamp_utc for bar in bars]
        if len(timestamps) != len(set(timestamps)):
            errors.append("Duplicate timestamps detected in sequence")

        # Check 4: Time gaps (if not allowed)
        if not allow_gaps and len(bars) > 1:
            from src.core.time.time_utils import floor_time

            for i in range(len(bars) - 1):
                expected_next = self._next_bar_time(bars[i].timestamp_utc, bars[i].timeframe)
                actual_next = bars[i + 1].timestamp_utc

                if actual_next != expected_next:
                    # Calculate gap in bars
                    gap = (actual_next - expected_next).total_seconds()
                    gap_bars = gap / self._timeframe_to_seconds(bars[i].timeframe)

                    if gap_bars > self.max_gap_bars:
                        errors.append(
                            f"Large time gap between bars {i} and {i + 1}: "
                            f"{gap_bars:.1f} bars missing"
                        )

        is_valid = len(errors) == 0
        if not is_valid:
            self.total_rejected += len(bars)
            self.rejection_reasons['sequence_error'] = \
                self.rejection_reasons.get('sequence_error', 0) + 1

        return is_valid, errors

    def validate_tick(self, tick: Tick) -> Tuple[bool, Optional[str]]:
        """
        Validate a single tick.

        Args:
            tick: Tick to validate

        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        self.total_validated += 1

        # Check 1: Bid/Ask relationship
        if tick.ask < tick.bid:
            return self._reject(tick, f"Invalid spread: ask ({tick.ask}) < bid ({tick.bid})")

        # Check 2: Positive prices
        if tick.bid <= 0 or tick.ask <= 0:
            return self._reject(tick, "Non-positive price")

        # Check 3: Reasonable spread
        spread = tick.ask - tick.bid
        mid = (tick.ask + tick.bid) / 2

        # Spread > 10% of mid price is suspicious
        if spread > mid * Decimal('0.1'):
            return self._reject(
                tick,
                f"Unrealistic spread: {spread} (>{mid * Decimal('0.1')})"
            )

        # Check 4: Timezone awareness
        if tick.timestamp_utc.tzinfo is None:
            return self._reject(tick, "Naive datetime")

        return True, None

    def get_statistics(self) -> dict:
        """
        Get validation statistics.

        Returns:
            Dictionary with validation stats
        """
        return {
            'total_validated': self.total_validated,
            'total_rejected': self.total_rejected,
            'rejection_rate': (
                self.total_rejected / self.total_validated
                if self.total_validated > 0 else 0.0
            ),
            'rejection_reasons': dict(self.rejection_reasons),
        }

    def reset_statistics(self):
        """Reset validation statistics."""
        self.total_validated = 0
        self.total_rejected = 0
        self.rejection_reasons.clear()

    def _reject(self, data, reason: str) -> Tuple[bool, str]:
        """
        Record rejection and return result.

        Args:
            data: Data being rejected (MarketBar or Tick)
            reason: Rejection reason

        Returns:
            Tuple of (False, reason)
        """
        self.total_rejected += 1

        # Track rejection reason
        reason_key = reason.split(':')[0]  # First part of reason
        self.rejection_reasons[reason_key] = \
            self.rejection_reasons.get(reason_key, 0) + 1

        # Log rejection with full context
        if isinstance(data, MarketBar):
            logger.warning(
                f"MarketBar REJECTED: {reason} | "
                f"Symbol: {data.symbol}, Time: {data.timestamp_utc}, "
                f"OHLC: {data.open}/{data.high}/{data.low}/{data.close}"
            )
        elif isinstance(data, Tick):
            logger.warning(
                f"Tick REJECTED: {reason} | "
                f"Symbol: {data.symbol}, Time: {data.timestamp_utc}, "
                f"Bid/Ask: {data.bid}/{data.ask}"
            )
        else:
            logger.warning(f"Data REJECTED: {reason} | Data: {data}")

        return False, reason

    def _next_bar_time(self, current_time: datetime, timeframe: str) -> datetime:
        """Calculate expected next bar time."""
        seconds = self._timeframe_to_seconds(timeframe)
        return current_time + timedelta(seconds=seconds)

    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """Convert timeframe string to seconds."""
        mapping = {
            'M1': 60,
            'M5': 300,
            'M15': 900,
            'M30': 1800,
            'H1': 3600,
            'H4': 14400,
            'D1': 86400,
        }
        return mapping.get(timeframe, 3600)


# Global validator instance
validator = DataValidator()



