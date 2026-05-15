from limits import parse, strategies
from limits.storage import storage_from_string
from fastapi import Request, HTTPException
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)

# CI-safe storage: Use Redis if available, fallback to memory
# This ensures tests pass even without a Redis instance.
storage_uri = settings.REDIS_URL or "memory://"
try:
    storage = storage_from_string(storage_uri)
    limiter = strategies.MovingWindowRateLimiter(storage)
except Exception as e:
    logger.error(f"Failed to initialize rate limit storage with {storage_uri}: {e}")
    # Fallback to memory if Redis fails
    storage = storage_from_string("memory://")
    limiter = strategies.MovingWindowRateLimiter(storage)

class RateLimiter:
    """
    A stable, production-ready replacement for FastAPILimiter.
    Uses 'limits' (the same engine as slowapi/flask-limiter).
    
    This implementation is CI-safe and doesn't require a live Redis 
    instance to pass basic import and initialization tests.
    """
    def __init__(self, times: int, minutes: int = 1, seconds: int = 0):
        if seconds:
            self.limit_str = f"{times} per {seconds} second"
        else:
            self.limit_str = f"{times} per {minutes} minute"
        
        try:
            self.limit_item = parse(self.limit_str)
        except Exception as e:
            logger.error(f"Invalid rate limit string '{self.limit_str}': {e}")
            self.limit_item = parse("100 per minute")

    async def __call__(self, request: Request):
        # Use IP address as the default identifier
        # In production behind a proxy, ensure X-Forwarded-For is handled.
        identifier = request.client.host if request.client else "127.0.0.1"
        
        try:
            if not limiter.hit(self.limit_item, identifier):
                raise HTTPException(
                    status_code=429, 
                    detail="Too Many Requests. Please try again later."
                )
        except HTTPException:
            raise
        except Exception as e:
            # Fail open: if rate limiting logic fails (e.g. Redis down), 
            # allow the request and log the error.
            logger.error(f"Rate limiter execution error: {e}")
            return
