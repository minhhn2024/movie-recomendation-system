from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.api.deps import SessionDep
from app.models import StgGenre
from pydantic import BaseModel


router = APIRouter(prefix="/genres", tags=["genres"])

@router.get("/", response_model=List[str])
def get_all_genres(session: SessionDep) -> List[str]:
    """
    Retrieve all unique genres.
    """
    statement = select(StgGenre.genre).distinct()
    genres = session.exec(statement).all()

    return genres
