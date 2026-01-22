# ============================================================================
# File: src/data/schemas.py
# Pydantic schemas for API validation and serialization
# ============================================================================

"""
Pydantic schemas for API validation.

These are separate from dataclass models to allow for:
- API-level validation
- Auto-generated documentation
- Flexible serialization
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from pydantic import BaseModel, Field, ConfigDict, field_validator


class MarketBarSchema(BaseModel):
    """API schema for MarketBar."""

    symbol: str = Field(..., min_length=1, description="Trading symbol")
    timeframe: str = Field(..., min_length=1, description="Timeframe (e.g., H1, M15)")
    timestamp_utc: datetime = Field(..., description="Bar open time in UTC")
    open: Decimal = Field(..., gt=0, description="Opening price")
    high: Decimal = Field(..., gt=0, description="Highest price")
    low: Decimal = Field(..., gt=0, description="Lowest price")
    close: Decimal = Field(..., gt=0, description="Closing price")
    tick_volume: int = Field(..., ge=0, description="Tick volume")
    real_volume: int = Field(default=0, ge=0, description="Real volume")
    spread: int = Field(default=0, ge=0, description="Spread in points")
    account_id: int = Field(default=0, description="MT5 account ID")
    broker: str = Field(default="unknown", description="Broker name")

    @field_validator("timestamp_utc")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        return v

    @field_validator("high", mode="after")
    @classmethod
    def validate_high(cls, v: Decimal, info):
        low = info.data.get("low")
        if low is not None and v < low:
            raise ValueError(f"high ({v}) must be >= low ({low})")
        return v

    @field_validator("open", "close", mode="after")
    @classmethod
    def validate_ohlc_range(cls, v: Decimal, info):
        low = info.data.get("low")
        high = info.data.get("high")

        if low is not None and v < low:
            raise ValueError(f"Price ({v}) must be >= low ({low})")
        if high is not None and v > high:
            raise ValueError(f"Price ({v}) must be <= high ({high})")
        return v

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class TickSchema(BaseModel):
    """API schema for Tick."""

    symbol: str = Field(..., min_length=1)
    timestamp_utc: datetime
    bid: Decimal = Field(..., gt=0)
    ask: Decimal = Field(..., gt=0)
    last: Decimal = Field(default=Decimal("0"), ge=0)
    volume: int = Field(default=0, ge=0)
    flags: int = Field(default=0)
    account_id: int = Field(default=0)
    broker: str = Field(default="unknown")

    @field_validator("timestamp_utc")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        return v

    @field_validator("ask", mode="after")
    @classmethod
    def validate_spread(cls, v: Decimal, info):
        bid = info.data.get("bid")
        if bid is not None and v < bid:
            raise ValueError(f"ask ({v}) must be >= bid ({bid})")
        return v

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class SymbolInfoSchema(BaseModel):
    """API schema for SymbolInfo."""

    symbol: str = Field(..., min_length=1)
    digits: int = Field(..., ge=0)
    point: Decimal = Field(..., gt=0)
    tick_size: Decimal = Field(..., gt=0)
    tick_value: Decimal = Field(..., gt=0)
    contract_size: Decimal = Field(..., gt=0)
    volume_min: Decimal = Field(..., gt=0)
    volume_max: Decimal = Field(..., gt=0)
    volume_step: Decimal = Field(..., gt=0)
    currency_base: str = Field(default="")
    currency_profit: str = Field(default="")
    currency_margin: str = Field(default="")
    spread_typical: int = Field(default=0, ge=0)
    account_id: int = Field(default=0)
    broker: str = Field(default="unknown")

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
        }
    )
