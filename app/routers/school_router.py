from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import get_rmp_service, require_service_token
from app.errors import NotFoundError
from app.schemas.common_schema import ApiResponse, ResponseMeta
from app.schemas.school_schema import SchoolOut
from app.services.rmp_service import RmpService

router = APIRouter(
    prefix="/schools",
    tags=["schools"],
    dependencies=[Depends(require_service_token)],
)


@router.get("/search", response_model=ApiResponse[list[SchoolOut]])
async def search_schools(
    request: Request,
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
    service: RmpService = Depends(get_rmp_service),
) -> ApiResponse[list[SchoolOut]]:
    result = await service.search_schools(q, limit)
    request.state.cached = result.cached
    request.state.stale = result.stale
    schools = [SchoolOut.model_validate(item) for item in result.value or []]
    return ApiResponse(
        data=schools,
        meta=ResponseMeta(
            request_id=request.state.request_id,
            count=len(schools),
            cached=result.cached,
            stale=result.stale,
        ),
    )


@router.get("/{school_id}", response_model=ApiResponse[SchoolOut])
async def get_school(
    school_id: str,
    request: Request,
    service: RmpService = Depends(get_rmp_service),
) -> ApiResponse[SchoolOut]:
    result = await service.get_school(school_id)
    request.state.cached = result.cached
    request.state.stale = result.stale
    if result.value is None:
        raise NotFoundError("School not found")
    return ApiResponse(
        data=SchoolOut.model_validate(result.value),
        meta=ResponseMeta(
            request_id=request.state.request_id,
            count=1,
            cached=result.cached,
            stale=result.stale,
        ),
    )
