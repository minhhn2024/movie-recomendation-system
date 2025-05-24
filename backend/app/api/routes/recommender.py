from typing import List, Optional, Annotated

from app import constants
from app.api.routes.movies import get_movies_by_ids
from app.models import MoviePublic, CastPublic, MoviePublicWr, StgMovieMetadata, StgRating
from sqlalchemy import text
from sqlmodel import select
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import SessionDep, EmbeddingModelDep, FaissIndexManager, get_faiss_manager, MFModel, get_mf_model
from app.core.ml_compute import get_embedding, multi_search_faiss_index, search_by_faiss_index


router = APIRouter(prefix="/recommender", tags=["recommender"])

class GenreRecommendationRequest(BaseModel):
    genres: List[str]
    limit: Optional[int] = 20

    @classmethod
    def validate_genres(cls, genres: List[str]) -> List[str]:
        if not genres:
            raise ValueError("Genres list cannot be empty")
        return [g.strip() for g in genres if g.strip()]

    @classmethod
    def validate_limit(cls, limit: int) -> int:
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        return limit

class MovieRecommendationResponse(BaseModel):
    recommendations: List[MoviePublicWr]

@router.post("/by-genres", response_model=MovieRecommendationResponse)
def recommend_movies_by_genres(
    *,
    session: SessionDep,
    request_body: GenreRecommendationRequest,
) -> MovieRecommendationResponse:
    """
    Retrieve top `limit` movies per genre, sorted by wr_80th, with full MoviePublic details.
    """
    try:
        # Step 1: Get top movies per genre
        query = """
        WITH RankedMovies AS (
            SELECT 
                h.genre,
                h.movie_id,
                h.title,
                h.vote_count,
                m.original_title,
                m.belongs_to_collection,
                m.release_date,
                m.overview,
                m.tagline,
                m.homepage,
                m.poster_path,
                m.vote_average,
                m.imdb_id,
                m.tmdb_id,
                m.keywords,
                h.wr_80th,
                ROW_NUMBER() OVER (
                    PARTITION BY h.genre
                    ORDER BY h.wr_80th DESC, h.movie_id
                ) AS row_num
            FROM mv_high_quality_movies h
            JOIN stg_movie_metadata m ON h.movie_id = m.id
            WHERE h.genre = ANY(:genres)
            AND h.wr_80th IS NOT NULL
        )
        SELECT 
            movie_id AS id,
            title,
            original_title,
            belongs_to_collection,
            release_date,
            overview,
            tagline,
            homepage,
            poster_path,
            vote_average,
            vote_count,
            imdb_id,
            tmdb_id,
            keywords,
            wr_80th
        FROM RankedMovies
        WHERE row_num <= :limit
        ORDER BY wr_80th DESC, movie_id
        LIMIT :limit;
        """
        result = session.execute(
            text(query),
            {"genres": request_body.genres, "limit": request_body.limit}
        )
        movie_data = [
            {
                "id": row.id,
                "title": row.title,
                "original_title": row.original_title,
                "belongs_to_collection": row.belongs_to_collection,
                "release_date": row.release_date,
                "overview": row.overview,
                "tagline": row.tagline,
                "homepage": row.homepage,
                "poster_path": row.poster_path,
                "vote_average": row.vote_average,
                "vote_count": row.vote_count,
                "imdb_id": row.imdb_id,
                "tmdb_id": row.tmdb_id,
                "keywords": row.keywords,
                "wr": row.wr_80th,
            }
            for row in result
        ]

        if not movie_data:
            raise HTTPException(status_code=404, detail="No movies found for the specified genres")

        movie_ids = [movie["id"] for movie in movie_data]
        genre_query = """
        SELECT movie_id, genre
        FROM stg_genre
        WHERE movie_id = ANY(:movie_ids) AND genre IS NOT NULL AND genre != '';
        """
        genre_result = session.execute(
            text(genre_query),
            {"movie_ids": movie_ids}
        )
        genre_dict = {}
        for row in genre_result:
            if row.movie_id not in genre_dict:
                genre_dict[row.movie_id] = []
            genre_dict[row.movie_id].append(row.genre)

        cast_query = """
        SELECT movie_id, name, role
        FROM stg_cast
        WHERE movie_id = ANY(:movie_ids) AND name IS NOT NULL;
        """
        cast_result = session.execute(
            text(cast_query),
            {"movie_ids": movie_ids}  # Pass movie_ids as a Python list
        )
        cast_dict = {}
        for row in cast_result:
            if row.movie_id not in cast_dict:
                cast_dict[row.movie_id] = []
            cast_dict[row.movie_id].append({"name": row.name, "role": row.role})

        recommendations = []
        for movie in movie_data:
            keyword_list = (
                [kw.strip() for kw in movie["keywords"].split(",") if kw.strip()]
                if movie["keywords"]
                else []
            )
            genres_list = genre_dict.get(movie["id"], [])
            cast_list = [
                CastPublic(name=c["name"], role=c["role"])
                for c in cast_dict.get(movie["id"], [])
            ]
            recommendations.append(
                MoviePublicWr(
                    id=movie["id"],
                    title=movie["title"],
                    original_title=movie["original_title"],
                    belongs_to_collection=movie["belongs_to_collection"],
                    release_date=movie["release_date"],
                    overview=movie["overview"],
                    tagline=movie["tagline"],
                    homepage=movie["homepage"],
                    poster_path=movie["poster_path"],
                    vote_average=movie["vote_average"],
                    vote_count=movie["vote_count"],
                    imdb_id=movie["imdb_id"],
                    tmdb_id=movie["tmdb_id"],
                    genres=genres_list,
                    cast=cast_list,
                    keywords=keyword_list,
                    wr=movie["wr"],
                )
            )

        return MovieRecommendationResponse(recommendations=recommendations)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20


