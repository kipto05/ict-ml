import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        return super().format(record)


def setup_logger(
        name: str = "ict_bot",
        log_dir: str = "logs",
        log_level: str = None
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name
        log_dir: Directory for log files
        log_level: Logging level (overrides settings)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level
    level = log_level or settings.log_level
    logger.setLevel(getattr(logging, level.upper()))

    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_format = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)

    # File handler - general logs
    file_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    # Error handler - errors only
    error_handler = RotatingFileHandler(
        log_path / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)

    # Trade handler - trade execution logs
    trade_handler = TimedRotatingFileHandler(
        log_path / "trades.log",
        when='midnight',
        interval=1,
        backupCount=30
    )
    trade_handler.setLevel(logging.INFO)
    trade_format = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    trade_handler.setFormatter(trade_format)

    # Clear existing handlers
    logger.handlers.clear()

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    # Add trade handler to trade logger
    if name == "ict_bot.trades":
        logger.addHandler(trade_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Create default loggers
main_logger = setup_logger("ict_bot")
trade_logger = setup_logger("ict_bot.trades")