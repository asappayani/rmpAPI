from __future__ import annotations


class ServiceError(Exception):
    status_code = 500
    title = "Internal Server Error"
    type = "about:blank"

    def __init__(self, detail: str, *, headers: dict[str, str] | None = None):
        super().__init__(detail)
        self.detail = detail
        self.headers = headers or {}


class AuthenticationError(ServiceError):
    status_code = 401
    title = "Unauthorized"
    type = "https://rmp-api.local/problems/unauthorized"


class NotFoundError(ServiceError):
    status_code = 404
    title = "Not Found"
    type = "https://rmp-api.local/problems/not-found"


class InvalidRequestError(ServiceError):
    status_code = 422
    title = "Validation Error"
    type = "https://rmp-api.local/problems/validation"


class RateLimitError(ServiceError):
    status_code = 429
    title = "Too Many Requests"
    type = "https://rmp-api.local/problems/rate-limit"


class DependencyUnavailableError(ServiceError):
    status_code = 503
    title = "Service Unavailable"
    type = "https://rmp-api.local/problems/dependency-unavailable"


class UpstreamUnavailableError(ServiceError):
    status_code = 503
    title = "Upstream Service Unavailable"
    type = "https://rmp-api.local/problems/upstream-unavailable"


class UpstreamResponseError(ServiceError):
    status_code = 502
    title = "Invalid Upstream Response"
    type = "https://rmp-api.local/problems/upstream-response"
