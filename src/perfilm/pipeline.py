"""Orchestration du pipeline ETL (figure 22 du rapport).

    lecture -> sélection -> renommage -> harmonisation -> regroupement des langues
    -> suppression des colonnes ≥ 90 % nulles -> correction grammaticale
    -> uniformisation monétaire -> fusion -> dimensions -> table de faits -> chargement

Usage ::

    perfilm                       # sources dans $PERFILM_DATA_DIR, base $PERFILM_DATABASE_URL
    perfilm --data-dir data/raw --database-url sqlite:///movies.db
    perfilm --dry-run             # transforme sans charger, affiche les volumes
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from perfilm.config import Sources, get_settings
from perfilm.extract import extract
from perfilm.load import get_engine, load
from perfilm.transform.dimensions import StarSchema, build_star_schema
from perfilm.transform.kaggle import language_names, transform_kaggle
from perfilm.transform.merge import build_movies_with_ratings
from perfilm.transform.wiki import transform_wiki

log = logging.getLogger("perfilm")


def transform(sources: Sources) -> StarSchema:
    raw = extract(sources)
    wiki_df = transform_wiki(raw.wiki_movies_raw)
    kaggle_df = transform_kaggle(raw.kaggle_metadata)
    movies_with_ratings_df = build_movies_with_ratings(wiki_df, kaggle_df, raw.ratings, raw.imdb)
    return build_star_schema(movies_with_ratings_df, language_names(kaggle_df))


def run(sources: Sources, database_url: str | None, dry_run: bool = False) -> StarSchema:
    star = transform(sources)
    for name, df in {**star.dimensions(), "fact_movies": star.fact_movies}.items():
        log.info("%-12s %8d lignes", name, len(df))
    if not dry_run:
        load(star, get_engine(database_url))
        log.info("Chargement terminé")
    return star


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pipeline ETL PerFilm")
    parser.add_argument("--data-dir", type=Path, help="dossier des fichiers sources")
    parser.add_argument("--database-url", help="URL SQLAlchemy de l'entrepôt")
    parser.add_argument("--dry-run", action="store_true", help="ne charge pas la base")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    settings = get_settings()
    sources = settings.sources
    if args.data_dir:
        sources = replace(sources, data_dir=args.data_dir)
    run(sources, args.database_url or settings.database_url, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
