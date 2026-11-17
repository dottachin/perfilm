"""LOAD — chargement du schéma en étoile dans l'entrepôt (figure 33 du rapport)."""

from __future__ import annotations

import logging

from sqlalchemy import Engine, create_engine

from perfilm.schema import LOAD_ORDER, metadata
from perfilm.transform.dimensions import StarSchema

log = logging.getLogger(__name__)


def get_engine(database_url: str) -> Engine:
    return create_engine(database_url)


def load(star: StarSchema, engine: Engine, replace: bool = True, chunksize: int = 5000) -> None:
    """Crée les tables (avec clés primaires/étrangères) puis insère dimensions et faits.

    ``replace=True`` rend le chargement idempotent : les tables sont supprimées puis recréées.
    """
    if replace:
        metadata.drop_all(engine)
    metadata.create_all(engine)

    frames = {**star.dimensions(), "fact_movies": star.fact_movies}
    with engine.begin() as conn:
        for name in LOAD_ORDER:
            df = frames[name]
            df.to_sql(name, conn, if_exists="append", index=False, chunksize=chunksize)
            log.info("table %-12s : %d lignes chargées", name, len(df))
