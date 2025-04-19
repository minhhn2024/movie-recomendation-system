from typing import List, Optional

from app import crud
from app.models import Movie

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import SessionDep, CurrentUser  # Import các dependency cần thiết


router = APIRouter(prefix="/recommender", tags=["recommender"])

class GenreRecommendationRequest(BaseModel):
    genres: List[str]
    limit: Optional[int] = 10

class GenreRecommendationResponse(BaseModel):
    recommendations: List[Movie]

@router.post("/", response_model=GenreRecommendationResponse)
def recommend_movies_by_genres(
    *,
    session: SessionDep,
    request_body: GenreRecommendationRequest,
):
    """
    Gợi ý các bộ phim dựa trên danh sách thể loại được cung cấp trong request body.
    """
    if not request_body.genres:
        raise HTTPException(status_code=400, detail="Please provide at least one genre.")

    recommended_movies = crud.recommend_by_genres(
        session=session, genres=request_body.genres, limit=request_body.limit
    )

    return GenreRecommendationResponse(recommendations=recommended_movies)


