# constants.py

from dataclasses import dataclass
from typing import Final


PYTHON_PATH: Final[str] = "app"

@dataclass(frozen=True)
class EmbeddingModelConstants:
    MODEL_SENTENCE_TRANSFORMER: Final[str] = "all-MiniLM-L6-v2"
    VECTOR_EMBEDDING_DIM : Final[int] = 384
    PATH_FAISSID_TO_MOVIEID : Final[str] = f"{PYTHON_PATH}/vector-embedding/faissid_to_movieid.pkl"
    PATH_FAISS_CONTENT_INDEX : Final[str] = f"{PYTHON_PATH}/vector-embedding/faiss_content.index"
    PATH_FAISS_TYPE_INDEX : Final[str] = f"{PYTHON_PATH}/vector-embedding/faiss_type.index"
    PATH_FAISS_TITLE_INDEX : Final[str] = f"{PYTHON_PATH}/vector-embedding/faiss_title.index"
    PATH_FAISS_PEOPLE_INDEX : Final[str] = f"{PYTHON_PATH}/vector-embedding/faiss_people.index"
    PATH_MOVIE_EMBEDDING: Final[str] = f"{PYTHON_PATH}/vector-embedding/movie_embedding.pkl"

@dataclass(frozen=True)
class MFModelConstants:
    PATH_INDEX_TO_MOVIEID : Final[str] = f"{PYTHON_PATH}/matrix-factorial/index_to_movieid.pkl"
    PATH_INDEX_TO_USERID : Final[str] = f"{PYTHON_PATH}/matrix-factorial/index_to_userid.pkl"
    PATH_MOVIEID_TO_INDEX : Final[str] = f"{PYTHON_PATH}/matrix-factorial/movieid_to_index.pkl"
    PATH_USERID_TO_INDEX : Final[str] = f"{PYTHON_PATH}/matrix-factorial/userid_to_index.pkl"
    PATH_MF_MODEL : Final[str] = f"{PYTHON_PATH}/matrix-factorial/model_SVD.pkl"


SEARCH_TYPE: Final[list[str]] = ["title", "content", "type", "people"]

@dataclass(frozen=True)
class Genres:
    pass