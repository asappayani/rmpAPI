from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import AuthenticationError
from app.services.rmp_service import RmpService

bearer_scheme = HTTPBearer(auto_error=False)


async def require_service_token(
    request: Request,
    response: Response,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> None:
    expected_token = request.app.state.settings.service_token
    if (
        credentials is None
        or credentials.scheme.casefold() != "bearer"
        or not secrets.compare_digest(credentials.credentials, expected_token)
    ):
        raise AuthenticationError(
            "A valid bearer service token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    limit, remaining = await request.app.state.rate_limiter.check("backend")
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)


def get_rmp_service(request: Request) -> RmpService:
    return request.app.state.rmp_service
