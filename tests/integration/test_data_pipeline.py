# ============================================================================
# tests/integration/test_data_pipeline.py - Data Pipeline Integration Tests
# ============================================================================

"""
Integration tests for data pipeline.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from database.models import Trade
import pytest
from datetime import datetime, timedelta


class TestDataPipeline:
    """Test data pipeline integration."""

    def test_historical_data_download(self, mock_mt5_connector):
        """Test downloading historical data."""
        mock_mt5_connector.connect()

        df = mock_mt5_connector.get_bars("EURUSD.m", "H1", 100)

        assert not df.empty
        assert len(df) == 100
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close'])

    def test_database_trade_storage(self, db_session, sample_account):
        """Test storing trades in database."""
        trade = Trade(
            ticket=99999,
            account_id=sample_account.id,
            symbol="EURUSD",
            direction="BUY",
            volume=0.1,
            price_open=1.1000,
            time_open=datetime.now(),
            status="OPEN"
        )

        db_session.add(trade)
        db_session.commit()

        # Retrieve trade
        stored_trade = db_session.query(Trade).filter_by(ticket=99999).first()

        assert stored_trade is not None
        assert stored_trade.symbol == "EURUSD"
        assert stored_trade.account_id == sample_account.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])