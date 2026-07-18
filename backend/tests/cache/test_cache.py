import pytest

from app.cache.service import CacheService


@pytest.fixture
def cache() -> CacheService:
    return CacheService.__new__(CacheService)


class TestCacheServiceMemory:
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: CacheService) -> None:
        cache._memory = {}
        cache._initialized = True
        cache._redis = None

        await cache.set("key1", {"data": "value"}, ttl=60)
        result = await cache.get("key1")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_missing_key(self, cache: CacheService) -> None:
        cache._memory = {}
        cache._initialized = True
        cache._redis = None

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache: CacheService) -> None:
        cache._memory = {}
        cache._initialized = True
        cache._redis = None

        await cache.set("key1", "value")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_increment(self, cache: CacheService) -> None:
        cache._memory = {}
        cache._initialized = True
        cache._redis = None

        count1 = await cache.increment("counter")
        count2 = await cache.increment("counter")
        count3 = await cache.increment("counter")
        assert count1 == 1
        assert count2 == 2
        assert count3 == 3

    @pytest.mark.asyncio
    async def test_set_overwrites(self, cache: CacheService) -> None:
        cache._memory = {}
        cache._initialized = True
        cache._redis = None

        await cache.set("key1", "first")
        await cache.set("key1", "second")
        result = await cache.get("key1")
        assert result == "second"

    @pytest.mark.asyncio
    async def test_json_roundtrip(self, cache: CacheService) -> None:
        cache._memory = {}
        cache._initialized = True
        cache._redis = None

        data = {
            "score": 85,
            "grade": "B",
            "categories": [{"name": "Testing", "score": 18}],
        }
        await cache.set("report:123", data)
        result = await cache.get("report:123")
        assert result == data
