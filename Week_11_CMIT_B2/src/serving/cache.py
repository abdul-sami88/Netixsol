"""
High-Performance Caching Layer for ShopKaro Serving Engine
Implements:
1. Multi-tier caching: In-memory LRU + TTL cache with optional Redis backend
2. Sub-10ms latency for precomputed & cached recommendations (< 100ms target)
3. Real-time session-aware cache invalidation and click stream enrichment
"""

import time
import json
from typing import Dict, Any, Optional, List
from collections import OrderedDict
import threading


class CacheManager:
    """
    Thread-safe, high-speed multi-tier cache.
    Falls back gracefully to high-performance in-memory LRU if Redis is offline.
    """
    def __init__(self, max_size: int = 10000, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        # Real-time session click history: user_id -> list of recently clicked product_ids
        self._session_clicks: Dict[str, List[Dict[str, Any]]] = {}

        # Optional Redis connection
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        try:
            import redis
            client = redis.Redis(host="localhost", port=6379, db=0, socket_timeout=0.2)
            client.ping()
            self.redis_client = client
            print("[CACHE] Connected successfully to local Redis instance.")
        except Exception:
            self.redis_client = None
            # print("[CACHE] Redis offline or not installed. Operating with high-speed in-memory LRU cache.")

    def get(self, key: str) -> Optional[Any]:
        """Retrieves value from cache if present and not expired."""
        # 1. Try Redis if available
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val.decode("utf-8"))
            except Exception:
                pass

        # 2. In-Memory LRU Cache
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check expiration
            expire_at = self._timestamps.get(key, 0)
            if time.time() > expire_at:
                del self._cache[key]
                del self._timestamps[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Stores value in cache with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        
        # 1. Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            except Exception:
                pass

        # 2. Store in-memory
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            self._timestamps[key] = time.time() + ttl
            
            # Evict oldest if exceeding max_size
            if len(self._cache) > self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                if oldest_key in self._timestamps:
                    del self._timestamps[oldest_key]

    def invalidate(self, key_prefix: str):
        """Invalidates all cache keys matching prefix."""
        with self._lock:
            keys_to_del = [k for k in self._cache.keys() if k.startswith(key_prefix)]
            for k in keys_to_del:
                del self._cache[k]
                if k in self._timestamps:
                    del self._timestamps[k]

    def record_session_click(self, user_id: str, product_id: str, category: str):
        """
        Records a real-time session click event.
        Invalidates cached recommendations for user to inject real-time intent!
        """
        with self._lock:
            if user_id not in self._session_clicks:
                self._session_clicks[user_id] = []
            self._session_clicks[user_id].append({
                "product_id": product_id,
                "category": category,
                "timestamp": time.time()
            })
            # Keep only last 5 clicks
            self._session_clicks[user_id] = self._session_clicks[user_id][-5:]
            
        # Invalidate recommendation cache for this user
        self.invalidate(f"recs:{user_id}")

    def get_session_clicks(self, user_id: str) -> List[Dict[str, Any]]:
        """Returns recent in-session click events for user."""
        with self._lock:
            return list(self._session_clicks.get(user_id, []))


# Global singleton cache instance
global_cache = CacheManager()

