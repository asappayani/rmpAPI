from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import get_rmp_service, require_service_token
from app.errors import InvalidRequestError, NotFoundError
from app.schemas.common_schema import ApiResponse, ResponseMeta
from app.schemas.professor_schema import ProfessorOut
from app.services.rmp_service import RmpService

router = APIRouter(
    prefix="/professors",
    tags=["professors"],
    dependencies=[Depends(require_service_token)],
)


@router.get("/search", response_model=ApiResponse[list[ProfessorOut]])
async def search_professors(
    request: Request,
    q: str = Query(min_length=1, max_length=100),
    school_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    service: RmpService = Depends(get_rmp_service),
) -> ApiResponse[list[ProfessorOut]]:
    resolved_school_id = school_id or request.app.state.settings.primary_school_id
    if not resolved_school_id:
        raise InvalidRequestError(
            "school_id is required when PRIMARY_SCHOOL_ID is not configured"
        )
    result = await service.search_professors(q, resolved_school_id, limit)
    request.state.cached = result.cached
    request.state.stale = result.stale
    professors = [ProfessorOut.model_validate(item) for item in result.value or []]
    return ApiResponse(
        data=professors,
        meta=ResponseMeta(
            request_id=request.state.request_id,
            count=len(professors),
            cached=result.cached,
            stale=result.stale,
        ),
    )


@router.get("/{professor_id}", response_model=ApiResponse[ProfessorOut])
async def get_professor(
    professor_id: str,
    request: Request,
    service: RmpService = Depends(get_rmp_service),
) -> ApiResponse[ProfessorOut]:
    if not professor_id.isdigit():
        raise InvalidRequestError("professor_id must be the numeric RMP professor ID")
    result = await service.get_professor(professor_id)
    request.state.cached = result.cached
    request.state.stale = result.stale
    if result.value is None:
        raise NotFoundError("Professor not found")
    return ApiResponse(
        data=ProfessorOut.model_validate(result.value),
        meta=ResponseMeta(
            request_id=request.state.request_id,
            count=1,
            cached=result.cached,
            stale=result.stale,
        ),
    )
