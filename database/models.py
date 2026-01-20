# ============================================================================
# File: database/models.py
# Location: ict-ml-trading-bot/database/models.py
# SQLAlchemy Database Models
# ============================================================================

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum as SQLEnum, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


# ============================================================================
# ENUMS - Database-level enumerations
# ============================================================================

class TradeDirection(enum.Enum):
    """Trade direction enumeration."""
    BUY = "buy"
    SELL = "sell"


class TradeStatus(enum.Enum):
    """Trade status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# ============================================================================
# MODELS - Database tables
# ============================================================================

class Account(Base):
    """MT5 Account model."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(Integer, unique=True, nullable=False, index=True)
    server = Column(String(100), nullable=False)
    broker = Column(String(100))

    # Balance information
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    free_margin = Column(Float, default=0.0)

    # Account settings
    leverage = Column(Integer, default=100)
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    account_type = Column(String(20))  # demo, live, prop

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
    metrics = relationship("DailyMetrics", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account(login={self.login}, server={self.server}, balance={self.balance})>"


class Trade(Base):
    """Trade record model."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    ticket = Column(Integer, unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(SQLEnum(TradeDirection), nullable=False)
    volume = Column(Float, nullable=False)

    # Prices
    price_open = Column(Float, nullable=False)
    price_close = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)

    # Timing
    time_open = Column(DateTime, nullable=False, index=True)
    time_close = Column(DateTime)

    # Results
    profit = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)

    # Status
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.OPEN, index=True)

    # ICT Analysis
    ict_setup_type = Column(String(50))  # FVG, OB, Liquidity Sweep, etc.
    market_structure = Column(String(50))  # BOS, CHoCH
    liquidity_target = Column(Float)
    htf_bias = Column(String(20))  # bullish, bearish
    session = Column(String(20))  # asian, london, ny
    killzone = Column(String(30))

    # ML Predictions
    ml_confidence = Column(Float)
    ml_predicted_tp = Column(Float)
    ml_predicted_sl = Column(Float)

    # Risk metrics
    risk_reward_ratio = Column(Float)
    r_multiple = Column(Float)

    # Additional data (JSON for flexibility)
    meta_data = Column(JSON)
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="trades")

    def __repr__(self):
        return f"<Trade(ticket={self.ticket}, symbol={self.symbol}, direction={self.direction.value}, status={self.status.value})>"


class DailyMetrics(Base):
    """Daily performance metrics."""
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)

    # Performance
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)

    # P&L
    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)

    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float)
    expectancy = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)

    # ICT specific metrics
    liquidity_sweep_success_rate = Column(Float)
    fvg_respect_rate = Column(Float)
    killzone_performance = Column(JSON)
    session_performance = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="metrics")

    def __repr__(self):
        return f"<DailyMetrics(date={self.date}, win_rate={self.win_rate}, net_profit={self.net_profit})>"


class MLModel(Base):
    """ML Model tracking and versioning."""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50))  # classifier, regressor, rl

    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    mae = Column(Float)  # Mean Absolute Error for regressors
    rmse = Column(Float)  # Root Mean Squared Error

    # Training info
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    test_samples = Column(Integer)
    training_date = Column(DateTime)
    training_duration_seconds = Column(Integer)

    # Status
    is_active = Column(Boolean, default=False)
    is_production = Column(Boolean, default=False)

    # File paths
    model_path = Column(String(500))
    config_path = Column(String(500))

    # Hyperparameters and other info
    hyperparameters = Column(JSON)
    features_used = Column(JSON)
    meta_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MLModel(name={self.name}, version={self.version}, active={self.is_active})>"


class BacktestResult(Base):
    """Backtest results storage."""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    strategy_name = Column(String(100))

    # Backtest parameters
    symbol = Column(String(20))
    timeframe = Column(String(10))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_balance = Column(Float)

    # Results
    final_balance = Column(Float)
    total_return = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)

    # Risk metrics
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    profit_factor = Column(Float)
    expectancy = Column(Float)

    # Detailed results (JSON)
    trade_history = Column(JSON)
    equity_curve = Column(JSON)
    monthly_returns = Column(JSON)

    # Configuration
    strategy_config = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BacktestResult(name={self.name}, return={self.total_return}%)>"


class SystemLog(Base):
    """System events and error logging."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), index=True)  # INFO, WARNING, ERROR, CRITICAL
    source = Column(String(100))  # Module/component that generated log
    message = Column(Text, nullable=False)

    # Context
    account_id = Column(Integer, ForeignKey("accounts.id"))
    trade_id = Column(Integer, ForeignKey("trades.id"))

    # Additional data
    stack_trace = Column(Text)
    meta_data = Column(JSON)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<SystemLog(level={self.level}, source={self.source})>"


# ============================================================================
# Helper function to create all tables
# ============================================================================

def create_tables(engine):
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.meta_data.create_all(bind=engine)


def drop_tables(engine):
    """
    Drop all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.meta_data.drop_all(bind=engine)


# ============================================================================
# Usage example (for reference)
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create engine
    engine = create_engine("sqlite:///test.db")

    # Create tables
    create_tables(engine)
    print("✓ Tables created successfully")

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test account
    account = Account(
        login=12345,
        server="Test-Server",
        broker="Test Broker",
        balance=10000.0,
        equity=10000.0,
        account_type="demo"
    )
    session.add(account)
    session.commit()

    print(f"✓ Created account: {account}")

    # Create a test trade
    trade = Trade(
        ticket=100001,
        account_id=account.id,
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.1,
        price_open=1.1000,
        time_open=datetime.utcnow(),
        status=TradeStatus.OPEN
    )
    session.add(trade)
    session.commit()

    print(f"✓ Created trade: {trade}")

    session.close()