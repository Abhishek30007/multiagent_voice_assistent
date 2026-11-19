import asyncio
import time
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()

_redis_pool: Optional[aioredis.Redis] = None
# In-memory lock fallback when Redis is unavailable (e.g. during standalone tests)
_in_memory_locks: dict[str, float] = {}


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Get or initialize the async Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2.0,
            )
            # Ping to verify connection
            await _redis_pool.ping()
        except Exception as e:
            logger.warning(f"Redis is not available at {settings.REDIS_URL}. Using in-memory fallback: {e}")
            _redis_pool = None
    return _redis_pool


async def close_redis_client() -> None:
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


class DistributedSyncLock:
    """Distributed lock using Redis with an automatic in-memory fallback.
    Prevents concurrent duplicate sync runs for the same user/service.
    """

    def __init__(self, lock_key: str, timeout_seconds: int = 600):
        self.lock_key = f"lock:{lock_key}"
        self.timeout_seconds = timeout_seconds
        self.acquired = False

    async def __aenter__(self):
        client = await get_redis_client()
        if client is not None:
            try:
                # SET key val NX EX timeout
                val = f"locked_at_{time.time()}"
                res = await client.set(self.lock_key, val, nx=True, ex=self.timeout_seconds)
                self.acquired = bool(res)
                return self.acquired
            except Exception as e:
                logger.error(f"Error acquiring Redis lock {self.lock_key}: {e}")
        
        # Fallback to in-memory lock
        now = time.time()
        expiry = _in_memory_locks.get(self.lock_key, 0)
        if expiry > now:
            self.acquired = False
        else:
            _in_memory_locks[self.lock_key] = now + self.timeout_seconds
            self.acquired = True
        return self.acquired

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.acquired:
            return
        client = await get_redis_client()
        if client is not None:
            try:
                await client.delete(self.lock_key)
            except Exception as e:
                logger.error(f"Error releasing Redis lock {self.lock_key}: {e}")
        
        # Release in-memory lock
        _in_memory_locks.pop(self.lock_key, None)
