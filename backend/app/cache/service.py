import contextlib
import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self) -> None:
        self._redis = None
        self._memory: dict[str, str] = {}
        self._initialized = False

    async def _get_redis(self):  # type: ignore[no-untyped-def]
        if self._initialized:
            return self._redis

        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self._redis.ping()
            self._initialized = True
            logger.info("Connected to Redis")
            return self._redis
        except Exception:
            logger.warning("Redis unavailable, using in-memory cache")
            self._redis = None
            self._initialized = True
            return None

    async def get(self, key: str) -> Any | None:  # noqa: ANN401
        redis = await self._get_redis()
        if redis:
            try:
                value = await redis.get(key)
                if value:
                    return json.loads(value)
                return None
            except Exception:
                logger.warning("Redis get failed for key: %s", key)
                return None

        value = self._memory.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,  # noqa: ANN401
    ) -> None:
        serialized = json.dumps(value)
        redis = await self._get_redis()
        if redis:
            try:
                await redis.set(key, serialized, ex=ttl)
                return
            except Exception:
                logger.warning("Redis set failed for key: %s", key)

        self._memory[key] = serialized

    async def delete(self, key: str) -> None:
        redis = await self._get_redis()
        if redis:
            try:
                await redis.delete(key)
                return
            except Exception:
                logger.warning("Redis delete failed for key: %s", key)

        self._memory.pop(key, None)

    async def increment(self, key: str, ttl: int = 3600) -> int:
        redis = await self._get_redis()
        if redis:
            try:
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, ttl)
                return count
            except Exception:
                logger.warning("Redis increment failed for key: %s", key)

        count = int(self._memory.get(key, "0")) + 1
        self._memory[key] = str(count)
        return count

    async def close(self) -> None:
        if self._redis:
            with contextlib.suppress(Exception):
                await self._redis.close()


cache_service = CacheService()
