# ============================================================================
# tests/conftest.py - Pytest Configuration and Fixtures
# ============================================================================

"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import db_manager, Base
from database.models import Account, Trade
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


@pytest.fixture(scope="session")
def test_database():
    """Create test database."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    yield SessionLocal

    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_database):
    """Create database session for tests."""
    session = test_database()
    yield session
    session.close()


@pytest.fixture
def sample_account(db_session):
    """Create sample account."""
    account = Account(
        login=12345,
        server="Test-Server",
        broker="Test Broker",
        balance=10000.0,
        equity=10000.0,
        leverage=100,
        account_type="demo",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def sample_trades(db_session, sample_account):
    """Create sample trades."""
    trades = []

    for i in range(10):
        trade = Trade(
            ticket=1000 + i,
            account_id=sample_account.id,
            symbol="EURUSD",
            direction="BUY" if i % 2 == 0 else "SELL",
            volume=0.1,
            price_open=1.1000 + (i * 0.001),
            price_close=1.1000 + (i * 0.001) + (0.002 if i % 2 == 0 else -0.002),
            time_open=datetime.now() - timedelta(days=10 - i),
            time_close=datetime.now() - timedelta(days=9 - i),
            profit=20.0 if i % 2 == 0 else -10.0,
            status="CLOSED",
            ict_setup_type="FVG" if i % 3 == 0 else "OB",
            ml_confidence=0.75 + (i * 0.02)
        )
        trades.append(trade)
        db_session.add(trade)

    db_session.commit()
    return trades


@pytest.fixture
def sample_ohlc_data():
    """Create sample OHLC data."""
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='1H')

    # Generate synthetic price data
    np.random.seed(42)
    open_prices = 1.1000 + np.cumsum(np.random.randn(1000) * 0.0001)

    df = pd.DataFrame({
        'time': dates,
        'open': open_prices,
        'high': open_prices + np.random.rand(1000) * 0.0010,
        'low': open_prices - np.random.rand(1000) * 0.0010,
        'close': open_prices + np.random.randn(1000) * 0.0005,
        'tick_volume': np.random.randint(100, 1000, 1000),
        'spread': np.random.randint(1, 3, 1000),
        'real_volume': np.random.randint(1000, 10000, 1000)
    })

    df.set_index('time', inplace=True)
    return df


@pytest.fixture
def mock_mt5_connector():
    """Mock MT5 connector for testing."""

    class MockMT5Connector:
        def __init__(self):
            self.connected = False
            self.account_info = {
                'login': 12345,
                'balance': 10000.0,
                'equity': 10000.0,
                'margin': 0.0,
                'margin_free': 10000.0,
                'leverage': 100
            }

        def connect(self):
            self.connected = True
            return True

        def disconnect(self):
            self.connected = False

        def is_connected(self):
            return self.connected

        def get_account_info(self):
            return self.account_info

        def get_bars(self, symbol, timeframe, count):
            dates = pd.date_range(end=datetime.now(), periods=count, freq='1H')
            return pd.DataFrame({
                'open': np.random.rand(count) + 1.1,
                'high': np.random.rand(count) + 1.12,
                'low': np.random.rand(count) + 1.08,
                'close': np.random.rand(count) + 1.1,
                'tick_volume': np.random.randint(100, 1000, count),
            }, index=dates)

    return MockMT5Connector()