@router.post("/search", response_model=MovieRecommendationResponse)
def search_movies(
    *,
    session: SessionDep,
    embeddingModel: EmbeddingModelDep,
    faissManager: Annotated[FaissIndexManager, Depends(get_faiss_manager)],
    request: SearchRequest
):
    # Validate input
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
    if len(query) > 500:
        raise HTTPException(status_code=400, detail="Query must not exceed 500 characters")

    top_k = request.limit
    if top_k < 1 or top_k > 50:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 50")

    # Tạo embedding cho query
    query_embedding = get_embedding(query, embeddingModel, constants.EmbeddingModelConstants.VECTOR_EMBEDDING_DIM)

    result_raw = multi_search_faiss_index(query_embedding, faissManager.get_indices(), faissManager.get_id_mapping(), top_k)
    movie_scores = dict()
    for r in result_raw:
        similarity = r["distance"]  # cosine similarity
        score = similarity
        movie_id = r["movieId"]
        movie_scores[movie_id] = max(movie_scores.get(movie_id, 0), score)

    sorted_movies = sorted(
        [{"movieId": movie_id, "score": score} for movie_id, score in movie_scores.items()],
        key=lambda x: x["score"],
        reverse=True
    )

    sorted_movies = sorted_movies[:top_k]

    movie_public = get_movies_by_ids(session, [m["movieId"] for m in sorted_movies])

    return MovieRecommendationResponse(recommendations=[
        MoviePublicWr(**movie.model_dump(), wr=sorted_movies[i]["score"])
        for i, movie in enumerate(movie_public)
    ])

class ContentBaseRequest(BaseModel):
    movieId: int
    limit: Optional[int] = 20


@router.post("/content-base", response_model=MovieRecommendationResponse)
def content_based_recommendation(
    *,
    session: SessionDep,
    faissManager: Annotated[FaissIndexManager, Depends(get_faiss_manager)],
    request: ContentBaseRequest
) -> MovieRecommendationResponse:
    movie_id = request.movieId
    top_k = request.limit

    if movie_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid movie ID")
    if top_k < 1 or top_k > 50:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 50")

    # Lấy thông tin phim từ cơ sở dữ liệu
    movie_statement = select(StgMovieMetadata).where(StgMovieMetadata.id == movie_id)
    movie = session.exec(movie_statement).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")

    # Lấy embedding
    embedding_dict = faissManager.get_embedding_vector(movie_id)

    result_raw = search_by_faiss_index(embedding_dict, faissManager.get_indices(), faissManager.get_id_mapping(), top_k)

    movie_scores = dict()
    weight = {
        "title": 0.45,
        "content": 0.2,
        "type": 0.1,
        "people": 0.25
    }
    for r in result_raw:
        similarity = r["distance"]  # cosine similarity
        score = similarity
        movie_id = r["movieId"]
        movie_scores[movie_id] = movie_scores.get(movie_id, 0) + score*weight.get(r["type"], 0)

    sorted_movies = sorted(
        [{"movieId": movie_id, "score": score} for movie_id, score in movie_scores.items()],
        key=lambda x: x["score"],
        reverse=True
    )

    sorted_movies = sorted_movies[:top_k]

    movie_public = get_movies_by_ids(session, [m["movieId"] for m in sorted_movies])

    return MovieRecommendationResponse(recommendations=[
        MoviePublicWr(**movie.model_dump(), wr=sorted_movies[i]["score"])
        for i, movie in enumerate(movie_public)
    ])


