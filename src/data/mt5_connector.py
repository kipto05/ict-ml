# ============================================================================
# src/data/mt5_connector.py - MetaTrader 5 Connector
# ============================================================================
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent  # src/core → src → project
sys.path.insert(0, str(project_root))


import MetaTrader5 as mt5
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.core.logger import main_logger
from src.core.exceptions import MT5ConnectionError, MT5ExecutionError
from src.core.constants import MT5_TIMEFRAMES
from config.settings import settings

logger = main_logger


class MT5Connector:
    """
    MetaTrader 5 connector for data streaming and order execution.
    """

    def __init__(
            self,
            login: int = None,
            password: str = None,
            server: str = None,
            path: str = None
    ):
        """
        Initialize MT5 connector.

        Args:
            login: MT5 account login
            password: MT5 account password
            server: MT5 broker server
            path: Path to MT5 terminal executable
        """
        self.login = login or settings.mt5_login
        self.password = password or settings.mt5_password
        self.server = server or settings.mt5_server
        self.path = path or settings.mt5_path
        self.connected = False
        self.account_info = None

    def connect(self) -> bool:
        """
        Connect to MT5 terminal.

        Returns:
            True if connection successful

        Raises:
            MT5ConnectionError: If connection fails
        """
        try:
            # Initialize MT5
            if self.path:
                if not mt5.initialize(path=self.path):
                    raise MT5ConnectionError(f"MT5 initialization failed: {mt5.last_error()}")
            else:
                if not mt5.initialize():
                    raise MT5ConnectionError(f"MT5 initialization failed: {mt5.last_error()}")

            # Login to account
            authorized = mt5.login(
                login=self.login,
                password=self.password,
                server=self.server,
                timeout=settings.mt5_timeout
            )

            if not authorized:
                error = mt5.last_error()
                raise MT5ConnectionError(f"MT5 login failed: {error}")

            self.connected = True

            # Get account info and convert to dict
            account_info_raw = mt5.account_info()
            if account_info_raw:
                self.account_info = {
                    'login': account_info_raw.login,
                    'balance': account_info_raw.balance,
                    'equity': account_info_raw.equity,
                    'profit': account_info_raw.profit,
                    'margin': account_info_raw.margin,
                    'margin_free': account_info_raw.margin_free,
                    'margin_level': account_info_raw.margin_level,
                    'leverage': account_info_raw.leverage,
                    'currency': account_info_raw.currency,
                }
            else:
                self.account_info = {}

            logger.info(
                f"Connected to MT5 - Account: {self.login} | "
                f"Server: {self.server} | Balance: {self.account_info['balance']}"
            )

            return True

        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            raise MT5ConnectionError(str(e))

    def disconnect(self):
        """Disconnect from MT5 terminal."""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")

    def is_connected(self) -> bool:
        """Check if connected to MT5."""
        return self.connected and mt5.terminal_info() is not None

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            Dictionary with account details
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        info = mt5.account_info()
        if info is None:
            raise MT5ConnectionError("Failed to get account info")

        return {
            'login': info.login,
            'balance': info.balance,
            'equity': info.equity,
            'profit': info.profit,
            'margin': info.margin,
            'margin_free': info.margin_free,
            'margin_level': info.margin_level,
            'leverage': info.leverage,
            'currency': info.currency,
        }

    def get_symbols(self) -> List[str]:
        """
        Get list of available symbols.

        Returns:
            List of symbol names
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        symbols = mt5.symbols_get()
        if symbols is None:
            return []

        return [symbol.name for symbol in symbols]

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get symbol specifications.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with symbol information
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        info = mt5.symbol_info(symbol)
        if info is None:
            raise MT5ConnectionError(f"Symbol {symbol} not found")

        return {
            'symbol': info.name,
            'bid': info.bid,
            'ask': info.ask,
            'spread': info.spread,
            'digits': info.digits,
            'point': info.point,
            'trade_contract_size': info.trade_contract_size,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step,
        }

    def get_tick(self, symbol: str) -> Dict[str, Any]:
        """
        Get latest tick for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with tick data
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5ConnectionError(f"Failed to get tick for {symbol}")

        return {
            'symbol': symbol,
            'time': datetime.fromtimestamp(tick.time),
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume,
        }

    def get_bars(
            self,
            symbol: str,
            timeframe: str = "H1",
            count: int = 1000,
            start_pos: int = 0
    ) -> pd.DataFrame:
        """
        Get historical bar data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, H1, etc.)
            count: Number of bars
            start_pos: Start position (0 = most recent)

        Returns:
            DataFrame with OHLCV data
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        # Get MT5 timeframe constant
        mt5_timeframe = getattr(mt5, f"TIMEFRAME_{timeframe}", None)
        if mt5_timeframe is None:
            raise ValueError(f"Invalid timeframe: {timeframe}")

        # Get bars
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, start_pos, count)

        if rates is None or len(rates) == 0:
            raise MT5ConnectionError(f"Failed to get bars for {symbol}")

        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        return df

    def get_bars_range(
            self,
            symbol: str,
            timeframe: str,
            start_date: datetime,
            end_date: datetime
    ) -> pd.DataFrame:
        """
        Get historical bars for date range.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLCV data
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        mt5_timeframe = getattr(mt5, f"TIMEFRAME_{timeframe}", None)
        if mt5_timeframe is None:
            raise ValueError(f"Invalid timeframe: {timeframe}")

        rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)

        if rates is None or len(rates) == 0:
            logger.warning(f"No data returned for {symbol} {timeframe}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        logger.info(f"Retrieved {len(df)} bars for {symbol} {timeframe}")
        return df

    def send_order(
            self,
            symbol: str,
            order_type: str,
            volume: float,
            price: float = None,
            sl: float = None,
            tp: float = None,
            deviation: int = 20,
            comment: str = "ICT Bot"
    ) -> Dict[str, Any]:
        """
        Send trading order.

        Args:
            symbol: Trading symbol
            order_type: Order type (BUY, SELL, BUY_LIMIT, etc.)
            volume: Order volume
            price: Order price (for pending orders)
            sl: Stop loss
            tp: Take profit
            deviation: Maximum price deviation
            comment: Order comment

        Returns:
            Order result dictionary
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        # Map order types
        order_type_map = {
            'BUY': mt5.ORDER_TYPE_BUY,
            'SELL': mt5.ORDER_TYPE_SELL,
            'BUY_LIMIT': mt5.ORDER_TYPE_BUY_LIMIT,
            'SELL_LIMIT': mt5.ORDER_TYPE_SELL_LIMIT,
            'BUY_STOP': mt5.ORDER_TYPE_BUY_STOP,
            'SELL_STOP': mt5.ORDER_TYPE_SELL_STOP,
        }

        mt5_order_type = order_type_map.get(order_type.upper())
        if mt5_order_type is None:
            raise ValueError(f"Invalid order type: {order_type}")

        # Get current price if not provided
        if price is None:
            tick = self.get_tick(symbol)
            price = tick['ask'] if 'BUY' in order_type else tick['bid']

        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "deviation": deviation,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp

        # Send order
        result = mt5.order_send(request)

        if result is None:
            raise MT5ExecutionError("Order send failed: No result")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise MT5ExecutionError(
                f"Order failed: {result.retcode} - {result.comment}"
            )

        logger.info(f"Order executed: {order_type} {volume} {symbol} @ {price}")

        return {
            'ticket': result.order,
            'retcode': result.retcode,
            'deal': result.deal,
            'volume': result.volume,
            'price': result.price,
            'comment': result.comment,
        }

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """
        Close position by ticket.

        Args:
            ticket: Position ticket

        Returns:
            Close result dictionary
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        # Get position
        position = mt5.positions_get(ticket=ticket)
        if not position:
            raise MT5ExecutionError(f"Position {ticket} not found")

        position = position[0]

        # Prepare close request
        close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": close_type,
            "position": ticket,
            "magic": 234000,
            "comment": "Close by ICT Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise MT5ExecutionError(
                f"Position close failed: {result.retcode} - {result.comment}"
            )

        logger.info(f"Position closed: {ticket}")

        return {
            'ticket': ticket,
            'retcode': result.retcode,
            'comment': result.comment,
        }

    def get_open_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Get open positions.

        Args:
            symbol: Filter by symbol (optional)

        Returns:
            List of position dictionaries
        """
        if not self.is_connected():
            raise MT5ConnectionError("Not connected to MT5")

        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()

        if positions is None:
            return []

        return [
            {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'time': datetime.fromtimestamp(pos.time),
            }
            for pos in positions
        ]

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test MT5 connection
    with MT5Connector() as mt5_conn:
        # Get account info
        account = mt5_conn.get_account_info()
        print(f"Account Balance: {account['balance']}")

        # Get symbols
        symbols = mt5_conn.get_symbols()[:5]
        print(f"Available symbols: {symbols}")

        # Get historical data
        df = mt5_conn.get_bars("EURUSD.m", "H1", count=100)
        print(f"\nEURUSD H1 Data:")
        print(df.tail())

        # Get open positions
        positions = mt5_conn.get_open_positions()
        print(f"\nOpen positions: {len(positions)}")