import time

from redis.exceptions import RedisError

from app.core.redis import blacklist_redis, handle_redis_error


def _blacklist_key(jti: str) -> str:
    return f"token:blacklist:{jti}"


async def blacklist_token(jti: str, expires_at: int | float) -> None:
    ttl_seconds = max(1, int(expires_at - time.time()))
    try:
        await blacklist_redis().setex(_blacklist_key(jti), ttl_seconds, "1")
    except RedisError as exc:
        handle_redis_error(exc, "blacklist token")


async def is_token_blacklisted(jti: str) -> bool:
    try:
        return bool(await blacklist_redis().exists(_blacklist_key(jti)))
    except RedisError as exc:
        handle_redis_error(exc, "check token blacklist")
        return False
