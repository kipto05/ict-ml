# ============================================================================
# File: src/analysis/market_structure/structure.py
# Overall structure analysis
# ============================================================================

"""
Market structure analysis.

Determines overall trend state and structure quality.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from datetime import datetime

from src.analysis.market_structure.swings import SwingPoint, SwingType
from src.core.logger import main_logger

logger = main_logger


class TrendState(Enum):
    """Market trend state."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGING = "ranging"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class StructureState:
    """
    Overall market structure state.

    Attributes:
        trend: Current trend state
        last_swing_high: Most recent swing high
        last_swing_low: Most recent swing low
        higher_highs: Count of consecutive higher highs
        lower_lows: Count of consecutive lower lows
        timestamp: State timestamp
    """
    trend: TrendState
    last_swing_high: Optional[SwingPoint]
    last_swing_low: Optional[SwingPoint]
    higher_highs: int = 0
    lower_lows: int = 0
    timestamp: Optional[datetime] = None


class StructureAnalyzer:
    """
    Analyzes overall market structure.

    Determines trend state based on swing point progression.

    Rules:
    - Bullish: Higher highs AND higher lows
    - Bearish: Lower lows AND lower highs
    - Ranging: Mixed or no clear direction
    """

    def __init__(self, min_swings_for_trend: int = 2):
        """
        Initialize analyzer.

        Args:
            min_swings_for_trend: Minimum swing count to confirm trend
        """
        self.min_swings_for_trend = min_swings_for_trend

    def analyze_structure(self, swings: List[SwingPoint]) -> StructureState:
        """
        Analyze structure from swing points.

        Args:
            swings: List of swing points (time-ordered)

        Returns:
            StructureState with trend determination
        """
        if not swings:
            return StructureState(
                trend=TrendState.UNKNOWN,
                last_swing_high=None,
                last_swing_low=None,
            )

        # Separate highs and lows
        highs = [s for s in swings if s.swing_type == SwingType.HIGH]
        lows = [s for s in swings if s.swing_type == SwingType.LOW]

        # Get latest swings
        last_high = highs[-1] if highs else None
        last_low = lows[-1] if lows else None

        # Count higher highs
        higher_highs_count = 0
        if len(highs) >= 2:
            for i in range(1, len(highs)):
                if highs[i].price > highs[i - 1].price:
                    higher_highs_count += 1
                else:
                    higher_highs_count = 0  # Reset on break

        # Count lower lows
        lower_lows_count = 0
        if len(lows) >= 2:
            for i in range(1, len(lows)):
                if lows[i].price < lows[i - 1].price:
                    lower_lows_count += 1
                else:
                    lower_lows_count = 0  # Reset on break

        # Determine trend
        trend = self._determine_trend(
            highs, lows, higher_highs_count, lower_lows_count
        )

        latest_timestamp = swings[-1].timestamp if swings else None

        return StructureState(
            trend=trend,
            last_swing_high=last_high,
            last_swing_low=last_low,
            higher_highs=higher_highs_count,
            lower_lows=lower_lows_count,
            timestamp=latest_timestamp,
        )

    def _determine_trend(
            self,
            highs: List[SwingPoint],
            lows: List[SwingPoint],
            higher_highs: int,
            lower_lows: int
    ) -> TrendState:
        """Determine trend state from swing analysis."""
        # Need minimum swings
        if len(highs) < self.min_swings_for_trend or len(lows) < self.min_swings_for_trend:
            return TrendState.UNKNOWN

        # Check for bullish structure
        if higher_highs >= self.min_swings_for_trend - 1:
            # Also check for higher lows
            if len(lows) >= 2 and lows[-1].price > lows[-2].price:
                return TrendState.BULLISH

        # Check for bearish structure
        if lower_lows >= self.min_swings_for_trend - 1:
            # Also check for lower highs
            if len(highs) >= 2 and highs[-1].price < highs[-2].price:
                return TrendState.BEARISH

        # No clear trend
        return TrendState.RANGING