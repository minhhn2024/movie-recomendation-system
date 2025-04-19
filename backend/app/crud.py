import uuid
from typing import Any

from sqlmodel import Session, select
import pandas as pd

from app.core.ml_compute import build_chart
from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate, Movie


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

def recommend_by_genres(*, session: Session, genres: list[str], limit: int = 10) -> list[Movie]:
    # truy van db
    #  do something
    # load to pandas
    movies_data = pd.read_csv("app/data/movies_simplify.csv")
    genres_data = pd.read_csv("app/data/genres.csv")
    merged = pd.merge(genres_data, movies_data, left_on='id', right_on='id')
    filtered = merged[merged['genre'].isin(genres)]

    qualified = build_chart(filtered, 0.85, limit)
    movie_list = [Movie(**row) for row in qualified.to_dict(orient="records")]

    return movie_list