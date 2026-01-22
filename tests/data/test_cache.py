
# File: tests/data/test_cache.py
"""Tests for cache manager."""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from src.data.models import MarketBar
from src.data.cache.cache_manager import CacheManager


class TestCacheManager:
    """Tests for CacheManager."""

    @pytest.fixture
    def cache(self):
        """Create cache instance."""
        return CacheManager(max_size=100, default_ttl_seconds=60)

    @pytest.fixture
    def sample_bars(self):
        """Create sample bars."""
        return [
            MarketBar(
                symbol="EURUSD",
                timeframe="H1",
                timestamp_utc=datetime(2024, 1, 15, 12 + i, 0, tzinfo=timezone.utc),
                open=Decimal("1.2345"),
                high=Decimal("1.2350"),
                low=Decimal("1.2340"),
                close=Decimal("1.2348"),
                tick_volume=1500,
            )
            for i in range(10)
        ]

    def test_cache_miss(self, cache):
        """Should return None on cache miss."""
        bars = cache.get_bars(
            "EURUSD",
            "H1",
            datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 22, 0, tzinfo=timezone.utc),
        )

        assert bars is None
        assert cache.misses == 1

    def test_cache_hit(self, cache, sample_bars):
        """Should return cached bars on hit."""
        start = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 22, 0, tzinfo=timezone.utc)

        # Cache bars
        cache.set_bars(sample_bars, "EURUSD", "H1", start, end)

        # Retrieve
        bars = cache.get_bars("EURUSD", "H1", start, end)

        assert bars == sample_bars
        assert cache.hits == 1

    def test_ttl_expiration(self, cache, sample_bars):
        """Should expire cached data after TTL."""
        start = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 22, 0, tzinfo=timezone.utc)

        # Cache with 0 second TTL should not cache at all
        cache.set_bars(sample_bars, "EURUSD", "H1", start, end, ttl_seconds=0)

        # Should be expired immediately -> Should not be cached
        bars = cache.get_bars("EURUSD", "H1", start, end)
        assert bars is None

        # Test with very short TTL
        cache.set_bars(sample_bars, "EURUSD", "H1", start, end, ttl_seconds=0.001)
