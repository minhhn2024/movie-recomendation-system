import uuid
from datetime import date
from typing import Optional, List

from pydantic import EmailStr, BaseModel
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

class StgGenre(SQLModel, table=True):
    __tablename__ = "stg_genre"
    key_id: int = Field(primary_key=True)
    movie_id: Optional[int] = Field(default=None, index=True)
    genre: Optional[str] = Field(default=None)

class StgCast(SQLModel, table=True):
    __tablename__ = "stg_cast"
    key_id: int = Field(primary_key=True)
    movie_id: Optional[int] = Field(default=None, index=True)
    name: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)

class StgMovieMetadata(SQLModel, table=True):
    __tablename__ = "stg_movie_metadata"
    id: int = Field(primary_key=True)
    title: Optional[str] = Field(default=None)
    original_title: Optional[str] = Field(default=None)
    belongs_to_collection: Optional[str] = Field(default=None)
    original_language: Optional[str] = Field(default=None)
    release_date: Optional[date] = Field(default=None)  # Using str for simplicity
    status: Optional[str] = Field(default=None)
    overview: Optional[str] = Field(default=None)
    tagline: Optional[str] = Field(default=None)
    adult: Optional[str] = Field(default=None)
    popularity: Optional[float] = Field(default=None)
    homepage: Optional[str] = Field(default=None)
    poster_path: Optional[str] = Field(default=None)
    runtime: Optional[int] = Field(default=None)
    budget: Optional[int] = Field(default=None)
    revenue: Optional[int] = Field(default=None)
    vote_average: Optional[float] = Field(default=None)
    vote_count: Optional[int] = Field(default=None)
    imdb_id: Optional[int] = Field(default=None)
    tmdb_id: Optional[int] = Field(default=None)
    keywords: Optional[str] = Field(default=None)

class StgRating(SQLModel, table=True):
    __tablename__ = "stg_rating"
    key_id: int = Field(primary_key=True)
    user_id: int = Field(index=True)
    movie_id: int = Field(index=True)
    rating: float
    timestamp: Optional[int] = Field(default=None)

class CastPublic(BaseModel):
    name: str
    role: Optional[str]

class MoviePublic(BaseModel):
    id: int
    title: Optional[str]
    original_title: Optional[str]
    belongs_to_collection: Optional[str]
    release_date: Optional[date]
    overview: Optional[str]
    tagline: Optional[str]
    homepage: Optional[str]
    poster_path: Optional[str]
    vote_average: Optional[float]
    vote_count: Optional[int]
    imdb_id: Optional[int]
    tmdb_id: Optional[int]
    genres: List[str]
    cast: List[CastPublic]
    keywords: List[str]

class MoviesPublic(BaseModel):
    data: List[MoviePublic]
    count: int

class MoviePublicWr(MoviePublic):
    wr: Optional[float]

class MoviePublicWithRating(MoviePublic):
    rating: Optional[float] = None