"""Définition de l'entrepôt (schéma en étoile, figure 6 du rapport) avec SQLAlchemy Core.

Le même schéma est disponible en SQL pur dans ``sql/schema.sql`` (PostgreSQL).
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)

metadata = MetaData()

genre = Table(
    "genre", metadata,
    Column("id_genre", Integer, primary_key=True, autoincrement=False),
    Column("genre", String(100), nullable=False, unique=True),
)  # fmt: skip

studio = Table(
    "studio", metadata,
    Column("id_studio", Integer, primary_key=True, autoincrement=False),
    Column("studio", String(255), nullable=False, unique=True),
)  # fmt: skip

pays = Table(
    "pays", metadata,
    Column("id_pays", Integer, primary_key=True, autoincrement=False),
    Column("pays", String(100), nullable=False, unique=True),
)  # fmt: skip

realisateur = Table(
    "realisateur", metadata,
    Column("id_realisateur", Integer, primary_key=True, autoincrement=False),
    Column("realisateur", String(255), nullable=False, unique=True),
)  # fmt: skip

langue = Table(
    "langue", metadata,
    Column("id_langue", Integer, primary_key=True, autoincrement=False),
    Column("langue", String(20), nullable=False, unique=True),
    Column("langue_complete", String(100)),
)  # fmt: skip

movie = Table(
    "movie", metadata,
    Column("id_movie", String(12), primary_key=True),
    Column("titre", String(500), nullable=False),
    Column("titre_original", String(500)),
    Column("duree", Float),
    Column("rating", Float),
)  # fmt: skip

date = Table(
    "date", metadata,
    Column("id_date", Integer, primary_key=True, autoincrement=False),
    Column("date", Date),
    Column("annee", Integer),
    Column("trimestre", Integer),
    Column("libelle_trimestre", String(10)),
    Column("mois", Integer),
    Column("libelle_mois", String(20)),
    Column("jour_semaine", Integer),
    Column("libelle_jour_semaine", String(20)),
    Column("jour", Integer),
)  # fmt: skip

fact_movies = Table(
    "fact_movies", metadata,
    Column("id_fact", Integer, primary_key=True, autoincrement=False),
    Column("id_movie", String(12), ForeignKey("movie.id_movie"), nullable=False, index=True),
    Column("id_date", Integer, ForeignKey("date.id_date"), nullable=False, index=True),
    Column("id_genre", Integer, ForeignKey("genre.id_genre"), nullable=False, index=True),
    Column("id_studio", Integer, ForeignKey("studio.id_studio"), nullable=False, index=True),
    Column("id_pays", Integer, ForeignKey("pays.id_pays"), nullable=False, index=True),
    Column(
        "id_realisateur", Integer, ForeignKey("realisateur.id_realisateur"),
        nullable=False, index=True,
    ),
    Column("id_langue", Integer, ForeignKey("langue.id_langue"), nullable=False, index=True),
    Column("budget", Float),
    Column("revenue", Float),
    Column("poids", Float, nullable=False),
)  # fmt: skip

#: ordre de chargement : dimensions puis faits
LOAD_ORDER = ["genre", "studio", "pays", "realisateur", "langue", "movie", "date", "fact_movies"]
