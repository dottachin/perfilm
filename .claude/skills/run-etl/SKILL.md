---
name: run-etl
description: Run the PerFilm ETL pipeline locally and check the loaded warehouse. Use when asked to run, test end-to-end, demo, or reload the data warehouse, either on the synthetic sample (SQLite, no downloads) or on the real sources in data/raw with PostgreSQL in Docker.
---

# Run the PerFilm ETL

## 1. Environment

```bash
test -x .venv/bin/perfilm || (uv venv && uv pip install -e ".[dev,explore]")
```

## 2a. Sample data on SQLite (fast, no Docker)

```bash
.venv/bin/python -m perfilm.sample_data data/sample
.venv/bin/perfilm --data-dir data/sample --database-url sqlite:///perfilm-demo.db
```

## 2b. Real data on PostgreSQL

1. Check that the sources exist: `ls data/raw`. The list of expected files is in `data/README.md`. If they are missing, tell the user where to download them. Do not fabricate them.
2. `test -f .env || cp .env.example .env`. Ask the user to set the passwords if they are still `change-me`.
3. `docker compose up -d warehouse`, then wait until `docker compose exec warehouse pg_isready -U postgres -d movies` succeeds.
4. `.venv/bin/perfilm` reads `PERFILM_DATA_DIR` and `PERFILM_DATABASE_URL` from `.env`.

Use `--dry-run` to transform without loading. Use `-v` for debug logs.

## 3. Verify

- The log shows a row count per table. `fact_movies` must be at least as large as `movie`.
- Run the report queries:
  - Postgres: `docker compose exec -T warehouse psql -U postgres -d movies < sql/reports.sql`
  - SQLite: run each `SELECT` from `sql/reports.sql` with Python's `sqlite3`
- Sanity checks: no orphan FKs, `poids` sums to 1 per movie, and budgets are in plausible ranges (no values above 1e10).

Report the row counts and anything suspicious. Don't just say "it worked".
