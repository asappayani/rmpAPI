"""
This file contains the professor schemas that will be returned by the API.
"""

from pydantic import BaseModel
from typing import Optional

class ProfessorOut(BaseModel):
    firstName: str
    lastName: str
    department: Optional[str] = None
    avgRating: Optional[float] = None
    avgDifficulty: Optional[float] = None
    wouldTakeAgainPercent: Optional[int] = None
    numRatings: Optional[int] = None
    link: str

