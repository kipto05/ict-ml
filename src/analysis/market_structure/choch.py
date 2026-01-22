# ============================================================================
# File: src/analysis/market_structure/choch.py
# Change of Character detection
# ============================================================================

"""
Change of Character (CHoCH) detection.

CHoCH occurs when price breaks structure in the OPPOSITE direction of the trend.
It signals a potential trend reversal.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from decimal import Decimal
from enum import Enum

from src.data.models import MarketBar
from src.analysis.market_structure.swings import SwingPoint, SwingType
from src.analysis.market_structure.structure import TrendState
from src.core.logger import main_logger

logger = main_logger


class CHoCHType(Enum):
    """CHoCH type."""
    BULLISH_TO_BEARISH = "bullish_to_bearish"
    BEARISH_TO_BULLISH = "bearish_to_bullish"


@dataclass(frozen=True)
class CHoCHEvent:
    """
    Change of Character event.

    Signals potential trend reversal.

    Attributes:
        choch_type: Type of character change
        broken_swing: Swing that was broken counter-trend
        break_price: Price at which break occurred
        break_bar: Bar that caused the break
        prior_trend: Trend before the CHoCH
        timestamp: Event timestamp
    """
    choch_type: CHoCHType
    broken_swing: SwingPoint
    break_price: Decimal
    break_bar: MarketBar
    prior_trend: TrendState
    timestamp: datetime


class CHoCHDetector:
    """
    Detects Change of Character events.

    CHoCH Rules:
    - In uptrend: Break below swing low = CHoCH (bullish to bearish)
    - In downtrend: Break above swing high = CHoCH (bearish to bullish)
    """

    def __init__(self, use_body: bool = True):
        """Initialize CHoCH detector."""
        self.use_body = use_body

    def detect_choch(
            self,
            bars: List[MarketBar],
            swings: List[SwingPoint],
            trend_state: TrendState
    ) -> List[CHoCHEvent]:
        """
        Detect CHoCH events.

        Args:
            bars: List of MarketBars
            swings: List of swing points
            trend_state: Current trend state

        Returns:
            List of CHoCHEvents
        """
        if trend_state == TrendState.RANGING or trend_state == TrendState.UNKNOWN:
            return []  # CHoCH only valid in trending markets

        choch_events = []
        broken_swings = set()

        for i, bar in enumerate(bars):
            relevant_swings = [
                s for s in swings
                if s.bar_index < i and s.bar_index not in broken_swings
            ]

            if not relevant_swings:
                continue

            # In bullish trend, look for break below swing low (CHoCH)
            if trend_state == TrendState.BULLISH:
                lows = [s for s in relevant_swings if s.swing_type == SwingType.LOW]
                if lows:
                    last_low = lows[-1]
                    break_price = bar.close if self.use_body else bar.low

                    if break_price < last_low.price:
                        choch = CHoCHEvent(
                            choch_type=CHoCHType.BULLISH_TO_BEARISH,
                            broken_swing=last_low,
                            break_price=break_price,
                            break_bar=bar,
                            prior_trend=trend_state,
                            timestamp=bar.timestamp_utc,
                        )
                        choch_events.append(choch)
                        broken_swings.add(last_low.bar_index)
                        logger.info(f"CHoCH detected (B→Be): {choch}")

            # In bearish trend, look for break above swing high (CHoCH)
            elif trend_state == TrendState.BEARISH:
                highs = [s for s in relevant_swings if s.swing_type == SwingType.HIGH]
                if highs:
                    last_high = highs[-1]
                    break_price = bar.close if self.use_body else bar.high

                    if break_price > last_high.price:
                        choch = CHoCHEvent(
                            choch_type=CHoCHType.BEARISH_TO_BULLISH,
                            broken_swing=last_high,
                            break_price=break_price,
                            break_bar=bar,
                            prior_trend=trend_state,
                            timestamp=bar.timestamp_utc,
                        )
                        choch_events.append(choch)
                        broken_swings.add(last_high.bar_index)
                        logger.info(f"CHoCH detected (Be→B): {choch}")

        return choch_events