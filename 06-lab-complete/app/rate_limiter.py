import time
import logging
from collections import defaultdict, deque
from fastapi import HTTPException
import redis
from app.config import settings

logger = logging.getLogger(__name__)

# Redis client setup for stateless operations
_redis = None
USE_REDIS = False
if settings.redis_url:
    try:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
        _redis.ping()
        USE_REDIS = True
        logger.info("Rate Limiter connected to Redis successfully.")
    except Exception as e:
        logger.warning(f"Rate Limiter Redis connection failed, falling back to memory: {e}")

# In-memory fallback
_rate_windows = defaultdict(deque)

def check_rate_limit(key: str):
    """
    Checks the rate limit for a given key.
    If Redis is available, uses a sliding window based on Sorted Sets.
    Otherwise, falls back to an in-memory deque.
    """
    now = time.time()
    
    if USE_REDIS and _redis:
        try:
            redis_key = f"rate_limit:{key}"
            # Remove timestamps older than 60 seconds
            _redis.zremrangebyscore(redis_key, 0, now - 60)
            # Count the remaining requests
            count = _redis.zcard(redis_key)
            if count >= settings.rate_limit_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                    headers={"Retry-After": "60"},
                )
            # Add current timestamp
            _redis.zadd(redis_key, {str(now): now})
            _redis.expire(redis_key, 65)
            return
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis rate limiting failed, falling back to memory: {e}")

    # In-memory fallback
    window = _rate_windows[key]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)
