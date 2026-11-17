"""Harmonisation et fusion des sources (Wikipedia ⨝ Kaggle ⨝ MovieLens ⨝ IMDb).

Règles de résolution des conflits, établies lors de l'exploration
(scatter plots wiki vs kaggle, figures 15 et 16) :

=====================  ==============  =================================================
Colonne                Source retenue  Repli
=====================  ==============  =================================================
title                  Kaggle          Wikipedia
runtime                Kaggle          Wikipedia (running_time)
budget                 Kaggle          Wikipedia
revenue                Kaggle          Wikipedia (box_office)
release_date           Kaggle          Wikipedia
original_language      Kaggle          —
genres / countries     Kaggle          —
production companies   Wikipedia       Kaggle
director               Wikipedia       IMDb
rating                 MovieLens       IMDb (avg_vote / 2, ramené sur 5)
=====================  ==============  =================================================
"""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)

#: au-delà de cet écart (années) entre les dates wiki et kaggle, la fusion est jugée erronée
MAX_RELEASE_YEAR_GAP = 5


def _fill(primary: pd.Series, fallback: pd.Series) -> pd.Series:
    return primary.where(primary.notna(), fallback)


def _fill_list(primary: pd.Series, fallback: pd.Series) -> pd.Series:
    return pd.Series(
        [p if p else f for p, f in zip(primary, fallback, strict=True)], index=primary.index
    )


def merge_wiki_kaggle(wiki_df: pd.DataFrame, kaggle_df: pd.DataFrame) -> pd.DataFrame:
    movies_df = pd.merge(wiki_df, kaggle_df, on="imdb_id", suffixes=("_wiki", "_kaggle"))

    # Fusions erronées : dates de sortie trop éloignées entre les deux sources
    gap = (movies_df["release_date_wiki"].dt.year - movies_df["release_date_kaggle"].dt.year).abs()
    bad = gap > MAX_RELEASE_YEAR_GAP
    if bad.any():
        log.info("%d fusions incohérentes (dates) supprimées", int(bad.sum()))
    movies_df = movies_df[~bad].copy()

    out = pd.DataFrame(index=movies_df.index)
    out["imdb_id"] = movies_df["imdb_id"]
    out["kaggle_id"] = movies_df["id"]
    out["title"] = _fill(movies_df["title_kaggle"], movies_df["title_wiki"])
    out["original_title"] = _fill(movies_df["original_title"], out["title"])
    out["runtime"] = _fill(movies_df["runtime"], movies_df["running_time"])
    out["budget"] = _fill(movies_df["budget_kaggle"], movies_df["budget_wiki"])
    out["revenue"] = _fill(movies_df["revenue"], movies_df["box_office"])
    out["release_date"] = _fill(movies_df["release_date_kaggle"], movies_df["release_date_wiki"])
    out["original_language"] = movies_df["original_language"]
    out["genres"] = movies_df["genres"]
    out["production_countries"] = movies_df["production_countries"]
    out["production_companies"] = _fill_list(
        movies_df["production_companies_wiki"], movies_df["production_companies_kaggle"]
    )
    out["director"] = movies_df["director"]
    return out.reset_index(drop=True)


def add_ratings(movies_df: pd.DataFrame, ratings: pd.DataFrame) -> pd.DataFrame:
    """Agrège les évaluations MovieLens par film (moyenne et nombre de votes)."""
    stats = (
        ratings.groupby("movieId")["rating"]
        .agg(rating_total="mean", rating_count="count")
        .reset_index()
        .rename(columns={"movieId": "kaggle_id"})
    )
    merged = movies_df.merge(stats, on="kaggle_id", how="left")
    merged["rating_count"] = merged["rating_count"].fillna(0).astype(int)
    return merged


def add_imdb(movies_df: pd.DataFrame, imdb: pd.DataFrame | None) -> pd.DataFrame:
    """Complète la note et le réalisateur à partir du fichier IMDb."""
    if imdb is None:
        return movies_df
    imdb_cols = imdb[["imdb_title_id", "avg_vote", "director"]].rename(
        columns={"imdb_title_id": "imdb_id", "director": "director_imdb"}
    )
    merged = movies_df.merge(imdb_cols, on="imdb_id", how="left")
    merged["rating_total"] = _fill(merged["rating_total"], merged["avg_vote"] / 2)
    imdb_directors = merged["director_imdb"].map(
        lambda d: [x.strip() for x in d.split(",") if x.strip()] if isinstance(d, str) else []
    )
    merged["director"] = _fill_list(merged["director"], imdb_directors)
    return merged.drop(columns=["avg_vote", "director_imdb"])


def build_movies_with_ratings(
    wiki_df: pd.DataFrame,
    kaggle_df: pd.DataFrame,
    ratings: pd.DataFrame,
    imdb: pd.DataFrame | None,
) -> pd.DataFrame:
    """Jeu de données consolidé ``movies_with_ratings_df`` utilisé pour les dimensions."""
    movies = merge_wiki_kaggle(wiki_df, kaggle_df)
    movies = add_ratings(movies, ratings)
    movies = add_imdb(movies, imdb)
    movies["rating_total"] = movies["rating_total"].astype(float).round(2)
    log.info("movies_with_ratings_df : %d films", len(movies))
    return movies
