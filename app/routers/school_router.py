from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional

from app.services.rmp_scraper import get_schools_data
from app.schemas.school_schema import SchoolOut
from app.main import limiter

router = APIRouter(
    prefix="/schools",
    tags=["schools"],
    responses={404: {"description": "School not found"}},
)

def _school_to_out(node: dict) -> SchoolOut:
    return SchoolOut(
        id=node.get("id"),
        name=node.get("name"),
        city=node.get("city"),
        state=node.get("state"),
    )

@router.get("/search", response_model=List[SchoolOut])
@limiter.limit("10/minute")
async def search_schools(
    request: Request,
    query: str = Query(..., description="The query to search for schools"),
) -> List[SchoolOut]:
    """Get the list of schools and return them in a list."""
    try:
        response = get_schools_data(query) # get the schools data
        
        if not response:
            raise HTTPException(status_code=404, detail="No schools found")
        
        schools = []
        for edge in response:
            node = edge["node"]
            schools.append(_school_to_out(node))
            
        return schools
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/search/first", response_model=SchoolOut)
@limiter.limit("10/minute")
async def get_first_search(
    request: Request,
    query: str = Query(..., description="The query to search for schools"),
) -> SchoolOut:
    """Get the first school from the list of schools and return it."""
    try:
        response = get_schools_data(query) # get the schools data
        
        if not response:
            raise HTTPException(status_code=404, detail="No schools found")
        
        first_node = response[0]["node"] # get the first node
        return _school_to_out(first_node) 
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        