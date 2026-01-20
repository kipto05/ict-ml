from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timezone
import pytz
import numpy as np
import pandas as pd


def to_ny_time(dt: datetime) -> datetime:
    """
    Convert datetime to New York timezone.

    Args:
        dt: Datetime to convert

    Returns:
        Datetime in New York timezone
    """
    ny_tz = pytz.timezone('America/New_York')
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(ny_tz)


def is_killzone(dt: datetime, killzone: Killzone) -> bool:
    """
    Check if datetime falls within specified killzone.

    Args:
        dt: Datetime to check (should be in NY time)
        killzone: Killzone to check against

    Returns:
        True if in killzone, False otherwise
    """
    ny_dt = to_ny_time(dt)
    time_str = ny_dt.strftime("%H:%M")

    start, end = KILLZONE_TIMES[killzone]
    return start <= time_str <= end


def pips_to_price(pips: float, symbol: str = "EURUSD") -> float:
    """
    Convert pips to price value.

    Args:
        pips: Number of pips
        symbol: Trading symbol

    Returns:
        Price value
    """
    # JPY pairs have different pip calculation
    if "JPY" in symbol:
        return pips * 0.01
    return pips * 0.0001


def price_to_pips(price_diff: float, symbol: str = "EURUSD") -> float:
    """
    Convert price difference to pips.

    Args:
        price_diff: Price difference
        symbol: Trading symbol

    Returns:
        Number of pips
    """
    if "JPY" in symbol:
        return price_diff / 0.01
    return price_diff / 0.0001


def calculate_lot_size(
        account_balance: float,
        risk_percent: float,
        stop_loss_pips: float,
        symbol: str = "EURUSD"
) -> float:
    """
    Calculate position size based on risk parameters.

    Args:
        account_balance: Account balance
        risk_percent: Risk percentage (1.0 = 1%)
        stop_loss_pips: Stop loss in pips
        symbol: Trading symbol

    Returns:
        Lot size
    """
    risk_amount = account_balance * (risk_percent / 100)
    pip_value = 10 if "JPY" not in symbol else 1000  # Standard lot
    lot_size = risk_amount / (stop_loss_pips * pip_value)

    # Round to 2 decimal places
    return round(lot_size, 2)


def format_trade_log(trade_data: Dict[str, Any]) -> str:
    """
    Format trade data for logging.

    Args:
        trade_data: Trade information dictionary

    Returns:
        Formatted log string
    """
    return (
        f"Trade: {trade_data.get('ticket')} | "
        f"{trade_data.get('symbol')} | "
        f"{trade_data.get('type')} | "
        f"Vol: {trade_data.get('volume')} | "
        f"Entry: {trade_data.get('price_open')} | "
        f"SL: {trade_data.get('sl')} | "
        f"TP: {trade_data.get('tp')} | "
        f"P/L: {trade_data.get('profit', 0):.2f}"
    )


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero

    Returns:
        Division result or default
    """
    return numerator / denominator if denominator != 0 else default


def serialize_numpy(obj: Any) -> Any:
    """
    Serialize numpy types for JSON encoding.

    Args:
        obj: Object to serialize

    Returns:
        Serializable object
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def validate_symbol(symbol: str) -> bool:
    """
    Validate trading symbol format.

    Args:
        symbol: Trading symbol

    Returns:
        True if valid, False otherwise
    """
    # Basic validation: 6 characters, uppercase
    return len(symbol) == 6 and symbol.isupper() and symbol.isalpha()