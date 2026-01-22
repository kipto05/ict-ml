# ============================================================================
# File: src/analysis/market_structure/bos.py
# Break of Structure detection
# ============================================================================

"""
Break of Structure (BOS) detection.

BOS occurs when price breaks through a swing point in the direction of the trend.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from enum import Enum

from src.data.models import MarketBar
from src.analysis.market_structure.swings import SwingPoint, SwingType
from src.core.logger import main_logger

logger = main_logger


class BOSDirection(Enum):
    """BOS direction."""
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass(frozen=True)
class BOSEvent:
    """
    Break of Structure event.

    Represents a confirmed structural break.

    Attributes:
        direction: Bullish or bearish BOS
        broken_swing: The swing point that was broken
        break_price: Price at which break occurred
        break_bar: Bar that caused the break
        timestamp: Event timestamp
    """
    direction: BOSDirection
    broken_swing: SwingPoint
    break_price: Decimal
    break_bar: MarketBar
    timestamp: datetime

    def __str__(self) -> str:
        return (
            f"BOS({self.direction.value}) @ {self.break_price} "
            f"broke {self.broken_swing.swing_type.value} at {self.broken_swing.price}"
        )


class BOSDetector:
    """
    Detects Break of Structure events.

    BOS Rules:
    - Bullish BOS: Price closes above previous swing high
    - Bearish BOS: Price closes below previous swing low
    """

    def __init__(self, use_body: bool = True):
        """
        Initialize BOS detector.

        Args:
            use_body: If True, use close for breaks. If False, use wick.
        """
        self.use_body = use_body

    def detect_bos(
            self,
            bars: List[MarketBar],
            swings: List[SwingPoint]
    ) -> List[BOSEvent]:
        """
        Detect BOS events in bar series.

        Args:
            bars: List of MarketBars
            swings: List of detected swing points

        Returns:
            List of BOSEvents
        """
        if not swings or len(bars) < 2:
            return []

        bos_events = []

        # Track which swings have been broken
        broken_swings = set()

        for i, bar in enumerate(bars):
            # Find relevant swing points before this bar
            relevant_swings = [
                s for s in swings
                if s.bar_index < i and s.bar_index not in broken_swings
            ]

            if not relevant_swings:
                continue

            # Check for bullish BOS (break above swing high)
            recent_highs = [s for s in relevant_swings if s.swing_type == SwingType.HIGH]
            if recent_highs:
                last_high = recent_highs[-1]
                break_price = bar.close if self.use_body else bar.high

                if break_price > last_high.price:
                    bos = BOSEvent(
                        direction=BOSDirection.BULLISH,
                        broken_swing=last_high,
                        break_price=break_price,
                        break_bar=bar,
                        timestamp=bar.timestamp_utc,
                    )
                    bos_events.append(bos)
                    broken_swings.add(last_high.bar_index)
                    logger.info(f"Bullish BOS detected: {bos}")

            # Check for bearish BOS (break below swing low)
            recent_lows = [s for s in relevant_swings if s.swing_type == SwingType.LOW]
            if recent_lows:
                last_low = recent_lows[-1]
                break_price = bar.close if self.use_body else bar.low

                if break_price < last_low.price:
                    bos = BOSEvent(
                        direction=BOSDirection.BEARISH,
                        broken_swing=last_low,
                        break_price=break_price,
                        break_bar=bar,
                        timestamp=bar.timestamp_utc,
                    )
                    bos_events.append(bos)
                    broken_swings.add(last_low.bar_index)
                    logger.info(f"Bearish BOS detected: {bos}")

        return bos_events
