from typing import List, Optional

from app import crud, constants
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

class SearchRequest(BaseModel):
    keyword: str
    search_type: str

class SearchResponse(BaseModel):
    recommendations: List[Movie]

@router.post("/search", response_model=GenreRecommendationResponse)
def recommend_movies_by_genre(
    *,
    session: SessionDep,
    request_body: SearchResponse,
):
    if request_body.search_type not in constants.SEARCH_TYPE:
        raise HTTPException(status_code=400, detail="Invalid search type. must in {}".format(constants.SEARCH_TYPE))

    recommended_movies = crud.recommend_by_keywords(
        session=session,
        keywords=request_body.keyword,
        search_type=request_body.search_type,
    )

    return SearchResponse(recommendations=recommended_movies)

class ContentRecommendationRequest(BaseModel):
    movies_id: int

class ContentRecommendationResponse(BaseModel):
    recommendations: List[Movie]

@router.post("/content-base", response_model=GenreRecommendationResponse)
def recommend_movies_by_genre(
    *,
    session: SessionDep,
    request_body: ContentRecommendationRequest,
):

    recommended_movies = crud.recommend_by_keywords(
        session=session,
        keywords=request_body.keyword,
        search_type=request_body.search_type,
    )

    return ContentRecommendationResponse(recommendations=recommended_movies)

