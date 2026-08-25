from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_origins(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    service_token: str
    redis_url: str
    primary_school_id: str | None
    allowed_origins: tuple[str, ...]
    docs_enabled: bool
    rmp_api_url: str
    rmp_timeout_seconds: float
    request_limit_per_minute: int
    max_upstream_concurrency: int
    school_cache_seconds: int
    professor_search_cache_seconds: int
    professor_profile_cache_seconds: int
    empty_cache_seconds: int
    stale_cache_seconds: int

    @classmethod
    def from_env(cls) -> Settings:
        environment = os.getenv("ENVIRONMENT", "development").strip().lower()
        token = os.getenv("RMP_SERVICE_TOKEN", "")
        if not token and environment != "production":
            token = "development-token-change-me"
        if environment == "production" and len(token) < 32:
            raise RuntimeError(
                "RMP_SERVICE_TOKEN must contain at least 32 characters in production"
            )

        primary_school_id = os.getenv("PRIMARY_SCHOOL_ID") or None
        return cls(
            environment=environment,
            service_token=token,
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            primary_school_id=primary_school_id,
            allowed_origins=_as_origins(os.getenv("ALLOWED_ORIGINS")),
            docs_enabled=_as_bool(
                os.getenv("DOCS_ENABLED"), environment != "production"
            ),
            rmp_api_url=os.getenv(
                "RMP_API_URL", "https://www.ratemyprofessors.com/graphql"
            ),
            rmp_timeout_seconds=float(os.getenv("RMP_TIMEOUT_SECONDS", "8")),
            request_limit_per_minute=int(
                os.getenv("REQUEST_LIMIT_PER_MINUTE", "120")
            ),
            max_upstream_concurrency=int(
                os.getenv("MAX_UPSTREAM_CONCURRENCY", "5")
            ),
            school_cache_seconds=int(os.getenv("SCHOOL_CACHE_SECONDS", "86400")),
            professor_search_cache_seconds=int(
                os.getenv("PROFESSOR_SEARCH_CACHE_SECONDS", "900")
            ),
            professor_profile_cache_seconds=int(
                os.getenv("PROFESSOR_PROFILE_CACHE_SECONDS", "3600")
            ),
            empty_cache_seconds=int(os.getenv("EMPTY_CACHE_SECONDS", "60")),
            stale_cache_seconds=int(os.getenv("STALE_CACHE_SECONDS", "86400")),
        )
