from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.errors import DependencyUnavailableError, RateLimitError

T = TypeVar("T")


@dataclass(slots=True)
class CacheResult(Generic[T]):
    value: T | None
    cached: bool
    stale: bool


class RedisStore:
    def __init__(self, redis: Redis, *, stale_seconds: int):
        self.redis = redis
        self.stale_seconds = stale_seconds

    async def ping(self) -> bool:
        try:
            return bool(await self.redis.ping())
        except RedisError:
            return False

    async def get(self, key: str) -> CacheResult:
        try:
            raw = await self.redis.get(key)
        except RedisError as exc:
            raise DependencyUnavailableError("Redis is unavailable") from exc
        if raw is None:
            return CacheResult(None, False, False)

        try:
            entry = json.loads(raw)
            stale = time.time() > float(entry["fresh_until"])
            return CacheResult(entry["value"], True, stale)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            await self.redis.delete(key)
            return CacheResult(None, False, False)

    async def set(self, key: str, value: Any, fresh_seconds: int) -> None:
        entry = {
            "fresh_until": time.time() + fresh_seconds,
            "value": value,
        }
        try:
            await self.redis.set(
                key,
                json.dumps(entry, separators=(",", ":")),
                ex=fresh_seconds + self.stale_seconds,
            )
        except RedisError as exc:
            raise DependencyUnavailableError("Redis is unavailable") from exc

    async def acquire_lock(self, key: str, seconds: int = 10) -> bool:
        try:
            return bool(await self.redis.set(f"lock:{key}", "1", ex=seconds, nx=True))
        except RedisError as exc:
            raise DependencyUnavailableError("Redis is unavailable") from exc

    async def release_lock(self, key: str) -> None:
        try:
            await self.redis.delete(f"lock:{key}")
        except RedisError:
            pass


class RedisRateLimiter:
    def __init__(self, redis: Redis, limit: int):
        self.redis = redis
        self.limit = limit

    async def check(self, identity: str) -> tuple[int, int]:
        minute = int(time.time() // 60)
        key = f"rate:{identity}:{minute}"
        try:
            count = int(await self.redis.incr(key))
            if count == 1:
                await self.redis.expire(key, 61)
        except RedisError as exc:
            raise DependencyUnavailableError("Redis is unavailable") from exc

        remaining = max(0, self.limit - count)
        if count > self.limit:
            retry_after = 60 - int(time.time() % 60)
            raise RateLimitError(
                "Internal request quota exceeded",
                headers={"Retry-After": str(retry_after)},
            )
        return self.limit, remaining
