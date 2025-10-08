from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.rmp_scraper import get_schools_data
from app.schemas.school_schema import SchoolOut

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

