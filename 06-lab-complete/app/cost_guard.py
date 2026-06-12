import time
import logging
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
        logger.info("Cost Guard connected to Redis successfully.")
    except Exception as e:
        logger.warning(f"Cost Guard Redis connection failed, falling back to memory: {e}")

# In-memory fallback
_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")

# Price per 1k tokens (GPT-4o-mini price estimation)
PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006

def check_budget(user_id: str, estimated_cost: float = 0.0) -> None:
    """
    Checks if the user has enough budget remaining.
    Raises 402 Payment Required if the budget is exceeded.
    """
    global _daily_cost, _cost_reset_day
    today = time.strftime("%Y-%m-%d")
    
    if USE_REDIS and _redis:
        try:
            redis_key = f"cost:{user_id}:{today}"
            current = float(_redis.get(redis_key) or 0.0)
            if current + estimated_cost >= settings.daily_budget_usd:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Daily budget exceeded",
                        "used_usd": current,
                        "budget_usd": settings.daily_budget_usd,
                        "resets_at": "midnight UTC",
                    }
                )
            return
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis check budget failed, falling back to memory: {e}")

    # In-memory fallback
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today
    if _daily_cost + estimated_cost >= settings.daily_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Daily budget exceeded",
                "used_usd": _daily_cost,
                "budget_usd": settings.daily_budget_usd,
                "resets_at": "midnight UTC",
            }
        )

def record_cost(user_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculates and records the cost for the LLM invocation.
    Updates Redis if available, or falls back to local memory.
    """
    global _daily_cost, _cost_reset_day
    today = time.strftime("%Y-%m-%d")
    cost = (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS + (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    
    if USE_REDIS and _redis:
        try:
            redis_key = f"cost:{user_id}:{today}"
            current = _redis.incrbyfloat(redis_key, cost)
            _redis.expire(redis_key, 86400 * 2) # keep for 2 days
            logger.info(f"Cost recorded (Redis) for user {user_id}: +${cost:.5f} (total: ${current:.5f})")
            return current
        except Exception as e:
            logger.warning(f"Redis record cost failed, falling back to memory: {e}")

    # In-memory fallback
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today
    _daily_cost += cost
    logger.info(f"Cost recorded (Memory) for user {user_id}: +${cost:.5f} (total: {_daily_cost:.5f})")
    return _daily_cost

def get_total_cost(user_id: str) -> float:
    """Gets the current daily cost for the user."""
    global _daily_cost, _cost_reset_day
    today = time.strftime("%Y-%m-%d")
    if USE_REDIS and _redis:
        try:
            redis_key = f"cost:{user_id}:{today}"
            return float(_redis.get(redis_key) or 0.0)
        except Exception:
            pass
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today
    return _daily_cost
