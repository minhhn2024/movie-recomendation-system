import logging
import pickle
from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app import constants
from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User

from sentence_transformers import SentenceTransformer
import faiss

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

_embedding_model = None

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(constants.EmbeddingModelConstants.MODEL_SENTENCE_TRANSFORMER)
    return _embedding_model

EmbeddingModelDep = Annotated[SentenceTransformer, Depends(get_embedding_model)]

class FaissIndexManager:
    def __init__(self):
        with open(constants.EmbeddingModelConstants.PATH_FAISSID_TO_MOVIEID, "rb") as f:
            self.id_mapping = pickle.load(f)

        self.title_index = faiss.read_index(constants.EmbeddingModelConstants.PATH_FAISS_TITLE_INDEX)
        self.content_index = faiss.read_index(constants.EmbeddingModelConstants.PATH_FAISS_CONTENT_INDEX)
        self.type_index = faiss.read_index(constants.EmbeddingModelConstants.PATH_FAISS_TYPE_INDEX)
        self.people_index = faiss.read_index(constants.EmbeddingModelConstants.PATH_FAISS_PEOPLE_INDEX)

        with open(constants.EmbeddingModelConstants.PATH_MOVIE_EMBEDDING, "rb") as f:
            self.movie_embedding = pickle.load(f)

    def get_indices(self):
        return {"title": self.title_index, "content": self.content_index, "type": self.type_index, "people": self.people_index}

    def get_id_mapping(self):
        return self.id_mapping

    def get_embedding_vector(self, movieId):
        return self.movie_embedding[movieId]

_faiss_manager: FaissIndexManager | None = None

def get_faiss_manager() -> FaissIndexManager:
    global _faiss_manager
    if _faiss_manager is None:
        _faiss_manager = FaissIndexManager()
    return _faiss_manager

class MFModel:
    def __init__(self):
        with open(constants.MFModelConstants.PATH_MF_MODEL, "rb") as f:
            self.model = pickle.load(f)


_mf_model: MFModel | None = None

def get_mf_model() -> MFModel:
    global _mf_model
    if _mf_model is None:
        _mf_model = MFModel()
    return _mf_model

def load_models():
    global _faiss_manager, _mf_model, _embedding_model
    try:
        logging.info("Loading FAISS indexes...")
        _faiss_manager = FaissIndexManager()
    except Exception as e:
        logging.error(f"Failed to load FAISS indexes: {e}")
        raise

    try:
        logging.info("Loading MF model...")
        _mf_model = MFModel()
    except Exception as e:
        logging.error(f"Failed to load MF model: {e}")
        raise

    try:
        logging.info("Loading embedding model...")
        _embedding_model = SentenceTransformer(constants.EmbeddingModelConstants.MODEL_SENTENCE_TRANSFORMER)
    except Exception as e:
        logging.error(f"Failed to load embedding model: {e}")
        raise

    logging.info("All models loaded successfully.")