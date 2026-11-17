"""Nettoyage des films Wikipedia (figures 24 à 28 du rapport).

Étapes :
  * sélection des données pertinentes (films avec réalisateur + lien IMDb, hors séries TV)
  * pivotement des titres alternatifs / renommage des colonnes (``clean_movie``)
  * suppression des colonnes contenant au moins 90 % de valeurs nulles
  * analyse grammaticale par expressions régulières des montants, dates et durées
  * uniformisation des valeurs monétaires (``parse_dollars``)
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

# Colonnes de titres alternatifs (une colonne par langue) regroupées dans une seule colonne
ALT_TITLE_KEYS = [
    "Also known as", "Arabic", "Cantonese", "Chinese", "French",
    "Hangul", "Hebrew", "Hepburn", "Japanese", "Literally",
    "Mandarin", "McCune-Reischauer", "Original title", "Polish",
    "Revised Romanization", "Romanized", "Russian",
    "Simplified", "Traditional", "Yiddish",
]  # fmt: skip

# Harmonisation des noms de colonnes : plusieurs libellés Wikipedia pour la même information
COLUMN_RENAMES = {
    "Adaptation by": "Writer(s)",
    "Country of origin": "Country",
    "Directed by": "Director",
    "Distributed by": "Distributor",
    "Edited by": "Editor(s)",
    "Length": "Running time",
    "Original release": "Release date",
    "Music by": "Composer(s)",
    "Produced by": "Producer(s)",
    "Producer": "Producer(s)",
    "Productioncompanies ": "Production company(s)",
    "Productioncompany ": "Production company(s)",
    "Released": "Release Date",
    "Release Date": "Release date",
    "Screen story by": "Writer(s)",
    "Screenplay by": "Writer(s)",
    "Story by": "Writer(s)",
    "Theme music composer": "Composer(s)",
    "Written by": "Writer(s)",
}

# --- Expressions régulières (figure 26) -------------------------------------------------
# $123.4 million / $1.2 billion
FORM_ONE = r"\$\s*\d+\.?\d*\s*[mb]illi?on"
# $123,456,789 (et non suivi de "million")
FORM_TWO = r"\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)"
# Intervalles « $5–7 million » -> « $7 million » (on garde la borne haute)
RANGE = r"\$.*[-—–](?![a-z])"
CITATION = r"\[\d+\]\s*"

DATE_FORM_ONE = (
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s[123]?\d,\s\d{4}"
)
DATE_FORM_TWO = r"\d{4}.[01]\d.[0123]\d"
DATE_FORM_THREE = (
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s\d{4}"
)
DATE_FORM_FOUR = r"\d{4}"


def is_relevant(movie: dict) -> bool:
    """Garde les films (pas les séries) ayant un réalisateur et un lien IMDb."""
    return (
        ("Director" in movie or "Directed by" in movie)
        and "imdb_link" in movie
        and "No. of episodes" not in movie
    )


def clean_movie(movie: dict) -> dict:
    """Pivote les titres alternatifs dans ``alt_titles`` et renomme les colonnes (figure 24)."""
    movie = dict(movie)
    alt_titles = {}

    for key in ALT_TITLE_KEYS:
        if key in movie:
            alt_titles[key] = movie.pop(key)
    if alt_titles:
        movie["alt_titles"] = alt_titles

    def change_column_name(old_name: str, new_name: str) -> None:
        if old_name in movie:
            movie[new_name] = movie.pop(old_name)

    for old_name, new_name in COLUMN_RENAMES.items():
        change_column_name(old_name, new_name)

    return movie


def parse_dollars(s) -> float:
    """Convertit une chaîne monétaire en float (figure 28)."""
    if not isinstance(s, str):
        return np.nan

    # forme $###.# million
    if re.match(r"\$\s*\d+\.?\d*\s*milli?on", s, flags=re.IGNORECASE):
        s = re.sub(r"\$|\s|[a-zA-Z]", "", s)
        return float(s) * 10**6

    # forme $###.# billion
    if re.match(r"\$\s*\d+\.?\d*\s*billi?on", s, flags=re.IGNORECASE):
        s = re.sub(r"\$|\s|[a-zA-Z]", "", s)
        return float(s) * 10**9

    # forme $###,###,### (séparateur de milliers « , » ou « . »)
    if re.match(r"\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)", s, flags=re.IGNORECASE):
        s = re.sub(r"\$|\s|,|\.(?=\d{3})", "", s)
        return float(s)

    return np.nan


def _join_lists(series: pd.Series) -> pd.Series:
    return series.map(lambda x: " ".join(map(str, x)) if isinstance(x, list) else x)


def parse_money_column(series: pd.Series) -> pd.Series:
    """Applique la chaîne d'analyse grammaticale complète à une colonne monétaire."""
    values = _join_lists(series.dropna())
    values = values.astype(str).str.replace(CITATION, "", regex=True)
    values = values.str.replace(RANGE, "$", regex=True)
    extracted = values.str.extract(f"({FORM_ONE}|{FORM_TWO})", flags=re.IGNORECASE)[0]
    return extracted.apply(parse_dollars).reindex(series.index)


