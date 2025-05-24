from datetime import date
from http.client import HTTPException
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter
from sqlmodel import select, func
from app.api.deps import SessionDep
from app.models import StgMovieMetadata, StgGenre, StgCast, MoviePublic, CastPublic, MoviesPublic, \
    MoviePublicWithRating, StgRating

router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("/", response_model=MoviesPublic)
def get_movies(
        session: SessionDep, skip: int = 0, limit: int = 100
) -> MoviesPublic:
    """
    Retrieve movies with pagination, including genres, cast, and keywords.
    """
    # Count total movies
    count_statement = select(func.count()).select_from(StgMovieMetadata)
    count = session.exec(count_statement).one()

    # Get movies with pagination
    statement = select(StgMovieMetadata).offset(skip).limit(limit)
    movies = session.exec(statement).all()

    # Fetch related data for each movie
    movie_ids = [movie.id for movie in movies]

    # Get genres
    genre_statement = select(StgGenre).where(StgGenre.movie_id.in_(movie_ids))
    genres = session.exec(genre_statement).all()
    genre_map = {}
    for genre in genres:
        if genre.movie_id not in genre_map:
            genre_map[genre.movie_id] = []
        genre_map[genre.movie_id].append(genre.genre)

    # Get cast
    cast_statement = select(StgCast).where(StgCast.movie_id.in_(movie_ids))
    cast = session.exec(cast_statement).all()
    cast_map = {}
    for c in cast:
        if c.movie_id not in cast_map:
            cast_map[c.movie_id] = []
        cast_map[c.movie_id].append(CastPublic(name=c.name, role=c.role))

    # Build response
    movie_data = []
    for movie in movies:
        # Split keywords string into list, handle None or empty string
        keyword_list = (
            [kw.strip() for kw in movie.keywords.split(",") if kw.strip()]
            if movie.keywords
            else []
        )
        movie_data.append(
            MoviePublic(
                id=movie.id,
                title=movie.title,
                original_title=movie.original_title,
                belongs_to_collection=movie.belongs_to_collection,
                release_date=movie.release_date,
                overview=movie.overview,
                tagline=movie.tagline,
                homepage=movie.homepage,
                poster_path=movie.poster_path,
                vote_average=movie.vote_average,
                vote_count=movie.vote_count,
                imdb_id=movie.imdb_id,
                tmdb_id=movie.tmdb_id,
                genres=genre_map.get(movie.id, []),
                cast=cast_map.get(movie.id, []),
                keywords=keyword_list
            )
        )

    return MoviesPublic(data=movie_data, count=count)


