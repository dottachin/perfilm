"""Configuration : chemins des sources et chaîne de connexion à l'entrepôt.

Les valeurs viennent des variables d'environnement (ou d'un fichier ``.env``) ;
aucun secret n'est codé en dur.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Sources:
    """Emplacement des 4 fichiers sources décrits dans le rapport (chapitre V.I)."""

    data_dir: Path
    wiki_json: str = "wikipedia-movies.json"
    kaggle_metadata: str = "movies_metadata.csv"
    ratings: str = "ratings.xlsb"
    imdb: str = "IMDb movies.csv"

    def path(self, name: str) -> Path:
        return self.data_dir / name

    @property
    def wiki_path(self) -> Path:
        return self.path(self.wiki_json)

    @property
    def kaggle_path(self) -> Path:
        return self.path(self.kaggle_metadata)

    @property
    def ratings_path(self) -> Path:
        # Accepte ratings.xlsb (version du rapport), ratings.xlsx ou ratings.csv (MovieLens brut)
        base = self.path(self.ratings)
        if base.exists():
            return base
        for ext in (".csv", ".xlsx", ".xlsb"):
            candidate = base.with_suffix(ext)
            if candidate.exists():
                return candidate
        return base

    @property
    def imdb_path(self) -> Path:
        return self.path(self.imdb)


@dataclass(frozen=True)
class Settings:
    sources: Sources = field(
        default_factory=lambda: Sources(
            data_dir=Path(os.getenv("PERFILM_DATA_DIR", PROJECT_ROOT / "data" / "raw"))
        )
    )
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "PERFILM_DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/movies",
        )
    )


def get_settings() -> Settings:
    return Settings()
