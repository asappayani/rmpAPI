from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import ValidationError

from app.config import Settings
from app.errors import ServiceError, UpstreamResponseError
from app.schemas.professor_schema import ProfessorOut
from app.schemas.school_schema import SchoolOut
from app.services.cache import CacheResult, RedisStore
from app.services.rmp_client import RmpProvider

T = TypeVar("T")


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _cache_key(namespace: str, *values: str) -> str:
    digest = hashlib.sha256("\x1f".join(values).encode()).hexdigest()
    return f"rmp:v1:{namespace}:{digest}"


class RmpService:
    def __init__(
        self,
        provider: RmpProvider,
        cache: RedisStore,
        settings: Settings,
    ):
        self.provider = provider
        self.cache = cache
        self.settings = settings

    async def _load(
        self,
        key: str,
        ttl: int,
        loader: Callable[[], Awaitable[T]],
    ) -> CacheResult[T]:
        cached = await self.cache.get(key)
        if cached.cached and not cached.stale:
            return cached

        acquired = await self.cache.acquire_lock(key)
        if not acquired:
            for _ in range(5):
                await asyncio.sleep(0.1)
                refreshed = await self.cache.get(key)
                if refreshed.cached and not refreshed.stale:
                    return refreshed
            if cached.cached:
                return CacheResult(cached.value, True, True)

        try:
            value = await loader()
            effective_ttl = self.settings.empty_cache_seconds if not value else ttl
            await self.cache.set(key, value, effective_ttl)
            return CacheResult(value, False, False)
        except ServiceError:
            if cached.cached:
                return CacheResult(cached.value, True, True)
            raise
        finally:
            if acquired:
                await self.cache.release_lock(key)

    @staticmethod
    def _school(node: dict[str, Any]) -> dict[str, Any]:
        try:
            if not node.get("id") or not node.get("name"):
                raise ValueError("missing school identity")
            return SchoolOut(
                id=str(node["id"]),
                name=str(node["name"]),
                city=node.get("city"),
                state=node.get("state"),
            ).model_dump(mode="json")
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise UpstreamResponseError("RMP returned an invalid school") from exc

    @staticmethod
    def _professor(node: dict[str, Any]) -> dict[str, Any]:
        try:
            first_name = str(node.get("firstName") or "").strip()
            last_name = str(node.get("lastName") or "").strip()
            if not node.get("legacyId") or not (first_name or last_name):
                raise ValueError("missing professor identity")
            legacy_id = str(node["legacyId"])
            school = node.get("school") or {}
            return ProfessorOut(
                id=legacy_id,
                source_id=node.get("id"),
                first_name=first_name,
                last_name=last_name,
                display_name=" ".join(
                    part for part in (first_name, last_name) if part
                ),
                department=node.get("department"),
                school_id=school.get("id"),
                school_name=school.get("name"),
                average_rating=node.get("avgRating"),
                average_difficulty=node.get("avgDifficulty"),
                would_take_again_percent=node.get("wouldTakeAgainPercent"),
                number_of_ratings=node.get("numRatings"),
                profile_url=(
                    f"https://www.ratemyprofessors.com/professor/{legacy_id}"
                ),
                retrieved_at=datetime.now(UTC),
            ).model_dump(mode="json")
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise UpstreamResponseError("RMP returned an invalid professor") from exc

    async def search_schools(
        self, query: str, limit: int
    ) -> CacheResult[list[dict[str, Any]]]:
        async def load() -> list[dict[str, Any]]:
            nodes = await self.provider.search_schools(query)
            return [self._school(node) for node in nodes]

        result = await self._load(
            _cache_key("school-search", _normalized(query)),
            self.settings.school_cache_seconds,
            load,
        )
        return CacheResult((result.value or [])[:limit], result.cached, result.stale)

    async def get_school(
        self, school_id: str
    ) -> CacheResult[dict[str, Any] | None]:
        async def load() -> dict[str, Any] | None:
            node = await self.provider.get_school(school_id)
            return self._school(node) if node else None

        return await self._load(
            _cache_key("school", school_id),
            self.settings.school_cache_seconds,
            load,
        )

    async def search_professors(
        self, query: str, school_id: str, limit: int
    ) -> CacheResult[list[dict[str, Any]]]:
        async def load() -> list[dict[str, Any]]:
            nodes = await self.provider.search_professors(query, school_id)
            return [self._professor(node) for node in nodes]

        result = await self._load(
            _cache_key("professor-search", _normalized(query), school_id),
            self.settings.professor_search_cache_seconds,
            load,
        )
        return CacheResult((result.value or [])[:limit], result.cached, result.stale)

    async def get_professor(
        self, professor_id: str
    ) -> CacheResult[dict[str, Any] | None]:
        async def load() -> dict[str, Any] | None:
            node = await self.provider.get_professor(professor_id)
            return self._professor(node) if node else None

        return await self._load(
            _cache_key("professor", professor_id),
            self.settings.professor_profile_cache_seconds,
            load,
        )
