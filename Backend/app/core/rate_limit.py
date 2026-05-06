import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from .config import settings
from .redis import handle_redis_error, rate_limit_redis


def rate_limit(
    key_prefix: str,
    limit: int | None = None,
    window_seconds: int | None = None,
) -> Callable[[Request], object]:
    """Return a FastAPI dependency that limits requests per client IP."""

    max_requests = limit or settings.RATE_LIMIT_REQUESTS
    window = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS

    async def dependency(request: Request) -> None:
        forwarded_for = request.headers.get("x-forwarded-for")
        ip_address = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else request.client.host if request.client else "unknown"
        )
        bucket = int(time.time() // window)
        key = f"rate:{key_prefix}:{ip_address}:{bucket}"

        try:
            current = await rate_limit_redis().incr(key)
            if current == 1:
                await rate_limit_redis().expire(key, window)
        except RedisError as exc:
            handle_redis_error(exc, f"rate limit {key_prefix}")
            return

        if current > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {window} seconds.",
                headers={"Retry-After": str(window)},
            )

    return dependency
