"""Construction du schéma en étoile (chapitre III et figures 29 à 32 du rapport).

Dimensions : genre, studio, pays, realisateur, langue, movie, date
Table de faits : fact_movies (mesures : budget, revenue)

Granularité de la table de faits : une ligne par combinaison
film × genre × studio × pays × réalisateur × langue (listes « explosées »).
Un film multi-genres apparaît donc sur plusieurs lignes ; la colonne ``poids``
(= 1 / nombre de lignes du film) permet d'agréger budget et revenu sans double comptage
(les mesures du cube Mondrian utilisent ``budget * poids`` et ``revenue * poids``).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

UNKNOWN = "Inconnu"
UNKNOWN_DATE_ID = 0

COUNTRY_ALIASES = {
    "United States of America": "USA",
    "United Kingdom": "UK",
}

# Repli quand ``spoken_languages`` ne fournit pas le libellé d'une langue originale
DEFAULT_LANGUAGES = {
    "en": "English", "fr": "Français", "es": "Español", "de": "Deutsch", "it": "Italiano",
    "ja": "日本語", "zh": "普通话", "cn": "广州话 / 廣州話", "ko": "한국어/조선말", "ru": "Pусский",
    "hi": "हिन्दी", "pt": "Português", "sv": "svenska", "da": "Dansk", "nl": "Nederlands",
    "ar": "العربية", "he": "עִבְרִית", "no": "Norsk", "fi": "suomi", "pl": "Polski",
}  # fmt: skip

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]  # fmt: skip
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


@dataclass
class StarSchema:
    genre: pd.DataFrame
    studio: pd.DataFrame
    pays: pd.DataFrame
    realisateur: pd.DataFrame
    langue: pd.DataFrame
    movie: pd.DataFrame
    date: pd.DataFrame
    fact_movies: pd.DataFrame

    def dimensions(self) -> dict[str, pd.DataFrame]:
        return {
            "genre": self.genre,
            "studio": self.studio,
            "pays": self.pays,
            "realisateur": self.realisateur,
            "langue": self.langue,
            "movie": self.movie,
            "date": self.date,
        }


def _non_empty(values) -> list[str]:
    if isinstance(values, list):
        items = values
    elif isinstance(values, str) and values.strip():
        items = values.split(",")
    else:
        items = []
    items = [str(v).strip() for v in items if str(v).strip()]
    return items or [UNKNOWN]


def label_dimension(labels: pd.Series, id_col: str, label_col: str) -> pd.DataFrame:
    """Dimension « libellé » : valeurs uniques triées, identifiant entier séquentiel."""
    unique = sorted({str(v).strip() for v in labels.dropna() if str(v).strip()})
    dim = pd.DataFrame({label_col: unique})
    dim.insert(0, id_col, range(1, len(dim) + 1))
    return dim


def build_movie_dimension(movies: pd.DataFrame) -> pd.DataFrame:
    dim = pd.DataFrame(
        {
            "id_movie": movies["imdb_id"],
            "titre": movies["title"].astype(str).str.strip(),
            "titre_original": movies["original_title"].astype(str).str.strip(),
            "duree": movies["runtime"].astype(float),
            "rating": movies["rating_total"].astype(float),
        }
    )
    return dim.drop_duplicates("id_movie").reset_index(drop=True)


def date_id(d: pd.Timestamp) -> int:
    return UNKNOWN_DATE_ID if pd.isna(d) else int(d.strftime("%Y%m%d"))


def build_date_dimension(dates: pd.Series) -> pd.DataFrame:
    """Dimension date avec libellés en français (trimestre, mois, jour de la semaine)."""
    unique = pd.Series(sorted(pd.to_datetime(dates.dropna()).dt.normalize().unique()))
    dim = pd.DataFrame(
        {
            "id_date": unique.map(date_id),
            "date": unique.dt.date,
            "annee": unique.dt.year,
            "trimestre": unique.dt.quarter,
            "libelle_trimestre": "Q" + unique.dt.quarter.astype(str),
            "mois": unique.dt.month,
            "libelle_mois": unique.dt.month.map(lambda m: MOIS[m - 1]),
            "jour_semaine": unique.dt.day_of_week + 1,
            "libelle_jour_semaine": unique.dt.day_of_week.map(lambda d: JOURS[d]),
            "jour": unique.dt.day,
        }
    )
    unknown = pd.DataFrame(
        [
            {
                "id_date": UNKNOWN_DATE_ID,
                "date": None,
                "annee": None,
                "trimestre": None,
                "libelle_trimestre": UNKNOWN,
                "mois": None,
                "libelle_mois": UNKNOWN,
                "jour_semaine": None,
                "libelle_jour_semaine": UNKNOWN,
                "jour": None,
            }
        ]
    )
    dim = pd.concat([unknown, dim], ignore_index=True)
    for column in ("annee", "trimestre", "mois", "jour_semaine", "jour"):
        dim[column] = dim[column].astype("Int64")
    return dim


def build_star_schema(
    movies_with_ratings_df: pd.DataFrame, language_names: dict[str, str] | None = None
) -> StarSchema:
    movies = movies_with_ratings_df.drop_duplicates("imdb_id").reset_index(drop=True)
    language_names = {**DEFAULT_LANGUAGES, **(language_names or {})}

    # --- table de faits « longue » avec les libellés (figure 32) -----------------------
    fact = pd.DataFrame(
        {
            "id_movie": movies["imdb_id"],
            "id_date": movies["release_date"].map(date_id),
            "id_genre": movies["genres"].map(_non_empty),
            "id_studio": movies["production_companies"].map(_non_empty),
            "id_pays": movies["production_countries"].map(
                lambda c: [COUNTRY_ALIASES.get(x, x) for x in _non_empty(c)]
            ),
            "id_realisateur": movies["director"].map(_non_empty),
            "id_langue": movies["original_language"].fillna(UNKNOWN).astype(str).str.strip(),
            "budget": movies["budget"].astype(float),
            "revenue": movies["revenue"].astype(float),
        }
    )
    fact_exploded = fact
    for column in ("id_genre", "id_studio", "id_pays", "id_realisateur"):
        fact_exploded = fact_exploded.explode(column, ignore_index=True)
    fact_exploded = fact_exploded.drop_duplicates(
        subset=["id_movie", "id_genre", "id_studio", "id_pays", "id_realisateur", "id_langue"]
    )

    # --- dimensions « libellé » (figures 29, 30) ---------------------------------------
    genre = label_dimension(fact_exploded["id_genre"], "id_genre", "genre")
    studio = label_dimension(fact_exploded["id_studio"], "id_studio", "studio")
    pays = label_dimension(fact_exploded["id_pays"], "id_pays", "pays")
    realisateur = label_dimension(fact_exploded["id_realisateur"], "id_realisateur", "realisateur")
    langue = label_dimension(fact_exploded["id_langue"], "id_langue", "langue")
    langue["langue_complete"] = langue["langue"].map(lambda c: language_names.get(c, c))

    movie = build_movie_dimension(movies)
    date = build_date_dimension(movies["release_date"])

    # --- remplacement des libellés par les clés étrangères -----------------------------
    for dim, id_col, label_col in (
        (genre, "id_genre", "genre"),
        (studio, "id_studio", "studio"),
        (pays, "id_pays", "pays"),
        (realisateur, "id_realisateur", "realisateur"),
        (langue, "id_langue", "langue"),
    ):
        mapping = dict(zip(dim[label_col], dim[id_col], strict=True))
        fact_exploded[id_col] = fact_exploded[id_col].map(mapping).astype(int)

    fact_exploded["poids"] = 1.0 / fact_exploded.groupby("id_movie")["id_movie"].transform("size")
    fact_movies = fact_exploded.reset_index(drop=True)
    fact_movies.insert(0, "id_fact", range(1, len(fact_movies) + 1))

    return StarSchema(
        genre=genre,
        studio=studio,
        pays=pays,
        realisateur=realisateur,
        langue=langue,
        movie=movie,
        date=date,
        fact_movies=fact_movies,
    )