def parse_release_date(series: pd.Series) -> pd.Series:
    values = _join_lists(series.dropna()).astype(str)
    pattern = f"({DATE_FORM_ONE}|{DATE_FORM_TWO}|{DATE_FORM_THREE}|{DATE_FORM_FOUR})"
    extracted = values.str.extract(pattern)[0]
    parsed = pd.to_datetime(extracted, format="mixed", errors="coerce")
    return parsed.reindex(series.index)


def parse_running_time(series: pd.Series) -> pd.Series:
    """« 1 hr 42 min », « 102 minutes », « 1h 42m » -> minutes (float)."""
    values = _join_lists(series.dropna()).astype(str)
    parts = values.str.extract(r"(\d+)\s*ho?u?r?s?\s*(\d*)|(\d+)\s*m")
    parts = parts.apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0)
    minutes = parts[0] * 60 + parts[1] + parts[2]
    minutes = minutes.where(minutes > 0)
    return minutes.reindex(series.index)


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [value]
    else:
        return []
    cleaned = [re.sub(CITATION, "", str(v)).strip() for v in items]
    return [c for c in cleaned if c]


def transform_wiki(wiki_movies_raw: list[dict], null_threshold: float = 0.9) -> pd.DataFrame:
    """Produit un DataFrame Wikipedia propre, indexé par ``imdb_id``."""
    wiki_movies = [clean_movie(m) for m in wiki_movies_raw if is_relevant(m)]
    wiki_movies_df = pd.DataFrame(wiki_movies)

    # identifiant IMDb : clé de fusion entre les sources
    wiki_movies_df["imdb_id"] = wiki_movies_df["imdb_link"].str.extract(r"(tt\d{7,8})")
    wiki_movies_df = wiki_movies_df.dropna(subset=["imdb_id"])
    wiki_movies_df = wiki_movies_df.drop_duplicates(subset="imdb_id")

    # Amputation des colonnes où au moins 90 % des valeurs sont nulles (figure 25)
    wiki_columns_to_keep = [
        column
        for column in wiki_movies_df.columns
        if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * null_threshold
    ]
    wiki_movies_df = wiki_movies_df[wiki_columns_to_keep].copy()

    def col(name: str) -> pd.Series:
        if name in wiki_movies_df:
            return wiki_movies_df[name]
        return pd.Series(np.nan, index=wiki_movies_df.index, dtype=object)

    out = pd.DataFrame(index=wiki_movies_df.index)
    out["imdb_id"] = wiki_movies_df["imdb_id"]
    out["title"] = col("title")
    out["box_office"] = parse_money_column(col("Box office"))
    out["budget"] = parse_money_column(col("Budget"))
    out["release_date"] = parse_release_date(col("Release date"))
    out["running_time"] = parse_running_time(col("Running time"))
    out["director"] = col("Director").map(_as_list)
    out["production_companies"] = col("Production company(s)").map(_as_list)
    out["country"] = col("Country").map(_as_list)
    return out.reset_index(drop=True)
