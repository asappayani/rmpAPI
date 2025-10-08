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
        response = get_professors_data(name, school_id) # get the professors data
        
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
) -> ProfessorOut:
    """Get the first professor from the list of professors and returns it."""
    try:
        response = get_professors_data(name, school_id) # get the professors data
        
        if not response:
            raise HTTPException(status_code=404, detail="No professors found") # if no professors found, raise an error
        
        first_node = response[0]["node"] # get the first node
        return _professor_to_out(first_node) 
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/filtered", response_model=List[ProfessorOut])
async def filtered_search(
    name: str = Query(..., description="The name of the professor to search for"),
    school_id: str = Query(..., description="The id of the school to search for"),
    min_rating: Optional[float] = Query(None, description="The minimum rating of the professor"),
    max_rating: Optional[float] = Query(None, description="The maximum rating of the professor"),
    min_difficulty: Optional[float] = Query(None, description="The minimum difficulty of the professor"),
    max_difficulty: Optional[float] = Query(None, description="The maximum difficulty of the professor"),
    min_would_take_again: Optional[float] = Query(None, description="The minimum would take again percentage of the professor"),
    max_would_take_again: Optional[float] = Query(None, description="The maximum would take again percentage of the professor"),
    min_num_ratings: Optional[int] = Query(None, description="The minimum number of ratings of the professor"),
    max_num_ratings: Optional[int] = Query(None, description="The maximum number of ratings of the professor"),
):
    """Get the list of professors and return them in a list."""
    try:
        response = get_professors_data(name, school_id) # get the professors data
        
        if not response:
            raise HTTPException(status_code=404, detail="No professors found") # if no professors found, raise an error
        
        professors = []
        for edge in response:
            node = edge["node"]
            
            # get values with defaults for None
            avg_rating = node.get("avgRating")
            avg_difficulty = node.get("avgDifficulty") 
            would_take_again = node.get("wouldTakeAgainPercent")
            num_ratings = node.get("numRatings")

            # apply filters (skip if value is None)
            if min_rating and (avg_rating is None or avg_rating < min_rating):
                continue
            if max_rating and (avg_rating is None or avg_rating > max_rating):
                continue
            if min_difficulty and (avg_difficulty is None or avg_difficulty < min_difficulty):
                continue
            if max_difficulty and (avg_difficulty is None or avg_difficulty > max_difficulty):
                continue
            if min_would_take_again and (would_take_again is None or would_take_again < min_would_take_again):
                continue
            if max_would_take_again and (would_take_again is None or would_take_again > max_would_take_again):
                continue
            if min_num_ratings and (num_ratings is None or num_ratings < min_num_ratings):
                continue
            if max_num_ratings and (num_ratings is None or num_ratings > max_num_ratings):
                continue
            
            professors.append(_professor_to_out(node)) # add the professor to the list

        return professors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






