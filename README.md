<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img src="assets/logo.svg" alt="PerFilm" width="440">
  </picture>
</p>

<p align="center">
  <img alt="License: All rights reserved" src="https://img.shields.io/badge/license-All%20rights%20reserved-red">
  <img alt="Status: Portfolio - view only" src="https://img.shields.io/badge/status-portfolio%20%C2%B7%20view%20only-0f172a">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776ab">
  <img alt="End-of-study project (PFE, Licence SMI)" src="https://img.shields.io/badge/PFE-Licence%20SMI%20%C2%B7%202021-4f46e5">
</p>

> [!IMPORTANT]
> **This is proprietary software, shown for portfolio purposes only.**
> You may view the code, but you may not copy, run, modify, distribute or sell any part of it without written permission. See [LICENSE](LICENSE).

# PerFilm

**PerFilm** is a business-intelligence system for analysing how movies perform. It answers questions such as **which genres earn the most compared to their budget, in which countries, and how has that changed over the years?**

PerFilm merges four public sources: Wikipedia infoboxes, TMDB metadata from Kaggle, MovieLens audience ratings and IMDb ratings. A Python ETL pipeline cleans the messy values (money written as `$2–3 million [4]`, dates in four formats, runtimes like `1 hr 42 min`), joins the sources on the IMDb id and loads a **PostgreSQL star schema**. A **Mondrian ROLAP cube** sits on top of the warehouse, and **Knowage** turns it into reports and dashboards that you can filter by genre, country, studio, director, language and date.

It was my end-of-study project (PFE, Licence Sciences Mathématiques et Informatique, option SID, Faculté des Sciences Aïn Chock, 2020/2021). The original code was lost. This repository rebuilds it from the project report, keeping its design and naming.

---

## Table of contents

