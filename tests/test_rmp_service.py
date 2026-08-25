from __future__ import annotations

from dataclasses import replace

import pytest

from app.config import Settings
from app.errors import UpstreamUnavailableError
from app.services.cache import CacheResult
from app.services.rmp_service import RmpService


class FakeCache:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key, CacheResult(None, False, False))

    async def set(self, key, value, fresh_seconds):
        self.values[key] = CacheResult(value, True, False)

    async def acquire_lock(self, key, seconds=10):
        return True

    async def release_lock(self, key):
        return None


class FakeProvider:
    def __init__(self):
        self.professor_calls = 0

    async def search_schools(self, query):
        return [{"id": "school-1", "name": "Texas A&M", "city": "College Station", "state": "TX"}]

    async def get_school(self, school_id):
        return {"id": school_id, "name": "Texas A&M", "city": "College Station", "state": "TX"}

    async def search_professors(self, query, school_id):
        self.professor_calls += 1
        return [
            {
                "id": "teacher-node",
                "legacyId": 123,
                "firstName": "Ada",
                "lastName": "Lovelace",
                "department": "Computer Science",
                "avgRating": 4.8,
                "avgDifficulty": 3.1,
                "wouldTakeAgainPercent": 95,
                "numRatings": 42,
                "school": {"id": school_id, "name": "Texas A&M"},
            }
        ]

    async def get_professor(self, professor_id):
        return (await self.search_professors("Ada Lovelace", "school-1"))[0]


def settings():
    return replace(
        Settings.from_env(),
        service_token="test-token",
        primary_school_id="school-1",
    )


@pytest.mark.asyncio
async def test_professor_search_maps_stable_fields_and_caches():
    provider = FakeProvider()
    service = RmpService(provider, FakeCache(), settings())

    first = await service.search_professors("Ada", "school-1", 20)
    second = await service.search_professors("  ADA  ", "school-1", 20)

    professor = first.value[0]
    assert professor["id"] == "123"
    assert professor["display_name"] == "Ada Lovelace"
    assert professor["school_id"] == "school-1"
    assert professor["profile_url"].endswith("/123")
    assert first.cached is False
    assert second.cached is True
    assert provider.professor_calls == 1


@pytest.mark.asyncio
async def test_stale_result_is_used_when_upstream_fails():
    class FailingProvider(FakeProvider):
        async def search_schools(self, query):
            raise UpstreamUnavailableError("down")

    cache = FakeCache()
    service = RmpService(FakeProvider(), cache, settings())
    await service.search_schools("Texas A&M", 20)
    for key, result in cache.values.items():
        cache.values[key] = CacheResult(result.value, True, True)
    service.provider = FailingProvider()

    key_result = await service.search_schools("Texas A&M", 20)
    assert key_result.value[0]["name"] == "Texas A&M"
    assert key_result.stale is True


@pytest.mark.asyncio
async def test_invalid_professor_payload_is_an_upstream_error():
    class InvalidProvider(FakeProvider):
        async def search_professors(self, query, school_id):
            return [{"firstName": "Missing ID"}]

    service = RmpService(InvalidProvider(), FakeCache(), settings())
    with pytest.raises(Exception) as error:
        await service.search_professors("Missing", "school-1", 20)
    assert error.value.status_code == 502
