"""
Redis service for caching and rate limiting
"""
import redis
from typing import Optional, Any
import json
import structlog
from config import settings

logger = structlog.get_logger()


class RedisService:
    """Redis service wrapper"""

    def __init__(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get failed: {e}", key=key)
            return None

    def set(self, key: str, value: Any, expiration: int = 3600) -> bool:
        """Set value in cache with expiration (seconds)"""
        try:
            return self.client.setex(
                key,
                expiration,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Redis set failed: {e}", key=key)
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete failed: {e}", key=key)
            return False

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment failed: {e}", key=key)
            return 0

    def check_rate_limit(self, identifier: str, limit: int, window: int = 60) -> bool:
        """
        Check rate limit for identifier
        Returns True if under limit, False if over limit
        """
        key = f"rate_limit:{identifier}"
        try:
            current = self.client.get(key)
            if current is None:
                self.client.setex(key, window, 1)
                return True

            current_count = int(current)
            if current_count >= limit:
                return False

            self.client.incr(key)
            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}", identifier=identifier)
            return True  # Fail open

    def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire distributed lock"""
        try:
            return bool(self.client.set(
                f"lock:{lock_name}",
                "1",
                nx=True,
                ex=timeout
            ))
        except Exception as e:
            logger.error(f"Lock acquisition failed: {e}", lock=lock_name)
            return False

    def release_lock(self, lock_name: str) -> bool:
        """Release distributed lock"""
        try:
            return bool(self.client.delete(f"lock:{lock_name}"))
        except Exception as e:
            logger.error(f"Lock release failed: {e}", lock=lock_name)
            return False


# Global instance
redis_client = RedisService()
