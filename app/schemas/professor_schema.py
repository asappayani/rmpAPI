from datetime import datetime

from pydantic import BaseModel


class ProfessorOut(BaseModel):
    id: str
    source_id: str | None = None
    first_name: str
    last_name: str
    display_name: str
    department: str | None = None
    school_id: str | None = None
    school_name: str | None = None
    average_rating: float | None = None
    average_difficulty: float | None = None
    would_take_again_percent: float | None = None
    number_of_ratings: int | None = None
    profile_url: str
    retrieved_at: datetime

