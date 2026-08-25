from __future__ import annotations

import asyncio
import base64
from typing import Any, Protocol

import httpx

from app.errors import UpstreamResponseError, UpstreamUnavailableError

SCHOOL_SEARCH_QUERY = """
query ($text: String!) {
  newSearch {
    schools(query: { text: $text }) {
      edges { node { id name city state } }
    }
  }
}
"""

SCHOOL_PROFILE_QUERY = """
query ($id: ID!) {
  node(id: $id) {
    ... on School { id name city state }
  }
}
"""

PROFESSOR_SEARCH_QUERY = """
query ($text: String!, $sid: ID!) {
  newSearch {
    teachers(query: { text: $text, schoolID: $sid }) {
      edges {
        node {
          id legacyId firstName lastName department avgRating avgDifficulty
          numRatings wouldTakeAgainPercent
          school { id name }
        }
      }
    }
  }
}
"""

PROFESSOR_PROFILE_QUERY = """
query ($id: ID!) {
  node(id: $id) {
    ... on Teacher {
      id legacyId firstName lastName department avgRating avgDifficulty
      numRatings wouldTakeAgainPercent
      school { id name }
    }
  }
}
"""


class RmpProvider(Protocol):
    async def search_schools(self, query: str) -> list[dict[str, Any]]: ...

    async def get_school(self, school_id: str) -> dict[str, Any] | None: ...

    async def search_professors(
        self, query: str, school_id: str
    ) -> list[dict[str, Any]]: ...

    async def get_professor(self, professor_id: str) -> dict[str, Any] | None: ...


class RmpGraphQLClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        api_url: str,
        max_concurrency: int,
    ):
        self.client = client
        self.api_url = api_url
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def _execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = {"query": query, "variables": variables}
        last_error: Exception | None = None
        async with self.semaphore:
            for attempt in range(2):
                try:
                    response = await self.client.post(self.api_url, json=payload)
                    response.raise_for_status()
                    try:
                        body = response.json()
                    except ValueError as exc:
                        raise UpstreamResponseError(
                            "RMP returned invalid JSON"
                        ) from exc
                    if body.get("errors"):
                        raise UpstreamResponseError("RMP returned a GraphQL error")
                    data = body.get("data")
                    if not isinstance(data, dict):
                        raise UpstreamResponseError("RMP returned an invalid response")
                    return data
                except UpstreamResponseError:
                    raise
                except httpx.HTTPError as exc:
                    last_error = exc
                    if attempt == 0:
                        await asyncio.sleep(0.1)
        raise UpstreamUnavailableError("RMP could not be reached") from last_error

    async def search_schools(self, query: str) -> list[dict[str, Any]]:
        data = await self._execute(SCHOOL_SEARCH_QUERY, {"text": query})
        try:
            return [edge["node"] for edge in data["newSearch"]["schools"]["edges"]]
        except (KeyError, TypeError) as exc:
            raise UpstreamResponseError("RMP school search shape changed") from exc

    async def get_school(self, school_id: str) -> dict[str, Any] | None:
        data = await self._execute(SCHOOL_PROFILE_QUERY, {"id": school_id})
        node = data.get("node")
        if node is not None and not isinstance(node, dict):
            raise UpstreamResponseError("RMP school profile shape changed")
        return node

    async def search_professors(
        self, query: str, school_id: str
    ) -> list[dict[str, Any]]:
        data = await self._execute(
            PROFESSOR_SEARCH_QUERY, {"text": query, "sid": school_id}
        )
        try:
            return [edge["node"] for edge in data["newSearch"]["teachers"]["edges"]]
        except (KeyError, TypeError) as exc:
            raise UpstreamResponseError("RMP professor search shape changed") from exc

    async def get_professor(self, professor_id: str) -> dict[str, Any] | None:
        if not professor_id.isdigit():
            raise UpstreamResponseError("Professor ID must be the numeric RMP ID")
        node_id = base64.b64encode(f"Teacher-{professor_id}".encode()).decode()
        data = await self._execute(PROFESSOR_PROFILE_QUERY, {"id": node_id})
        node = data.get("node")
        if node is not None and not isinstance(node, dict):
            raise UpstreamResponseError("RMP professor profile shape changed")
        return node
