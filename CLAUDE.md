# CLAUDE.md

PerFilm reconstructs a 2021 end-of-studies BI project from its report (French PDF, kept locally in `docs/` and not versioned).
Pipeline: Python ETL (pandas) → PostgreSQL star schema → Mondrian ROLAP cube → Knowage reports.

## Commands

- Install: `uv venv && uv pip install -e ".[dev,explore]"`
- Tests: `.venv/bin/pytest` (end-to-end test runs the full pipeline on synthetic data into SQLite)
- Lint: `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
- Sample run: `python -m perfilm.sample_data data/sample && perfilm --data-dir data/sample --database-url sqlite:///perfilm-demo.db`
- Warehouse: `docker compose up -d warehouse` (needs `.env`, see `.env.example`)

## Conventions

- Domain names stay **in French**, as in the report: tables `genre, studio, pays, realisateur, langue, movie, date, fact_movies`; columns `titre, duree, annee, libelle_mois`. Do not translate them, because the Mondrian schema and the MDX depend on them.
- The warehouse schema is defined twice. Keep these in sync: `src/perfilm/schema.py` (SQLAlchemy) and `sql/schema.sql` (plain DDL). `olap/movies_mondrian_schema.xml` must match both.
- Fact grain is one row per movie × genre × studio × pays × realisateur × langue. Always aggregate money with `budget * poids` / `revenue * poids`. Never plain `SUM(budget)`.
- Missing dimension values map to the `Inconnu` member, and an unknown date maps to `id_date = 0`. Never leave a fact FK null.
- Merge rules (which source wins per column) are documented in the `merge.py` docstring. Update the table there when you change a rule.
- Never hard-code credentials. Use the `PERFILM_DATABASE_URL` and `PERFILM_DATA_DIR` env vars.
- Raw data (`data/raw/`) is large, licensed and git-ignored. Tests use `perfilm.sample_data` only.

## Project agents and skills

- `.claude/agents/etl-engineer.md`: data cleaning, regex parsing, merge and dimension work.
- `.claude/agents/olap-designer.md`: Mondrian schema, MDX, Knowage reports.
- `.claude/skills/run-etl`: run the pipeline locally (sample or real data, SQLite or Postgres).
- `.claude/skills/add-dimension`: checklist for adding or changing a dimension across all layers.
