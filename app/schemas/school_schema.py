from pydantic import BaseModel


class SchoolOut(BaseModel):
    id: str
    name: str
    city: str | None = None
    state: str | None = None
