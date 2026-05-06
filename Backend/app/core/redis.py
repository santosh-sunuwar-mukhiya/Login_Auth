import json
import logging
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def get_redis_client(url: str) -> Redis:
    return Redis.from_url(url, decode_responses=True)


def blacklist_redis() -> Redis:
    return get_redis_client(settings.redis_blacklist_url)


def rate_limit_redis() -> Redis:
    return get_redis_client(settings.redis_rate_limit_url)


def cache_redis() -> Redis:
    return get_redis_client(settings.redis_cache_url)


def handle_redis_error(exc: RedisError, action: str) -> None:
    if settings.REDIS_FAIL_OPEN:
        logger.warning("Redis unavailable while trying to %s: %s", action, exc)
        return
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Redis is unavailable. Please try again later.",
    ) from exc


async def cache_get_json(key: str) -> Any | None:
    try:
        value = await cache_redis().get(key)
    except RedisError as exc:
        handle_redis_error(exc, f"read cache key {key}")
        return None

    return json.loads(value) if value else None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        await cache_redis().setex(key, ttl_seconds, json.dumps(value, default=str))
    except RedisError as exc:
        handle_redis_error(exc, f"write cache key {key}")


async def cache_delete_pattern(pattern: str) -> None:
    try:
        keys = [key async for key in cache_redis().scan_iter(match=pattern)]
        if keys:
            await cache_redis().delete(*keys)
    except RedisError as exc:
        handle_redis_error(exc, f"delete cache pattern {pattern}")


async def close_redis_clients() -> None:
    for client in list(get_redis_client.cache_info().__dict__.values()):
        _ = client
