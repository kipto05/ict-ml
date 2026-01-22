# ============================================================================
# File: src/data/cache/cache_manager.py
# Market data caching system
# ============================================================================

"""
Market data cache manager.

Caches validated data to reduce database load and improve performance.

Design principles:
- Cache only validated data
- Deterministic cache keys
- Explicit invalidation
- No stale data
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json
import logging

from src.data.models import MarketBar
from src.core.logger import main_logger

logger = main_logger


class CacheManager:
    """
    In-memory cache for market data.

    Features:
    - LRU eviction
    - TTL support
    - Deterministic keys
    - Thread-safe (for single-threaded async)
    """

    def __init__(
            self,
            max_size: int = 10000,
            default_ttl_seconds: int = 3600
    ):
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of cache entries
            default_ttl_seconds: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds

        # LRU cache: key -> (value, expiry_time)
        self._cache: OrderedDict = OrderedDict()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _make_key(
            self,
            prefix: str,
            symbol: str,
            timeframe: str,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            account_id: Optional[int] = None,
            **kwargs
    ) -> str:
        """
        Create deterministic cache key.

        Args:
            prefix: Key prefix (e.g., 'bars', 'session')
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime
            account_id: Account ID
            **kwargs: Additional key components

        Returns:
            Deterministic cache key
        """
        key_parts = [
            prefix,
            symbol,
            timeframe,
        ]

        if start_time:
            key_parts.append(start_time.isoformat())
        if end_time:
            key_parts.append(end_time.isoformat())
        if account_id is not None:
            key_parts.append(str(account_id))

        # Add any additional kwargs
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True))

        # Create hash for long keys
        key_str = "|".join(str(p) for p in key_parts)
        if len(key_str) > 200:
            key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
            return f"{prefix}:{key_hash}"

        return key_str

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self.misses += 1
            return None

        value, expiry = self._cache[key]

        # Check expiry
        if expiry and datetime.utcnow() > expiry:
            # Expired - remove and return None
            del self._cache[key]
            self.misses += 1
            return None

        # Move to end (LRU)
        self._cache.move_to_end(key)
        self.hits += 1

        return value

    def set(
            self,
            key: str,
            value: Any,
            ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (None = use default)
        """
        # Calculate expiry
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        if ttl == 0:
            # Don't cache at all if TTL is 0
            return
        elif ttl < 0:
            # Never expire
            expiry = None
        else:
            # Expire after ttl seconds
            expiry = datetime.utcnow() + timedelta(seconds=ttl)

        # Store value
        self._cache[key] = (value, expiry)
        self._cache.move_to_end(key)

        # Evict if over size
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)  # Remove oldest
            self.evictions += 1

    def get_bars(
            self,
            symbol: str,
            timeframe: str,
            start_time: datetime,
            end_time: datetime,
            account_id: Optional[int] = None
    ) -> Optional[List[MarketBar]]:
        """
        Get cached bars for a time range.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime
            account_id: Account ID filter

        Returns:
            List of cached MarketBars or None if not cached
        """
        key = self._make_key(
            'bars',
            symbol,
            timeframe,
            start_time,
            end_time,
            account_id
        )

        bars = self.get(key)

        if bars:
            logger.debug(
                f"Cache HIT: {symbol} {timeframe} "
                f"{start_time} to {end_time}"
            )
        else:
            logger.debug(
                f"Cache MISS: {symbol} {timeframe} "
                f"{start_time} to {end_time}"
            )

        return bars

    def set_bars(
            self,
            bars: List[MarketBar],
            symbol: str,
            timeframe: str,
            start_time: datetime,
            end_time: datetime,
            account_id: Optional[int] = None,
            ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Cache bars for a time range.

        Args:
            bars: List of MarketBars to cache
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime
            account_id: Account ID
            ttl_seconds: Time-to-live
        """
        if not bars:
            return

        key = self._make_key(
            'bars',
            symbol,
            timeframe,
            start_time,
            end_time,
            account_id
        )

        self.set(key, bars, ttl_seconds)

        logger.debug(
            f"Cached {len(bars)} bars: {symbol} {timeframe} "
            f"{start_time} to {end_time}"
        )

    def invalidate_bars(
            self,
            symbol: str,
            timeframe: str,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            account_id: Optional[int] = None
    ) -> int:
        """
        Invalidate cached bars.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start datetime (None = invalidate all for symbol/tf)
            end_time: End datetime
            account_id: Account ID

        Returns:
            Number of cache entries invalidated
        """
        if start_time is None or end_time is None:
            # Invalidate all for symbol/timeframe
            pattern = f"bars|{symbol}|{timeframe}"
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(pattern)]
        else:
            # Invalidate specific range
            key = self._make_key(
                'bars',
                symbol,
                timeframe,
                start_time,
                end_time,
                account_id
            )
            keys_to_remove = [key] if key in self._cache else []

        for key in keys_to_remove:
            del self._cache[key]

        logger.info(
            f"Invalidated {len(keys_to_remove)} cache entries for "
            f"{symbol} {timeframe}"
        )

        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear entire cache."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions,
        }

    def reset_statistics(self) -> None:
        """Reset cache statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0


# Global cache manager instance
cache_manager = CacheManager(max_size=10000, default_ttl_seconds=3600)