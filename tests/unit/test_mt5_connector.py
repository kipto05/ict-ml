# ============================================================================
# tests/unit/test_mt5_connector.py - MT5 Connector Unit Tests (FIXED)
# ============================================================================

"""
Unit tests for MT5 connector.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.data.mt5_connector import MT5Connector
from src.core.exceptions import MT5ConnectionError


class TestMT5Connector:
    """Test MT5Connector class."""

    def test_initialization(self):
        """Test connector initialization."""
        connector = MT5Connector(
            login=12345,
            password="test_password",
            server="Test-Server"
        )

        assert connector.login == 12345
        assert connector.password == "test_password"
        assert connector.server == "Test-Server"
        assert connector.connected is False

    @patch('src.data.mt5_connector.mt5')
    def test_connect_success(self, mock_mt5):
        """Test successful connection."""
        # Create mock account info object with proper attributes
        mock_account = Mock()
        mock_account.login = 12345
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.currency = "USD"

        # Setup MT5 mocks
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.terminal_info.return_value = Mock()  # Non-None means connected

        connector = MT5Connector()
        result = connector.connect()

        assert result is True
        assert connector.connected is True
        assert connector.account_info is not None
        assert connector.account_info['login'] == 12345
        assert connector.account_info['balance'] == 10000.0

        mock_mt5.initialize.assert_called_once()
        mock_mt5.login.assert_called_once()

    @patch('src.data.mt5_connector.mt5')
    def test_connect_failure(self, mock_mt5):
        """Test connection failure."""
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Connection failed")

        connector = MT5Connector()

        with pytest.raises(MT5ConnectionError):
            connector.connect()

    @patch('src.data.mt5_connector.mt5')
    def test_disconnect(self, mock_mt5):
        """Test disconnection."""
        # Setup mocks for connection
        mock_account = Mock()
        mock_account.login = 12345
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.currency = "USD"

        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.terminal_info.return_value = Mock()

        connector = MT5Connector()
        connector.connect()
        assert connector.connected is True

        # Test disconnect
        connector.disconnect()
        mock_mt5.shutdown.assert_called_once()
        assert connector.connected is False

    @patch('src.data.mt5_connector.mt5')
    def test_get_account_info(self, mock_mt5):
        """Test getting account information."""
        # Setup mock account
        mock_account = Mock()
        mock_account.login = 12345
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.currency = "USD"

        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.terminal_info.return_value = Mock()

        connector = MT5Connector()
        connector.connect()

        # Get account info again (should call MT5 again)
        info = connector.get_account_info()

        assert isinstance(info, dict)
        assert info['login'] == 12345
        assert info['balance'] == 10000.0
        assert info['equity'] == 10000.0
        assert info['currency'] == "USD"

    @patch('src.data.mt5_connector.mt5')
    def test_get_bars(self, mock_mt5):
        """Test getting historical bars."""
        # Setup connection mocks
        mock_account = Mock()
        mock_account.login = 12345
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.currency = "USD"

        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.terminal_info.return_value = Mock()

        # Create mock rates data
        import numpy as np
        mock_rates = np.array([
                                  (1609459200, 1.2200, 1.2250, 1.2150, 1.2225, 1000, 0, 0),
                                  (1609462800, 1.2225, 1.2275, 1.2175, 1.2250, 1200, 0, 0),
                              ] * 50,  # 100 bars
                              dtype=[
                                  ('time', 'i8'),
                                  ('open', 'f8'),
                                  ('high', 'f8'),
                                  ('low', 'f8'),
                                  ('close', 'f8'),
                                  ('tick_volume', 'i8'),
                                  ('spread', 'i4'),
                                  ('real_volume', 'i8')
                              ])

        mock_mt5.copy_rates_from_pos.return_value = mock_rates
        mock_mt5.TIMEFRAME_H1 = 16385  # Actual MT5 constant value

        connector = MT5Connector()
        connector.connect()

        df = connector.get_bars("EURUSD", "H1", 100)

        assert len(df) == 100
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'tick_volume' in df.columns
        assert isinstance(df.index, pd.DatetimeIndex)

    @patch('src.data.mt5_connector.mt5')
    def test_get_symbols(self, mock_mt5):
        """Test getting available symbols."""
        # Setup connection
        mock_account = Mock()
        mock_account.login = 12345
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.currency = "USD"

        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.terminal_info.return_value = Mock()

        # Create mock symbols
        mock_symbol1 = Mock()
        mock_symbol1.name = "EURUSD"
        mock_symbol2 = Mock()
        mock_symbol2.name = "GBPUSD"
        mock_symbol3 = Mock()
        mock_symbol3.name = "USDJPY"

        mock_mt5.symbols_get.return_value = [mock_symbol1, mock_symbol2, mock_symbol3]

        connector = MT5Connector()
        connector.connect()

        symbols = connector.get_symbols()

        assert len(symbols) == 3
        assert "EURUSD" in symbols
        assert "GBPUSD" in symbols
        assert "USDJPY" in symbols

    @patch('src.data.mt5_connector.mt5')
    def test_is_connected(self, mock_mt5):
        """Test connection status check."""
        connector = MT5Connector()

        # Initially not connected
        mock_mt5.terminal_info.return_value = None
        assert connector.is_connected() is False

        # Setup connection
        mock_account = Mock()
        mock_account.login = 12345
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.currency = "USD"

        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.terminal_info.return_value = Mock()

        # Connect
        connector.connect()
        assert connector.is_connected() is True

        # Simulate disconnection
        mock_mt5.terminal_info.return_value = None
        assert connector.is_connected() is False


# ============================================================================
# Test fixtures for more complex scenarios
# ============================================================================

@pytest.fixture
def mock_mt5_setup():
    """Fixture to setup mock MT5 for tests."""
    with patch('src.data.mt5_connector.mt5') as mock_mt5:
        # Setup basic mocks
        mock_account = Mock()
        mock_account.login = 12345
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.currency = "USD"

        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.account_info.return_value = mock_account
        mock_mt5.terminal_info.return_value = Mock()

        yield mock_mt5


def test_with_mock_fixture(mock_mt5_setup):
    """Example test using the fixture."""
    connector = MT5Connector()
    connector.connect()

    assert connector.connected is True
    assert connector.account_info is not None
    assert connector.account_info['balance'] == 10000.0
    mock_mt5_setup.initialize.assert_called_once()


# ============================================================================
# Additional edge case tests
# ============================================================================

@patch('src.data.mt5_connector.mt5')
def test_connect_init_failure(mock_mt5):
    """Test connection when initialize fails."""
    mock_mt5.initialize.return_value = False
    mock_mt5.last_error.return_value = (1, "Initialize failed")

    connector = MT5Connector()

    with pytest.raises(MT5ConnectionError) as exc_info:
        connector.connect()

    assert "initialization failed" in str(exc_info.value).lower()


@patch('src.data.mt5_connector.mt5')
def test_connect_login_failure(mock_mt5):
    """Test connection when login fails."""
    mock_mt5.initialize.return_value = True
    mock_mt5.login.return_value = False
    mock_mt5.last_error.return_value = (2, "Invalid credentials")

    connector = MT5Connector()

    with pytest.raises(MT5ConnectionError) as exc_info:
        connector.connect()

    assert "login failed" in str(exc_info.value).lower()


@patch('src.data.mt5_connector.mt5')
def test_get_bars_invalid_timeframe(mock_mt5):
    """Test get_bars with invalid timeframe."""
    # Setup connection
    mock_account = Mock()
    mock_account.login = 12345
    mock_account.balance = 10000.0
    mock_account.equity = 10000.0
    mock_account.profit = 0.0
    mock_account.margin = 0.0
    mock_account.margin_free = 10000.0
    mock_account.margin_level = 0.0
    mock_account.leverage = 100
    mock_account.currency = "USD"

    mock_mt5.initialize.return_value = True
    mock_mt5.login.return_value = True
    mock_mt5.account_info.return_value = mock_account
    mock_mt5.terminal_info.return_value = Mock()

    # Mock the getattr call specifically
    with patch('src.data.mt5_connector.getattr') as mock_getattr:
        # Make getattr return None for TIMEFRAME_INVALID
        def getattr_side_effect(obj, name, default=None):
            if name == "TIMEFRAME_INVALID":
                return None
            # For other attributes, use the mock's behavior
            if obj is mock_mt5:
                if hasattr(mock_mt5, name):
                    return getattr(mock_mt5, name)
                elif name in ["TIMEFRAME_H1", "TIMEFRAME_M5", "TIMEFRAME_M1"]:
                    # Return some constants
                    return {"TIMEFRAME_H1": 16385,
                            "TIMEFRAME_M5": 16390,
                            "TIMEFRAME_M1": 16385}.get(name)
            return default

        mock_getattr.side_effect = getattr_side_effect

        with patch('src.data.mt5_connector.logger'):
            connector = MT5Connector()
            connector.connect()

            # Test invalid timeframe - should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                connector.get_bars("EURUSD.m", "INVALID", 100)

            assert "Invalid timeframe" in str(exc_info.value)


@patch('src.data.mt5_connector.mt5')
def test_get_account_info_not_connected(mock_mt5):
    """Test get_account_info when not connected."""
    mock_mt5.terminal_info.return_value = None

    connector = MT5Connector()

    with pytest.raises(MT5ConnectionError) as exc_info:
        connector.get_account_info()

    assert "not connected" in str(exc_info.value).lower()


@patch('src.data.mt5_connector.mt5')
def test_context_manager(mock_mt5):
    """Test using connector as context manager."""
    mock_account = Mock()
    mock_account.login = 12345
    mock_account.balance = 10000.0
    mock_account.equity = 10000.0
    mock_account.profit = 0.0
    mock_account.margin = 0.0
    mock_account.margin_free = 10000.0
    mock_account.margin_level = 0.0
    mock_account.leverage = 100
    mock_account.currency = "USD"

    mock_mt5.initialize.return_value = True
    mock_mt5.login.return_value = True
    mock_mt5.account_info.return_value = mock_account
    mock_mt5.terminal_info.return_value = Mock()

    with MT5Connector() as connector:
        assert connector.connected is True

    # Should be disconnected after exiting context
    mock_mt5.shutdown.assert_called_once()