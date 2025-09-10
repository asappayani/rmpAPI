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

def _professor_to_out(node: dict) -> ProfessorOut:
    return ProfessorOut(
        firstName = node.get("firstName"),
        lastName = node.get("lastName"),
        department = node.get("department"),
        avgRating = node.get("avgRating"),
        avgDifficulty = node.get("avgDifficulty"),
        wouldTakeAgainPercent = node.get("wouldTakeAgainPercent"),
        numRatings = node.get("numRatings"),
        link = f"https://www.ratemyprofessors.com/professor/{node.get('legacyId')}"
    )

@router.get("/search", response_model=List[ProfessorOut])
async def search_professors(
    name: str = Query(..., description="The name of the professor to search for"),
    school_id: str = Query(..., description="The id of the school to search for"),
) -> List[ProfessorOut]:
    """Get the list of professors and return them in a list."""
    try:
        response = get_professors_data(name, school_id)
        
        if not response:
            raise HTTPException(status_code=404, detail="No professors found")
        
        professors = []
        for edge in response:
            node = edge["node"]
            professors.append(_professor_to_out(node))
            
        return professors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/search/first", response_model=ProfessorOut)
async def get_first_search(
    name: str = Query(..., description="The name of the professor to search for"),
    school_id: str = Query(..., description="The id of the school to search for"),
):
    """Get the first professor from the list of professors and returns it."""
    try:
        response = get_professors_data(name, school_id)
        
        if not response:
            raise HTTPException(status_code=404, detail="No professors found")
        
        professors = []
        for edge in response:
            node = edge["node"]
            professors.append(ProfessorOut(
                firstName = node.get("firstName"),
                lastName = node.get("lastName"),
                department = node.get("department"),
                avgRating = node.get("avgRating"),
                avgDifficulty = node.get("avgDifficulty"),
                wouldTakeAgainPercent = node.get("wouldTakeAgainPercent"),
                numRatings = node.get("numRatings"),
                link = f"https://www.ratemyprofessors.com/professor/{node.get('legacyId')}"
            ))
            
        return professors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/filtered", response_model=List[ProfessorOut])
async def filtered_search():
    """Get the list of professors and return them in a list."""
    pass





