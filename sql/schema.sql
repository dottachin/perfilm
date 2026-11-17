-- =====================================================================
-- PerFilm — entrepôt de données (schéma en étoile, figure 6 du rapport)
-- PostgreSQL 13+
--   createdb movies && psql -d movies -f sql/schema.sql
-- Le pipeline Python crée aussi ces tables (perfilm/schema.py).
-- =====================================================================

DROP TABLE IF EXISTS fact_movies;
DROP TABLE IF EXISTS genre, studio, pays, realisateur, langue, movie, "date";

CREATE TABLE genre (
    id_genre        INTEGER      PRIMARY KEY,
    genre           VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE studio (
    id_studio       INTEGER      PRIMARY KEY,
    studio          VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE pays (
    id_pays         INTEGER      PRIMARY KEY,
    pays            VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE realisateur (
    id_realisateur  INTEGER      PRIMARY KEY,
    realisateur     VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE langue (
    id_langue       INTEGER      PRIMARY KEY,
    langue          VARCHAR(20)  NOT NULL UNIQUE,   -- code ISO 639-1 (ex. 'en')
    langue_complete VARCHAR(100)                    -- libellé (ex. 'English')
);

CREATE TABLE movie (
    id_movie        VARCHAR(12)  PRIMARY KEY,       -- identifiant IMDb (ex. 'tt0098987')
    titre           VARCHAR(500) NOT NULL,
    titre_original  VARCHAR(500),
    duree           DOUBLE PRECISION,               -- minutes
    rating          DOUBLE PRECISION                -- note moyenne sur 5
);

CREATE TABLE "date" (
    id_date              INTEGER PRIMARY KEY,       -- AAAAMMJJ, 0 = date inconnue
    "date"               DATE,
    annee                INTEGER,
    trimestre            INTEGER,
    libelle_trimestre    VARCHAR(10),
    mois                 INTEGER,
    libelle_mois         VARCHAR(20),
    jour_semaine         INTEGER,                   -- 1 = lundi … 7 = dimanche
    libelle_jour_semaine VARCHAR(20),
    jour                 INTEGER
);

CREATE TABLE fact_movies (
    id_fact         INTEGER      PRIMARY KEY,
    id_movie        VARCHAR(12)  NOT NULL REFERENCES movie (id_movie),
    id_date         INTEGER      NOT NULL REFERENCES "date" (id_date),
    id_genre        INTEGER      NOT NULL REFERENCES genre (id_genre),
    id_studio       INTEGER      NOT NULL REFERENCES studio (id_studio),
    id_pays         INTEGER      NOT NULL REFERENCES pays (id_pays),
    id_realisateur  INTEGER      NOT NULL REFERENCES realisateur (id_realisateur),
    id_langue       INTEGER      NOT NULL REFERENCES langue (id_langue),
    budget          DOUBLE PRECISION,               -- mesure
    revenue         DOUBLE PRECISION,               -- mesure
    poids           DOUBLE PRECISION NOT NULL       -- 1 / nb de lignes du film (anti double comptage)
);

CREATE INDEX ix_fact_movies_id_movie       ON fact_movies (id_movie);
CREATE INDEX ix_fact_movies_id_date        ON fact_movies (id_date);
CREATE INDEX ix_fact_movies_id_genre       ON fact_movies (id_genre);
CREATE INDEX ix_fact_movies_id_studio      ON fact_movies (id_studio);
CREATE INDEX ix_fact_movies_id_pays        ON fact_movies (id_pays);
CREATE INDEX ix_fact_movies_id_realisateur ON fact_movies (id_realisateur);
CREATE INDEX ix_fact_movies_id_langue      ON fact_movies (id_langue);
