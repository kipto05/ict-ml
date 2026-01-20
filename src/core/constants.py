
# ============================================================================
# src/core/constants.py - Application Constants
# ============================================================================

from enum import Enum
from typing import Dict

class TrendState(Enum):
    """Market trend states."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGING = "ranging"
    UNKNOWN = "unknown"


class StructureType(Enum):
    """Market structure types."""
    BOS = "break_of_structure"
    CHOCH = "change_of_character"
    INTERNAL = "internal"
    EXTERNAL = "external"


class LiquiditySide(Enum):
    """Liquidity pool sides."""
    BUY_SIDE = "buy_side"
    SELL_SIDE = "sell_side"


class OrderBlockType(Enum):
    """Order block classifications."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    BREAKER = "breaker"
    MITIGATION = "mitigation"


class TradingSession(Enum):
    """Trading session definitions."""
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    LONDON_CLOSE = "london_close"


class Killzone(Enum):
    """ICT Killzone definitions."""
    LONDON = "london_killzone"
    NEW_YORK = "new_york_killzone"
    ASIAN_RANGE = "asian_range"


# Session times (in New York time)
SESSION_TIMES: Dict[TradingSession, tuple] = {
    TradingSession.ASIAN: ("20:00", "00:00"),
    TradingSession.LONDON: ("02:00", "05:00"),
    TradingSession.NEW_YORK: ("08:00", "11:00"),
    TradingSession.LONDON_CLOSE: ("10:00", "12:00"),
}

KILLZONE_TIMES: Dict[Killzone, tuple] = {
    Killzone.LONDON: ("02:00", "05:00"),
    Killzone.NEW_YORK: ("08:30", "11:00"),
    Killzone.ASIAN_RANGE: ("20:00", "00:00"),
}

# MT5 Timeframe mappings
MT5_TIMEFRAMES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
}

# ICT Configuration
FVG_MIN_SIZE_PIPS = 5
OB_LOOKBACK_BARS = 20
LIQUIDITY_TOLERANCE_PIPS = 2
STRUCTURE_SWING_LOOKBACK = 5

# Risk Constants
MIN_STOP_LOSS_PIPS = 10
MAX_STOP_LOSS_PIPS = 100
MIN_RISK_REWARD_RATIO = 1.5