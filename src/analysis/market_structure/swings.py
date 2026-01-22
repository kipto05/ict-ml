# ============================================================================
# File: src/analysis/market_structure/swings.py
# Objective swing detection with parameterized lookback
# ============================================================================

"""
Swing detection engine.

Detects swing highs and swing lows objectively using configurable lookback.
No subjective interpretation - purely rule-based.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum

from src.data.models import MarketBar


class SwingType(Enum):
    """Swing point types."""
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True)
class SwingPoint:
    """
    Immutable swing point representation.

    Attributes:
        timestamp: When swing occurred (UTC)
        price: Swing price level
        swing_type: HIGH or LOW
        bar_index: Position in bar sequence
        lookback: Lookback window used for detection
        strength: Number of bars confirming swing
    """
    timestamp: datetime
    price: Decimal
    swing_type: SwingType
    bar_index: int
    lookback: int
    strength: int = 0

    def __post_init__(self):
        """Validate swing point."""
        if self.price <= 0:
            raise ValueError(f"Swing price must be positive, got {self.price}")
        if self.lookback < 1:
            raise ValueError(f"Lookback must be >= 1, got {self.lookback}")
        if self.bar_index < 0:
            raise ValueError(f"Bar index must be >= 0, got {self.bar_index}")


class SwingDetector:
    """
    Detects swing highs and lows in price data.

    Design principles:
    - Deterministic: Same input = same output
    - Parameterized: Configurable lookback
    - No repainting: Uses confirmed bars only
    - No future data: Only looks backward
    """

    def __init__(self, lookback: int = 5):
        """
        Initialize swing detector.

        Args:
            lookback: Number of bars to left and right for swing confirmation
                     (5 = 5 bars left + swing bar + 5 bars right = 11 bar window)

        Raises:
            ValueError: If lookback < 1
        """
        if lookback < 1:
            raise ValueError(f"Lookback must be >= 1, got {lookback}")

        self.lookback = lookback

        # Statistics
        self.swings_detected = 0
        self.highs_detected = 0
        self.lows_detected = 0

    def detect_swings(self, bars: List[MarketBar]) -> List[SwingPoint]:
        """
        Detect all swing points in bar sequence.

        Args:
            bars: List of MarketBars (must be time-ordered)

        Returns:
            List of SwingPoints (time-ordered)

        Raises:
            ValueError: If bars are not time-ordered

        Example:
            >>> detector = SwingDetector(lookback=5)
            >>> swings = detector.detect_swings(bars)
            >>> highs = [s for s in swings if s.swing_type == SwingType.HIGH]
        """
        if not bars:
            return []

        # Validate time ordering
        self._validate_bar_sequence(bars)

        swings = []

        # Need at least (lookback * 2 + 1) bars for first swing
        min_bars = (self.lookback * 2) + 1

        if len(bars) < min_bars:
            return []

        # Detect swings (exclude last 'lookback' bars - not confirmed yet)
        for i in range(self.lookback, len(bars) - self.lookback):
            # Check for swing high
            if self._is_swing_high(bars, i):
                swing = SwingPoint(
                    timestamp=bars[i].timestamp_utc,
                    price=bars[i].high,
                    swing_type=SwingType.HIGH,
                    bar_index=i,
                    lookback=self.lookback,
                    strength=self._calculate_strength(bars, i, SwingType.HIGH)
                )
                swings.append(swing)
                self.swings_detected += 1
                self.highs_detected += 1

            # Check for swing low
            if self._is_swing_low(bars, i):
                swing = SwingPoint(
                    timestamp=bars[i].timestamp_utc,
                    price=bars[i].low,
                    swing_type=SwingType.LOW,
                    bar_index=i,
                    lookback=self.lookback,
                    strength=self._calculate_strength(bars, i, SwingType.LOW)
                )
                swings.append(swing)
                self.swings_detected += 1
                self.lows_detected += 1

        # Sort by time (should already be sorted, but ensure)
        swings.sort(key=lambda s: s.timestamp)

        return swings

    def _is_swing_high(self, bars: List[MarketBar], index: int) -> bool:
        """
        Check if bar at index is a swing high.

        Swing high definition:
        - High at index > all highs in lookback window (left)
        - High at index >= all highs in lookback window (right)

        Args:
            bars: Bar sequence
            index: Index to check

        Returns:
            True if swing high
        """
        center_high = bars[index].high

        # Check left side (must be strictly greater)
        for i in range(index - self.lookback, index):
            if bars[i].high >= center_high:
                return False

        # Check right side (can be equal)
        for i in range(index + 1, index + self.lookback + 1):
            if bars[i].high > center_high:
                return False

        return True

    def _is_swing_low(self, bars: List[MarketBar], index: int) -> bool:
        """
        Check if bar at index is a swing low.

        Swing low definition:
        - Low at index < all lows in lookback window (left)
        - Low at index <= all lows in lookback window (right)

        Args:
            bars: Bar sequence
            index: Index to check

        Returns:
            True if swing low
        """
        center_low = bars[index].low

        # Check left side (must be strictly less)
        for i in range(index - self.lookback, index):
            if bars[i].low <= center_low:
                return False

        # Check right side (can be equal)
        for i in range(index + 1, index + self.lookback + 1):
            if bars[i].low < center_low:
                return False

        return True

    def _calculate_strength(
            self,
            bars: List[MarketBar],
            index: int,
            swing_type: SwingType
    ) -> int:
        """
        Calculate swing strength (how many bars respect it).

        Higher strength = more significant swing.

        Args:
            bars: Bar sequence
            index: Swing bar index
            swing_type: HIGH or LOW

        Returns:
            Strength value (number of confirming bars)
        """
        strength = 0
        swing_price = bars[index].high if swing_type == SwingType.HIGH else bars[index].low

        # Count how many bars on each side respect the swing
        if swing_type == SwingType.HIGH:
            # Count bars below swing high
            for i in range(index - self.lookback, index + self.lookback + 1):
                if i != index and bars[i].high < swing_price:
                    strength += 1
        else:
            # Count bars above swing low
            for i in range(index - self.lookback, index + self.lookback + 1):
                if i != index and bars[i].low > swing_price:
                    strength += 1

        return strength

    def _validate_bar_sequence(self, bars: List[MarketBar]) -> None:
        """
        Validate bars are time-ordered.

        Raises:
            ValueError: If bars are not monotonically increasing
        """
        for i in range(len(bars) - 1):
            if bars[i].timestamp_utc >= bars[i + 1].timestamp_utc:
                raise ValueError(
                    f"Bars must be time-ordered. "
                    f"Bar {i} ({bars[i].timestamp_utc}) >= "
                    f"Bar {i + 1} ({bars[i + 1].timestamp_utc})"
                )

    def get_last_swing_high(self, swings: List[SwingPoint]) -> Optional[SwingPoint]:
        """Get most recent swing high."""
        highs = [s for s in swings if s.swing_type == SwingType.HIGH]
        return highs[-1] if highs else None

    def get_last_swing_low(self, swings: List[SwingPoint]) -> Optional[SwingPoint]:
        """Get most recent swing low."""
        lows = [s for s in swings if s.swing_type == SwingType.LOW]
        return lows[-1] if lows else None

    def get_statistics(self) -> dict:
        """Get detector statistics."""
        return {
            'lookback': self.lookback,
            'total_swings': self.swings_detected,
            'highs': self.highs_detected,
            'lows': self.lows_detected,
        }

    def reset_statistics(self) -> None:
        """Reset detector statistics."""
        self.swings_detected = 0
        self.highs_detected = 0
        self.lows_detected = 0