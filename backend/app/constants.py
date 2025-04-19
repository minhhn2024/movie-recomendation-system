# constants.py

from dataclasses import dataclass
from typing import Final

DATA_DIR: Final[str] = "/data"
MOVIES_FILE: Final[str] = f"{DATA_DIR}/movies_simplify.csv"
GENRES_FILE: Final[str] = f"{DATA_DIR}/genres.csv"

MAX_CHART_RECOMMENDATIONS: Final[int] = 250


@dataclass(frozen=True)
class Genres:
    pass