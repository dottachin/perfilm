"""Nettoyage des métadonnées Kaggle (``movies_metadata.csv``, The Movies Dataset / TMDB).

Les colonnes ``genres``, ``production_companies``, ``production_countries`` et
``spoken_languages`` sont des listes de dictionnaires sérialisées en texte Python,
par ex. ``"[{'id': 16, 'name': 'Animation'}]"``.
"""

from __future__ import annotations

import ast

import pandas as pd


def parse_named_list(value, key: str = "name") -> list[str]:
    """``"[{'id': 16, 'name': 'Animation'}]"`` -> ``['Animation']``."""
    if not isinstance(value, str) or not value.startswith("["):
        return []
    try:
        items = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []
    return [str(i[key]).strip() for i in items if isinstance(i, dict) and i.get(key)]


def parse_code_name_pairs(value, code_key: str) -> list[tuple[str, str]]:
    """``"[{'iso_639_1': 'en', 'name': 'English'}]"`` -> ``[('en', 'English')]``."""
    if not isinstance(value, str) or not value.startswith("["):
        return []
    try:
        items = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []
    return [
        (str(i[code_key]).strip(), str(i.get("name") or "").strip())
        for i in items
        if isinstance(i, dict) and i.get(code_key)
    ]


def transform_kaggle(kaggle_metadata: pd.DataFrame) -> pd.DataFrame:
    df = kaggle_metadata.copy()

    # lignes corrompues (décalage de colonnes) et films pour adultes / vidéos
    df = df[df["adult"].astype(str) == "False"].drop(columns="adult")
    if "video" in df:
        df["video"] = df["video"].astype(str) == "True"

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id", "imdb_id"])
    df["id"] = df["id"].astype(int)
    for column in ("budget", "revenue", "runtime", "popularity", "vote_average", "vote_count"):
        if column in df:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    df["genres"] = df["genres"].map(parse_named_list)
    df["production_companies"] = df["production_companies"].map(parse_named_list)
    df["production_countries"] = df["production_countries"].map(parse_named_list)
    df["spoken_languages_pairs"] = df["spoken_languages"].map(
        lambda v: parse_code_name_pairs(v, "iso_639_1")
    )

    # Une valeur 0 pour budget / revenu / durée signifie « inconnue »
    for column in ("budget", "revenue", "runtime"):
        df[column] = df[column].mask(df[column] == 0)

    return df.drop_duplicates(subset="imdb_id").reset_index(drop=True)


def language_names(kaggle_df: pd.DataFrame) -> dict[str, str]:
    """Construit le dictionnaire code ISO 639-1 -> libellé à partir de ``spoken_languages``."""
    mapping: dict[str, str] = {}
    for pairs in kaggle_df["spoken_languages_pairs"]:
        for code, name in pairs:
            if name and code not in mapping:
                mapping[code] = name
    return mapping
