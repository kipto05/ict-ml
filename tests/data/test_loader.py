import pandas as pd
import pytest
from datetime import datetime, timezone

from src.data.historical.loader import HistoricalDataLoader
from src.data.models import MarketBar


# ------------------------------------------------------------------
# FIXTURES
# ------------------------------------------------------------------

@pytest.fixture
def fake_mt5_connector(mocker):
    """
    Fake MT5 connector with mocked get_bars_range().
    """
    mt5 = mocker.Mock()

    index = pd.date_range(
        start="2024-01-01 00:00:00",
        periods=3,
        freq="h",
        tz=timezone.utc
    )

    df = pd.DataFrame(
        {
            "open": [1.1000, 1.1010, 1.1020],
            "high": [1.1050, 1.1060, 1.1070],
            "low": [1.0950, 1.0960, 1.0970],
            "close": [1.1020, 1.1030, 1.1040],
            "tick_volume": [100, 120, 110],
            "spread": [10, 10, 10],
        },
        index=index
    )

    mt5.get_bars_range.return_value = df
    return mt5


@pytest.fixture
def loader(fake_mt5_connector):
    return HistoricalDataLoader(
        mt5_connector=fake_mt5_connector,
        account_id=123456,
        broker="JustMarkets"
    )


# ------------------------------------------------------------------
# TESTS
# ------------------------------------------------------------------

def test_load_historical_bars_success(loader, mocker):
    """
    Happy-path test: all bars valid.
    """

    mocker.patch(
        "src.data.validation.validator.validate_bar",
        return_value=(True, None)
    )

    mocker.patch(
        "src.data.validation.validator.validate_bar_sequence",
        return_value=(True, [])
    )

    bars = loader.load_historical_bars(
        symbol="EURUSD",
        timeframe="H1",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 2, tzinfo=timezone.utc)
    )

    assert len(bars) == 3
    assert all(isinstance(bar, MarketBar) for bar in bars)

    stats = loader.get_statistics()
    assert stats["bars_fetched"] == 3
    assert stats["bars_validated"] == 3
    assert stats["bars_rejected"] == 0


def test_invalid_bars_are_rejected(loader, mocker):
    """
    Validation rejects all bars.
    """

    mocker.patch(
        "src.data.validation.validator.validate_bar",
        return_value=(False, "Invalid OHLC")
    )

    bars = loader.load_historical_bars(
        symbol="EURUSD",
        timeframe="H1",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 2, tzinfo=timezone.utc)
    )

    assert bars == []

    stats = loader.get_statistics()
    assert stats["bars_fetched"] == 3
    assert stats["bars_validated"] == 0
    assert stats["bars_rejected"] == 3


def test_empty_mt5_response(loader, mocker):
    """
    MT5 returns empty dataframe.
    """

    loader.mt5.get_bars_range.return_value = pd.DataFrame()

    bars = loader.load_historical_bars(
        symbol="EURUSD",
        timeframe="H1",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 2, tzinfo=timezone.utc)
    )

    assert bars == []

    stats = loader.get_statistics()
    assert stats["bars_fetched"] == 0


def test_invalid_date_range_raises(loader):
    """
    start_date >= end_date should raise ValueError.
    """

    with pytest.raises(ValueError):
        loader.load_historical_bars(
            symbol="EURUSD",
            timeframe="H1",
            start_date=datetime(2024, 1, 2, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