@router.get("/{id}", response_model=MoviePublic)
def get_movie_by_id(session: SessionDep, id: int) -> MoviePublic:
    """
    Retrieve a movie by ID from local database, including genres, cast, and keywords.
    """
    # Get movie by ID
    movie = session.get(StgMovieMetadata, id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Get genres
    genre_statement = select(StgGenre).where(StgGenre.movie_id == id)
    genres = session.exec(genre_statement).all()
    genres_list = [genre.genre for genre in genres if genre.genre]

    # Get cast
    cast_statement = select(StgCast).where(StgCast.movie_id == id)
    cast = session.exec(cast_statement).all()
    cast_list = [CastPublic(name=c.name, role=c.role) for c in cast if c.name]

    # Process keywords
    keyword_list = (
        [kw.strip() for kw in movie.keywords.split(",") if kw.strip()]
        if movie.keywords
        else []
    )


    return MoviePublic(
        id=movie.id,
        title=movie.title,
        original_title=movie.original_title,
        belongs_to_collection=movie.belongs_to_collection,
        release_date=movie.release_date,
        overview=movie.overview,
        tagline=movie.tagline,
        homepage=movie.homepage,
        poster_path=movie.poster_path,
        vote_average=movie.vote_average,
        vote_count=movie.vote_count,
        imdb_id=movie.imdb_id,
        tmdb_id=movie.tmdb_id,
        genres=genres_list,
        cast=cast_list,
        keywords=keyword_list
    )

@router.post("/get-by-ids", response_model=List[MoviePublic])
def get_movies_by_ids(session: SessionDep, ids: List[int]) -> List[MoviePublic]:
    """
    Retrieve multiple movies by IDs from local database, including genres, cast, and keywords.
    Expects a JSON body with an array of IDs (e.g., [1, 2, 3]).
    Returns results in the exact order of input IDs, skipping non-existent IDs.
    """
    if not ids:
        raise HTTPException(status_code=400, detail="No valid IDs provided")

    # Kiểm tra ID hợp lệ (số nguyên dương)
    if not all(isinstance(id, int) and id > 0 for id in ids):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Truy vấn phim theo danh sách ID
    movie_statement = select(StgMovieMetadata).where(StgMovieMetadata.id.in_(ids))
    movies = session.exec(movie_statement).all()

    # Tạo từ điển để lưu trữ phim theo ID
    movies_dict = {movie.id: movie for movie in movies}

    # Truy vấn tất cả genres cho các movie_id
    genre_statement = select(StgGenre).where(StgGenre.movie_id.in_(ids))
    genres = session.exec(genre_statement).all()
    genres_dict = {}
    for genre in genres:
        if genre.movie_id not in genres_dict:
            genres_dict[genre.movie_id] = []
        if genre.genre:
            genres_dict[genre.movie_id].append(genre.genre)

    # Truy vấn tất cả cast cho các movie_id
    cast_statement = select(StgCast).where(StgCast.movie_id.in_(ids))
    cast = session.exec(cast_statement).all()
    cast_dict = {}
    for c in cast:
        if c.movie_id not in cast_dict:
            cast_dict[c.movie_id] = []
        if c.name:
            cast_dict[c.movie_id].append(CastPublic(name=c.name, role=c.role))

    result = []
    missing_ids = []
    for movie_id in ids:
        if movie_id in movies_dict:
            movie = movies_dict[movie_id]
            keyword_list = (
                [kw.strip() for kw in movie.keywords.split(",") if kw.strip()]
                if movie.keywords
                else []
            )

            result.append(
                MoviePublic(
                    id=movie.id,
                    title=movie.title,
                    original_title=movie.original_title,
                    belongs_to_collection=movie.belongs_to_collection,
                    release_date=movie.release_date,
                    overview=movie.overview,
                    tagline=movie.tagline,
                    homepage=movie.homepage,
                    poster_path=movie.poster_path,
                    vote_average=movie.vote_average,
                    vote_count=movie.vote_count,
                    imdb_id=movie.imdb_id,
                    tmdb_id=movie.tmdb_id,
                    genres=genres_dict.get(movie.id, []),
                    cast=cast_dict.get(movie.id, []),
                    keywords=keyword_list
                )
            )
        else:
            missing_ids.append(movie_id)

    # Ghi log các ID không tìm thấy (tùy chọn)
    if missing_ids:
        print(f"Warning: Movies with IDs {missing_ids} not found")

    if not result:
        raise HTTPException(status_code=404, detail="No movies found for the provided IDs")

    return result

class UserRatingsRequest(BaseModel):
    user_id: int
    limit: Optional[int] = 20  # Giới hạn số lượng phim trả về (mặc định 50)

class UserRatingsResponse(BaseModel):
    rated_movies: List[MoviePublicWithRating]

@router.post("/user/ratings", response_model=UserRatingsResponse)
def get_user_rated_movies(
    *,
    session: SessionDep,
    request: UserRatingsRequest
) -> UserRatingsResponse:

    user_id = request.user_id
    limit = request.limit

    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    # Truy vấn danh sách movie_id và rating từ bảng Ratings
    rating_statement = select(StgRating.movie_id, StgRating.rating).where(StgRating.user_id == user_id).limit(limit)
    ratings = session.exec(rating_statement).all()

    if not ratings:
        raise HTTPException(status_code=404, detail=f"No ratings found for user ID {user_id}")

    movie_ids = [rating.movie_id for rating in ratings]
    ratings_dict = {rating.movie_id: rating.rating for rating in ratings}

    movies = get_movies_by_ids(session, movie_ids)

    rated_movies = []
    for movie_id in movie_ids:
        for movie in movies:
            if movie.id == movie_id:
                rated_movies.append(
                    MoviePublicWithRating(
                        **movie.model_dump(),
                        rating=ratings_dict.get(movie_id)
                    )
                )
                break

    return UserRatingsResponse(rated_movies=rated_movies)