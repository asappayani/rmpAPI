"""
This file contains the school schemas that will be returned by the API.
"""

from pydantic import BaseModel
from typing import Optional

class SchoolOut(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None