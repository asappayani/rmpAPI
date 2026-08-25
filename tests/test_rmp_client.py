from __future__ import annotations

import base64

import httpx
import pytest

from app.errors import UpstreamResponseError
from app.services.rmp_client import RmpGraphQLClient


@pytest.mark.asyncio
async def test_professor_lookup_converts_numeric_id_to_relay_id():
    captured = {}

    async def handler(request: httpx.Request):
        captured.update(__import__("json").loads(request.content))
        return httpx.Response(
            200,
            json={
                "data": {
                    "node": {
                        "id": "node-id",
                        "legacyId": 123,
                        "firstName": "Ada",
                        "lastName": "Lovelace",
                    }
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RmpGraphQLClient(client, "https://example.test/graphql", 1)
        result = await provider.get_professor("123")

    expected = base64.b64encode(b"Teacher-123").decode()
    assert captured["variables"]["id"] == expected
    assert result["legacyId"] == 123


@pytest.mark.asyncio
async def test_invalid_upstream_json_maps_to_bad_gateway():
    async def handler(request: httpx.Request):
        return httpx.Response(200, content=b"not-json")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RmpGraphQLClient(client, "https://example.test/graphql", 1)
        with pytest.raises(UpstreamResponseError) as error:
            await provider.search_schools("Texas A&M")

    assert error.value.status_code == 502
