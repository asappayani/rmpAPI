# RMP Internal API

An internal FastAPI service that provides normalized Rate My Professors data to
another backend. The intended consumer will combine these records with Texas A&M
GPA distributions; matching instructors and ranking professors are deliberately
outside this service.

> Rate My Professors does not publish a supported API for this integration. Do
> not deploy a public product until you have permission to access and republish
> its data, or have replaced the provider with an authorized source.

## What it provides

- Asynchronous school and professor lookups
- Stable numeric professor IDs and normalized response fields
- Redis caching, stale fallback, request limiting, and refresh locks
- One shared bearer token for backend-to-backend authentication
- Consistent response envelopes and problem-detail errors
- Liveness, readiness, request IDs, and structured request logs

The service is school-agnostic. Set `PRIMARY_SCHOOL_ID` to the correct Texas A&M
campus returned by school search to make it the default for professor searches.

## Run with Docker

1. Copy `.env.example` to `.env` and replace `RMP_SERVICE_TOKEN`.
2. Start the API and Redis:

   ```bash
   docker compose up --build
   ```

3. Find the desired Texas A&M campus ID:

   ```bash
   curl -H "Authorization: Bearer $RMP_SERVICE_TOKEN" \
     "http://localhost:8000/api/v1/schools/search?q=Texas%20A%26M"
   ```

4. Put the returned school ID in `PRIMARY_SCHOOL_ID` and restart the API.

Swagger documentation is available at <http://localhost:8000/docs> in the
development configuration.

## Endpoints

All data endpoints require `Authorization: Bearer <service-token>`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/schools/search?q=...&limit=20` | Search for schools |
| GET | `/api/v1/schools/{school_id}` | Retrieve a school |
| GET | `/api/v1/professors/search?q=...&school_id=...&limit=20` | Search professors |
| GET | `/api/v1/professors/{professor_id}` | Retrieve a professor by numeric RMP ID |
| GET | `/health/live` | Process liveness |
| GET | `/health/ready` | Redis and initialization readiness |

`school_id` may be omitted from professor search when `PRIMARY_SCHOOL_ID` is
configured. Empty searches return HTTP 200 with an empty `data` array.

Successful responses use this shape:

```json
{
  "data": [],
  "meta": {
    "request_id": "8d9f...",
    "count": 0,
    "cached": false,
    "stale": false
  }
}
```

Temporary upstream failures may return cached data with `stale: true`. Invalid
input uses HTTP 422, authentication failures use 401, malformed upstream data
uses 502, and unavailable dependencies use 503.

## Local Python development

This project uses Python 3.11 and `uv`:

```bash
uv sync --dev
docker compose up -d redis
uv run uvicorn app.main:app --reload
```

Run checks with:

```bash
uv run ruff check .
uv run pytest
```

Never commit `.env`. In production, use a randomly generated service token of at
least 32 characters, disable docs unless needed, terminate HTTPS at the ingress,
and keep the API reachable only by the consuming backend when possible.
