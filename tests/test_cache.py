from __future__ import annotations

import json
import time

import pytest

from app.errors import RateLimitError
from app.services.cache import RedisRateLimiter, RedisStore


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def ping(self):
        return True

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.values:
            return None
        self.values[key] = value
        return True

    async def delete(self, key):
        self.values.pop(key, None)

    async def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    async def expire(self, key, seconds):
        return True


@pytest.mark.asyncio
async def test_cache_distinguishes_fresh_and_stale_values():
    redis = FakeRedis()
    store = RedisStore(redis, stale_seconds=60)
    await store.set("key", {"answer": 42}, 30)

    fresh = await store.get("key")
    assert fresh.cached is True
    assert fresh.stale is False

    entry = json.loads(redis.values["key"])
    entry["fresh_until"] = time.time() - 1
    redis.values["key"] = json.dumps(entry)
    stale = await store.get("key")
    assert stale.cached is True
    assert stale.stale is True


@pytest.mark.asyncio
async def test_rate_limiter_rejects_requests_over_limit():
    limiter = RedisRateLimiter(FakeRedis(), limit=2)
    assert await limiter.check("backend") == (2, 1)
    assert await limiter.check("backend") == (2, 0)
    with pytest.raises(RateLimitError) as error:
        await limiter.check("backend")
    assert error.value.headers["Retry-After"]
