from ast import Pass
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.rmp_scraper import get_professors_data
from app.schemas.professor_schema import ProfessorOut

# to create link  print(f"  link        : https://www.ratemyprofessors.com/professor/{legacy_id}")

router = APIRouter(
    prefix="/professors",
    tags=["professors"],
    responses={404: {"description": "Professor not found"}},
)

@router.get("/search", response_model=List[ProfessorOut])
async def search_professors():
    """Get the list of professors and return them in a list."""
    pass

@router.get("/get_first_search", response_model=ProfessorOut)
async def get_first_search():
    """Get the first professor from the list of professors and returns it."""
    pass

@router.get("/search/filtered", response_model=List[ProfessorOut])
async def filtered_search():
    """Get the list of professors and return them in a list."""
    pass





