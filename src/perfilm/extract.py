"""EXTRACT — lecture des sources hétérogènes (JSON, CSV, Excel binaire).

Correspond à la figure 23 du rapport.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from perfilm.config import Sources

log = logging.getLogger(__name__)


@dataclass
class RawData:
    wiki_movies_raw: list[dict]
    kaggle_metadata: pd.DataFrame
    ratings: pd.DataFrame
    imdb: pd.DataFrame | None


def read_wiki(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def read_kaggle_metadata(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def read_ratings(path: Path) -> pd.DataFrame:
    """Lit les évaluations MovieLens (userId, movieId, rating, timestamp).

    Le rapport utilisait un classeur Excel binaire (``ratings.xlsb``) ;
    les formats ``.xlsx`` et ``.csv`` sont aussi acceptés.
    """
    suffix = path.suffix.lower()
    if suffix == ".xlsb":
        return pd.read_excel(path, engine="pyxlsb")
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path)


def read_imdb(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        log.warning("Source IMDb absente (%s) : étape d'enrichissement ignorée", path)
        return None
    return pd.read_csv(path, low_memory=False)


def extract(sources: Sources) -> RawData:
    log.info("Extraction depuis %s", sources.data_dir)
    raw = RawData(
        wiki_movies_raw=read_wiki(sources.wiki_path),
        kaggle_metadata=read_kaggle_metadata(sources.kaggle_path),
        ratings=read_ratings(sources.ratings_path),
        imdb=read_imdb(sources.imdb_path),
    )
    log.info(
        "wiki=%d films, kaggle=%d lignes, ratings=%d lignes, imdb=%s",
        len(raw.wiki_movies_raw),
        len(raw.kaggle_metadata),
        len(raw.ratings),
        "absent" if raw.imdb is None else len(raw.imdb),
    )
    return raw
