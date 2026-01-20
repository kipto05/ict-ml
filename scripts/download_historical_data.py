# ============================================================================
# scripts/download_historical_data.py - Historical Data Downloader
# ============================================================================

"""
Download historical data from MT5 for backtesting.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.data.mt5_connector import MT5Connector
from config.settings import settings
from src.core.logger import main_logger
from datetime import datetime, timedelta
import pandas as pd
import click

logger = main_logger


@click.command()
@click.option('--symbols', default='EURUSD,GBPUSD,USDJPY', help='Comma-separated symbols')
@click.option('--timeframe', default='H1', help='Timeframe (M1, M5, H1, H4, D1)')
@click.option('--start-date', default='2020-01-01', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD), default: today')
@click.option('--output-dir', default='data/historical', help='Output directory')
def download(symbols, timeframe, start_date, end_date, output_dir):
    """Download historical data from MT5."""

    # Parse parameters
    symbol_list = [s.strip() for s in symbols.split(',')]
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading data for {len(symbol_list)} symbols")
    logger.info(f"Timeframe: {timeframe}")
    logger.info(f"Date range: {start_date} to {end.strftime('%Y-%m-%d')}")

    try:
        with MT5Connector() as mt5:
            for symbol in symbol_list:
                logger.info(f"\nDownloading {symbol}...")

                try:
                    # Download data
                    df = mt5.get_bars_range(symbol, timeframe, start, end)

                    if df.empty:
                        logger.warning(f"No data retrieved for {symbol}")
                        continue

                    # Save to parquet
                    filename = f"{symbol}_{timeframe}_{start_date}_to_{end.strftime('%Y-%m-%d')}.parquet"
                    filepath = output_path / filename
                    df.to_parquet(filepath)

                    logger.info(
                        f"✓ Saved {len(df)} bars to {filepath} "
                        f"({df.index[0]} to {df.index[-1]})"
                    )

                except Exception as e:
                    logger.error(f"✗ Failed to download {symbol}: {e}")
                    continue

        logger.info("\n✓ Download completed")

    except Exception as e:
        logger.error(f"✗ Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download()