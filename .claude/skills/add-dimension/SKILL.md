---
name: add-dimension
description: Checklist for adding, renaming or changing a dimension (or a dimension attribute or measure) in the PerFilm star schema, so the ETL, SQLAlchemy schema, SQL DDL, Mondrian cube, reports and tests stay in sync. Use for requests like "add an actors dimension", "add a collection/franchise dimension", "add popularity as a measure".
---

# Add or change a dimension in PerFilm

A dimension lives in six places. Update all of them in this order.

1. **Source → consolidated dataframe**: `src/perfilm/transform/kaggle.py`, `wiki.py` or `merge.py`.
   Bring the column into `movies_with_ratings_df`. Multi-valued attributes are Python lists, like `genres`.
   If you merge several sources, add the column to the conflict table in the `merge.py` docstring.
2. **Star schema build**: `src/perfilm/transform/dimensions.py`
   - Add a `StarSchema` field and include it in `dimensions()`.
   - Use `label_dimension(...)` for simple label dimensions. Map missing values with `_non_empty` so they become `Inconnu`.
   - Add the FK column to the fact table. If the attribute is multi-valued, `explode` it and add it to the `drop_duplicates` subset. `poids` is recomputed afterwards, so leave it alone.
   - Add the label-to-id mapping in the FK replacement loop.
3. **SQLAlchemy schema**: `src/perfilm/schema.py`. Add the `Table`, the FK column on `fact_movies`, and the table name in `LOAD_ORDER` before `fact_movies`.
4. **SQL DDL**: `sql/schema.sql`. Add the same table, the FK, the `DROP TABLE` entry and the index.
5. **Cube**: `olap/movies_mondrian_schema.xml`. Add a `<Dimension foreignKey=...>` whose column names match the DDL exactly. A new measure must be weighted by `poids` if it is additive per movie.
6. **Tests and sample**: add values for the new attribute to `src/perfilm/sample_data.py`. Extend `tests/test_pipeline.py` to cover unique ids, no orphan FKs, and one expected label.

Keep French naming (`id_<nom>`, `<nom>`, `libelle_*`), like the existing dimensions.

Then run:

```bash
.venv/bin/pytest && .venv/bin/ruff check . && python3 -c "import xml.dom.minidom as m; m.parse('olap/movies_mondrian_schema.xml')"
```

Update the star schema diagram in `README.md` if the shape changed.
