from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str
    count: int = Field(ge=0)
    cached: bool = False
    stale: bool = False


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    request_id: str
