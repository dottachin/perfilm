"""PerFilm — application décisionnelle dédiée à l'analyse des performances des films.

Pipeline ETL (Python/pandas) qui fusionne les données Wikipedia, Kaggle (TMDB metadata),
MovieLens (ratings) et IMDb, puis les charge dans un entrepôt PostgreSQL modélisé en étoile,
exploité par un cube ROLAP Mondrian dans la suite BI Knowage.
"""

__version__ = "1.0.0"