class CollaborativeRequest(BaseModel):
    userId: int
    top_n: Optional[int] = 15

@router.post("/collaborative-filtering", response_model=MovieRecommendationResponse)
def collaborative_filtering_recommendation(
    *,
    session: SessionDep,
    mfModel: Annotated[MFModel, Depends(get_mf_model)],
    request: CollaborativeRequest
) -> MovieRecommendationResponse:
    user_id = request.userId

    query_ratings = text("""
            SELECT movie_id, rating
            FROM stg_rating
            WHERE user_id = :user_id
            ORDER BY rating DESC
        """)

    result_ratings = session.execute(query_ratings, {"user_id": user_id}).fetchall()

    if not result_ratings:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đánh giá nào cho user {user_id}")

    list_suggest_movie = []
    if len(result_ratings) < 10:
        # Dưới 10 đánh giá: Lấy top 3 phim có điểm cao nhất
        top_rated_movies = [row[0] for row in result_ratings[:min(3, len(result_ratings))]]  # Top 3 phim

        for mid in top_rated_movies:
            list_suggest_movie.extend(
                content_based_recommendation(session=session, request=ContentBaseRequest(movieId=mid, limit=5)).recommendations
            )
    else:
        # Từ 10 đánh giá trở lên: Lấy top 3 thể loại
        rated_movie_ids = [row[0] for row in result_ratings]
        query_genres = text("""
                WITH user_rated_movies AS (
                SELECT movie_id
                FROM stg_rating
                WHERE user_id = :user_id
            )
            SELECT g.genre, COUNT(*) AS count_num
            FROM user_rated_movies u
            JOIN stg_genre g ON u.movie_id = g.movie_id
            GROUP BY g.genre;
        """)
        result_genres = session.execute(query_genres, {"user_id": user_id}).fetchall()

        if not result_genres:
            raise HTTPException(status_code=404, detail="Không tìm thấy thể loại nào từ các phim đã đánh giá")

        # Lấy top 3 thể loại
        top_genres = sorted(result_genres, key=lambda x: x[1], reverse=True)[:min(3, len(result_genres))]

        # Tìm phim thuộc top 3 thể loại
        list_suggest_movie.extend(
            recommend_movies_by_genres(session=session, request_body=GenreRecommendationRequest(genres=[i[0] for i in top_genres], limit=15)).recommendations
        )

    exist = []
    for movie in list_suggest_movie:
        if movie.id in exist:
            list_suggest_movie.remove(movie)
        else:
            exist.append(movie.id)


    model = mfModel.model

    for movie in list_suggest_movie:
        movie.wr = model.predict(user_id, movie.id).est

    list_suggest_movie = sorted(list_suggest_movie, key=lambda x: x.wr, reverse=True)[:min(len(list_suggest_movie), request.top_n)]

    return MovieRecommendationResponse(recommendations=list_suggest_movie)

class UserIdsResponse(BaseModel):
    userIds: List[int]

@router.get("/all-users", response_model=UserIdsResponse)
def get_user_ids(session: SessionDep) -> UserIdsResponse:
    try:
        # Truy vấn lấy user_id duy nhất, sắp xếp tăng dần
        query = text("""
            SELECT user_id
            FROM (
                SELECT DISTINCT user_id
                FROM stg_rating
            ) AS subquery
            ORDER BY RANDOM()
            LIMIT 100;
        """)
        result = session.execute(query).fetchall()

        # Kiểm tra kết quả
        if not result:
            raise HTTPException(status_code=404, detail="Không tìm thấy userId nào trong bảng stg_rating")

        # Lấy danh sách userId
        user_ids = [row[0] for row in result]

        return UserIdsResponse(userIds=user_ids)

    except Exception as e:
        # Xử lý lỗi
        raise HTTPException(status_code=500, detail=f"Lỗi khi truy vấn bảng stg_rating: {str(e)}")