1. [How it works (big picture)](#how-it-works-big-picture)
2. [Services](#services)
3. [Repository layout](#repository-layout)
4. [Features in detail](#features-in-detail)
5. [Prerequisites](#prerequisites)
6. [Configuration (environment variables)](#configuration-environment-variables)
7. [Quick start with Docker](#quick-start-with-docker)
8. [Local development (sample data, no Docker)](#local-development-sample-data-no-docker)
9. [The ETL pipeline](#the-etl-pipeline)
10. [The data warehouse](#the-data-warehouse)
11. [The OLAP cube and reports](#the-olap-cube-and-reports)
12. [Differences from the 2021 version](#differences-from-the-2021-version)
13. [Testing](#testing)
14. [Troubleshooting](#troubleshooting)
15. [Data credits](#data-credits)
16. [License](#license)

---

## How it works (big picture)

```
 wikipedia-movies.json ─┐
 movies_metadata.csv  ──┤   ┌──────────────────────────┐   ┌───────────────┐   ┌───────────────┐   ┌──────────────┐
 ratings.xlsb / .csv  ──┼──▶│ ETL (Python, pandas)     │──▶│ PostgreSQL    │──▶│ Mondrian      │──▶│ Knowage      │
 IMDb movies.csv      ──┘   │ extract → transform →    │   │ star schema   │   │ ROLAP cube    │   │ reports and  │
                            │ load                     │   │ (warehouse)   │   │ (MDX)         │   │ dashboards   │
                            └──────────────────────────┘   └───────────────┘   └───────────────┘   └──────────────┘
```

1. **Extract**: the four files are read as they are (JSON, CSV, binary Excel).
2. **Transform**: Wikipedia records are filtered and normalised. Money, dates and runtimes are parsed with regular expressions. Kaggle's JSON-in-text columns are decoded. The sources are merged on the IMDb id with explicit rules for which source wins.
3. **Load**: dimensions and the fact table are written to PostgreSQL, with primary keys, foreign keys and indexes.
4. **Analyse**: Mondrian maps the star schema to a cube with weighted money measures and ratio members. Knowage queries it with MDX and renders the reports.

---

## Services

All services run from `docker-compose.yml`. The ETL itself is a Python command (`perfilm`) that you run on the host.

| Service | Role | URL / port |
|---|---|---|
| `warehouse` | PostgreSQL 16, the star-schema data warehouse | :5432 |
| `knowage` | Knowage BI suite: OLAP documents, cockpits, reports (profile `bi`) | http://localhost:8080/knowage |
| `knowage-db` | MariaDB metadata store for Knowage (profile `bi`) | not exposed |
| `pgadmin` | pgAdmin 4, to browse the warehouse (profile `admin`) | http://localhost:5050 |

---

## Repository layout

```
perfilm/
├── assets/                  logo
├── data/                    where the source files go (not versioned, see data/README.md)
├── notebooks/
│   └── 01_exploration.ipynb exploration of the sources and cross-source integrity checks
├── olap/
│   ├── movies_mondrian_schema.xml   Mondrian cube: dimensions, weighted measures, calculated members
│   ├── Template.xml                 Knowage OLAP document template
│   └── queries.mdx                  MDX for the example reports
├── sql/
│   ├── schema.sql           warehouse DDL (PostgreSQL)
│   └── reports.sql          SQL versions of the example reports
├── src/perfilm/
│   ├── extract.py           reads JSON / CSV / .xlsb sources
│   ├── transform/
│   │   ├── wiki.py          clean_movie, parse_dollars, date and runtime parsing
│   │   ├── kaggle.py        typing and decoding of TMDB list columns
│   │   ├── merge.py         source merge and conflict-resolution rules
│   │   └── dimensions.py    dimensions, exploded fact table, weights
│   ├── schema.py            the same warehouse schema in SQLAlchemy
│   ├── load.py              idempotent load
│   ├── pipeline.py          orchestration and the `perfilm` command
│   ├── sample_data.py       synthetic sample in the format of the real sources
│   └── config.py            settings from environment variables
├── tests/                   pytest suite, including an end-to-end run on SQLite
├── docker-compose.yml       warehouse, Knowage, pgAdmin
└── pyproject.toml           package, `perfilm` command, optional extras (explore, dev)
```

---

## Features in detail

**Reports.** Budget and revenue broken down by genre, country, studio, director, language, year, quarter, month and weekday. The examples in `sql/reports.sql` and `olap/queries.mdx` reproduce the three reports from the project:
- genre distribution of UK movies by budget and revenue, 2007–2017
- revenue/budget ratio per genre and year in the US
- the most profitable genres across all countries

**Dashboards.** Knowage cockpits combine a data table, pie charts per genre (budget vs revenue), a parallel chart and filters for country, year, quarter, month and weekday.

**Report customisation.** Analysts can pivot, drill down (year → quarter → month → day), filter and export the OLAP views without writing SQL. Report designers create new documents from the same cube.

**Audience ratings.** Each movie has an average rating out of 5. It comes from MovieLens, with the IMDb score (scaled to 5) as a fallback.

**Roles.** Knowage handles users and permissions. The administrator manages roles, the report designer builds reports, and the analyst consults, customises and exports them.

---

## Prerequisites

- Python 3.10 or newer, with [uv](https://docs.astral.sh/uv/) or pip
- Docker with Compose v2, for the warehouse and Knowage
- The four source files for a full run (see [data/README.md](data/README.md)). They are not needed for the sample run.

---

## Configuration (environment variables)

Copy `.env.example` to `.env` and adjust it. `.env` is git-ignored.

| Variable | Example | Description |
|---|---|---|
| `PERFILM_DATA_DIR` | `data/raw` | Folder that holds the four source files. |
| `PERFILM_DATABASE_URL` | `postgresql+psycopg2://postgres:…@localhost:5432/movies` | SQLAlchemy URL of the warehouse. Any SQLAlchemy URL works, for example `sqlite:///perfilm.db`. |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | `postgres` / `change-me` | Credentials of the `warehouse` service. **Required** by compose. |
| `KNOWAGE_DB_PASSWORD`, `KNOWAGE_DB_ROOT_PASSWORD` | | Knowage metadata database. |
| `KNOWAGE_HMAC_KEY`, `KNOWAGE_PASSWORD_ENCRYPTION_SECRET`, `KNOWAGE_SENSIBLE_DATA_ENCRYPTION_SECRET` | | Knowage secrets. **Change them** from the defaults. |
| `PGADMIN_PASSWORD` | | pgAdmin login (`admin@perfilm.local`). |

---

## Quick start with Docker

```bash
# 1. Python environment
uv venv && uv pip install -e ".[dev,explore]"

# 2. Configuration
cp .env.example .env                 # set the passwords

# 3. Warehouse
docker compose up -d warehouse

# 4. Put the four source files in data/raw/, then run the ETL
.venv/bin/perfilm

# 5. BI layer
docker compose --profile bi up -d    # Knowage on http://localhost:8080/knowage
```

Then, in Knowage:

1. Create a JDBC PostgreSQL data source: `jdbc:postgresql://warehouse:5432/movies`.
2. Import `olap/movies_mondrian_schema.xml` into the Mondrian schemas catalog as `movies_schema`.
3. Create an OLAP document from `olap/Template.xml`.
4. Build cockpits on top of it: tables, genre pie charts, parallel charts, filters.

---

## Local development (sample data, no Docker)

`perfilm.sample_data` writes a small synthetic dataset that uses the real file formats and their messy values. The whole pipeline then runs against SQLite in about a second:

```bash
.venv/bin/python -m perfilm.sample_data data/sample
.venv/bin/perfilm --data-dir data/sample --database-url sqlite:///perfilm-demo.db
```

| Flag | Effect |
|---|---|
| `--data-dir` | Overrides `PERFILM_DATA_DIR`. |
| `--database-url` | Overrides `PERFILM_DATABASE_URL`. |
| `--dry-run` | Transforms everything and prints row counts, without loading. |
| `-v` | Debug logging. |

The exploration notebook (`notebooks/01_exploration.ipynb`) shows the raw files, null rates and types. It also plots budget and release-date agreement between Wikipedia and Kaggle, which is how the merge rules below were chosen.

---

## The ETL pipeline

```
read → select relevant records → rename columns → harmonise → group language columns
     → drop columns ≥ 90 % null → regex parsing → normalise money values
     → merge sources → build dimensions → build fact table → load
```

**Wikipedia cleaning** (`transform/wiki.py`):
- Only movies that have a director and an IMDb link are kept. TV series are dropped.
- Alternative titles in about twenty languages are folded into one `alt_titles` field.
- Duplicate labels are renamed to a single name, for example `Directed by` → `Director`.
- Columns that are at least 90 % null are dropped.
- Money values go through citation removal, range handling (`$2–3 million` → `$3 million`) and two regex forms (`$123.4 million`, `$123,456,789`) before `parse_dollars`. Values in other currencies become empty, not wrong numbers.

**Merge rules** (`transform/merge.py`):

| Column | Source used | Fallback |
|---|---|---|
| title, runtime, budget, revenue, release date | Kaggle | Wikipedia |
| original language, genres, countries | Kaggle | — |
| production companies, director | Wikipedia | Kaggle / IMDb |
| rating | MovieLens (mean) | IMDb `avg_vote / 2` |

Merges whose release dates differ by more than five years are treated as wrong matches and dropped.

---

## The data warehouse

A star schema with French domain names, kept from the original project:

```
        genre(id_genre, genre)                movie(id_movie, titre, titre_original, duree, rating)
      studio(id_studio, studio)        ╲     ╱
          pays(id_pays, pays)      ─── fact_movies ───  date(id_date, date, annee, trimestre, libelle_trimestre,
realisateur(id_realisateur, realisateur)  budget         mois, libelle_mois, jour_semaine, libelle_jour_semaine, jour)
  langue(id_langue, langue, langue_complete)  revenue
                                            poids
```

- **Grain**: one fact row per movie × genre × studio × country × director × language.
- **`poids`** (weight) is `1 / number of rows for that movie`. Money is always aggregated as `budget * poids`, so a movie with three genres isn't counted three times.
- **Unknown values** map to an `Inconnu` member in each dimension, and an unknown date maps to `id_date = 0`. No fact is lost in a join.
- **`id_date`** is an integer `YYYYMMDD`. Month and weekday labels are in French.

The schema is defined in `sql/schema.sql` and, identically, in `src/perfilm/schema.py`.

---

## The OLAP cube and reports

`movies_cube` (`olap/movies_mondrian_schema.xml`) has these dimensions: `genre`, `realisateur`, `studio`, `pays`, `langue`, `movie` (with `duree` and `rating` as properties) and `date`. The `date` dimension has a year → quarter → month → day hierarchy and a separate weekday hierarchy.

| Measure | Definition |
|---|---|
| `budget`, `revenue` | Weighted sums (`… * poids`). |
| `nb_films` | Distinct count of movies. |
| `ratio_revenu_budget` | `revenue / budget`, empty when the budget is 0. |
| `marge` | `revenue − budget`. |

Example MDX, the profitability of genres between 2007 and 2017:

```mdx
SELECT {[Measures].[marge], [Measures].[ratio_revenu_budget], [Measures].[nb_films]} ON COLUMNS,
       Order(NON EMPTY [genre].[genre].Members, [Measures].[marge], BDESC) ON ROWS
FROM [movies_cube]
WHERE {[date].[2007] : [date].[2017]}
```

---

## Differences from the 2021 version

| 2021 | Now | Why |
|---|---|---|
| Database password written in the notebook | Environment variables (`.env`) | Security |
| Fact table columns held text labels | Integer foreign keys to the dimensions | Referential integrity |
| `id_date` was text in the dimension and an integer in the fact table | Integer `YYYYMMDD` on both sides | Consistency |
| Budget and revenue repeated on every exploded row | `poids` weight and weighted cube measures | No double counting |
| Missing values dropped facts at join time | `Inconnu` members | Every movie stays in the totals |
| A single Jupyter notebook | Python package, CLI, tests, CI | Reproducibility |

---

## Testing

```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest
```

The unit tests cover `parse_dollars`, money ranges and citations, runtime parsing, `clean_movie` and record filtering. The end-to-end test runs the full pipeline on the synthetic sample into SQLite. It then checks the merge rules, unique dimension ids, that the weights sum to 1 per movie, the French date labels and that there are no orphan foreign keys.

GitHub Actions (`.github/workflows/ci.yml`) also loads the sample into a real PostgreSQL, runs `sql/reports.sql` and validates the OLAP XML.

---

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `docker compose up` fails with `définir POSTGRES_PASSWORD dans .env` | `.env` is missing. Copy `.env.example` to `.env`. |
| `FileNotFoundError` on `wikipedia-movies.json` | The sources aren't in `PERFILM_DATA_DIR`. See `data/README.md`, or use the sample. |
| `ImportError: pyxlsb` when reading ratings | Reinstall with `uv pip install -e .`, or convert the ratings to `.csv`. |
| Totals in Knowage are much higher than expected | A measure is summing `budget` without `poids`. Use the cube measures, not the raw column. |
| `[pays].[All payss]` not found in MDX | The `pays` hierarchy was renamed. The template relies on Mondrian's default all-member name. |
| `IMDb movies.csv` missing | Optional. The pipeline logs a warning and skips the IMDb fallback. |

---

## Data credits

Movie data comes from Wikipedia (CC BY-SA), *The Movies Dataset* on Kaggle (TMDB metadata and MovieLens ratings, © GroupLens) and the *IMDb movies extensive dataset* on Kaggle. The source files are not included in this repository. Third-party data keeps its own licence and is not covered by the notice below.

---

## License

**Copyright © 2026 dottachin. All rights reserved.**

PerFilm is proprietary software. The source code is public **only so it can be viewed** as part of a portfolio. It is **not** open source.

Without prior written permission, you may not:

- copy or download the code, in whole or in part
- use, run, deploy or host it
- modify it or build derivative works from it
- distribute, sublicense or sell it
- use it to train AI models or to build competing products

The name "PerFilm" and its logo are also not licensed for use. Read the full terms in [LICENSE](LICENSE).

For licensing or other inquiries, contact me through [my GitHub profile](https://github.com/dottachin).
