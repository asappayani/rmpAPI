from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.config import Settings
from app.errors import ServiceError
from app.routers import professor_router, school_router
from app.schemas.common_schema import ProblemDetail
from app.services.cache import RedisRateLimiter, RedisStore
from app.services.rmp_client import RmpGraphQLClient
from app.services.rmp_service import RmpService

logger = logging.getLogger("rmp_api")
logging.basicConfig(level=logging.INFO, format="%(message)s")


def _problem(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    problem_type: str = "about:blank",
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ProblemDetail(
        type=problem_type,
        title=title,
        status=status,
        detail=detail,
        request_id=getattr(request.state, "request_id", "unknown"),
    )
    return JSONResponse(status_code=status, content=body.model_dump(), headers=headers)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        cache = RedisStore(redis, stale_seconds=settings.stale_cache_seconds)
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.rmp_timeout_seconds, connect=2.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={
                "Authorization": "Basic dGVzdDp0ZXN0",
                "Content-Type": "application/json",
                "Origin": "https://www.ratemyprofessors.com",
                "Referer": "https://www.ratemyprofessors.com/",
                "User-Agent": "rmp-api/0.2",
            },
        )
        provider = RmpGraphQLClient(
            http_client,
            settings.rmp_api_url,
            settings.max_upstream_concurrency,
        )
        app.state.settings = settings
        app.state.redis = redis
        app.state.cache = cache
        app.state.rate_limiter = RedisRateLimiter(
            redis, settings.request_limit_per_minute
        )
        app.state.rmp_service = RmpService(provider, cache, settings)
        app.state.initialized = True
        yield
        app.state.initialized = False
        await http_client.aclose()
        await redis.aclose()

    app = FastAPI(
        title="RMP Internal API",
        description="Internal Rate My Professors data service",
        version="0.2.0",
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.initialized = False

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id[:128]
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        logger.info(
            json.dumps(
                {
                    "event": "request_complete",
                    "request_id": request.state.request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "cached": getattr(request.state, "cached", None),
                    "stale": getattr(request.state, "stale", None),
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            )
        )
        return response

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        return _problem(
            request,
            status=exc.status_code,
            title=exc.title,
            detail=exc.detail,
            problem_type=exc.type,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return _problem(
            request,
            status=422,
            title="Validation Error",
            detail="Request parameters are invalid",
            problem_type="https://rmp-api.local/problems/validation",
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("unhandled request error", exc_info=exc)
        return _problem(
            request,
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred",
        )

    app.include_router(professor_router.router, prefix="/api/v1")
    app.include_router(school_router.router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"name": "RMP Internal API", "version": "0.2.0"}

    @app.get("/health/live")
    async def liveness():
        return {"status": "healthy"}

    @app.get("/health/ready")
    async def readiness(request: Request):
        initialized = bool(request.app.state.initialized)
        redis_ready = initialized and await request.app.state.cache.ping()
        if not initialized or not redis_ready:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "redis": redis_ready},
            )
        return {"status": "ready", "redis": True}

    return app


app = create_app()
