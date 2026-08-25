from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.cache import CacheResult


class AllowingLimiter:
    async def check(self, identity):
        return 120, 119


class FakeService:
    async def search_professors(self, query, school_id, limit):
        return CacheResult([], False, False)


def test_data_endpoints_require_service_token():
    settings = replace(
        Settings.from_env(),
        service_token="secret-token",
        primary_school_id="school-1",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        app.state.rate_limiter = AllowingLimiter()
        app.state.rmp_service = FakeService()

        unauthorized = client.get("/api/v1/professors/search?q=Ada")
        authorized = client.get(
            "/api/v1/professors/search?q=Ada",
            headers={"Authorization": "Bearer secret-token"},
        )

    assert unauthorized.status_code == 401
    assert unauthorized.json()["request_id"]
    assert authorized.status_code == 200
    assert authorized.json()["data"] == []
    assert authorized.json()["meta"]["count"] == 0
    assert authorized.headers["X-RateLimit-Remaining"] == "119"


def test_validation_uses_problem_details():
    settings = replace(Settings.from_env(), service_token="secret-token")
    app = create_app(settings)
    with TestClient(app) as client:
        app.state.rate_limiter = AllowingLimiter()
        app.state.rmp_service = FakeService()
        response = client.get(
            "/api/v1/professors/search?q=",
            headers={"Authorization": "Bearer secret-token"},
        )

    assert response.status_code == 422
    assert response.json()["title"] == "Validation Error"
    assert response.json()["request_id"]
