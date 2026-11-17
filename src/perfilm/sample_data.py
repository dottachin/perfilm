"""Génère un petit jeu de données synthétique au format des 4 sources réelles.

Utile pour les tests et pour faire tourner la chaîne complète sans télécharger
les jeux Kaggle/MovieLens (plusieurs centaines de Mo). Les valeurs reprennent
volontairement les formats « sales » rencontrés dans Wikipedia (intervalles,
renvois [1], listes, devises étrangères, etc.).

    python -m perfilm.sample_data data/sample
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

WIKI = [
    {
        "url": "https://en.wikipedia.org/wiki/The_Adventures_of_Ford_Fairlane",
        "year": 1990,
        "imdb_link": "https://www.imdb.com/title/tt0098987/",
        "title": "The Adventures of Ford Fairlane",
        "Directed by": "Renny Harlin",
        "Productioncompany ": "Silver Pictures",
        "Release date": ["July 11, 1990", "(1990-07-11)"],
        "Running time": "102 minutes",
        "Country": "United States",
        "Language": "English",
        "Budget": "$20 million [2]",
        "Box office": "$21.4 million",
    },
    {
        "url": "https://en.wikipedia.org/wiki/Air_America_(film)",
        "year": 1990,
        "imdb_link": "https://www.imdb.com/title/tt0099005/",
        "title": "Air America",
        "Directed by": "Roger Spottiswoode",
        "Productioncompanies ": ["Carolco Pictures", "IndieProd Company"],
        "Release date": "August 10, 1990",
        "Running time": "113 minutes",
        "Country": "United States",
        "Language": "English",
        "Budget": "$35 million",
        "Box office": "$57,718,089",
    },
    {
        "url": "https://en.wikipedia.org/wiki/Alice_(1990_film)",
        "year": 1990,
        "imdb_link": "https://www.imdb.com/title/tt0099012/",
        "title": "Alice",
        "Directed by": "Woody Allen",
        "Produced by": "Robert Greenhut",
        "Release date": "December 25, 1990",
        "Length": "1 hr 42 min",
        "Budget": "$12 million",
        "Box office": "$7.3 million",
    },
    {
        "url": "https://en.wikipedia.org/wiki/Loveless_(film)",
        "year": 2017,
        "imdb_link": "https://www.imdb.com/title/tt6304162/",
        "title": "Loveless",
        "Directed by": "Andrey Zvyagintsev",
        "Russian": "Нелюбовь",
        "Release date": "1 June 2017",
        "Running time": "128 minutes",
        "Country": ["Russia", "France"],
        "Budget": "$2–3 million",
        "Box office": "$4.8 million",
    },
    {
        "url": "https://en.wikipedia.org/wiki/Paddington_2",
        "year": 2017,
        "imdb_link": "https://www.imdb.com/title/tt4468740/",
        "title": "Paddington 2",
        "Directed by": "Paul King",
        "Productioncompanies ": ["Heyday Films", "StudioCanal"],
        "Release date": "10 November 2017",
        "Running time": "104 minutes",
        "Country": ["United Kingdom", "France"],
        "Budget": "$40 million [3] [4]",
        "Box office": "$227.9 million",
    },
    {  # série TV : doit être filtrée
        "url": "https://en.wikipedia.org/wiki/Some_series",
        "imdb_link": "https://www.imdb.com/title/tt0000001/",
        "title": "Some series",
        "Directed by": "Someone",
        "No. of episodes": 10,
    },
    {  # pas de lien IMDb : doit être filtré
        "url": "https://en.wikipedia.org/wiki/No_imdb",
        "title": "No imdb",
        "Directed by": "Someone",
    },
]


def _named(names: list[str]) -> str:
    return str([{"id": i, "name": n} for i, n in enumerate(names, 1)])


def _countries(pairs: list[tuple[str, str]]) -> str:
    return str([{"iso_3166_1": c, "name": n} for c, n in pairs])


def _languages(pairs: list[tuple[str, str]]) -> str:
    return str([{"iso_639_1": c, "name": n} for c, n in pairs])


US = ("US", "United States of America")
KAGGLE = [
    # id, imdb_id, title, original_title, genres, companies, countries, lang, spoken,
    # release_date, budget, revenue, runtime
    (9548, "tt0098987", "The Adventures of Ford Fairlane", "The Adventures of Ford Fairlane",
     ["Action", "Comedy", "Thriller", "Crime", "Mystery"], ["Silver Pictures"], [US], "en",
     [("en", "English")], "1990-07-11", 49000000, 20423389, 104),
    (10164, "tt0099005", "Air America", "Air America", ["Action", "Comedy"],
     ["Carolco Pictures"], [US], "en", [("en", "English"), ("th", "ภาษาไทย")],
     "1990-08-10", 35000000, 33461269, 112),
    (11795, "tt0099012", "Alice", "Alice", ["Comedy", "Drama", "Fantasy", "Romance"],
     ["Orion Pictures"], [US], "en", [("en", "English")], "1990-12-25", 0, 7331647, 102),
    (429200, "tt6304162", "Loveless", "Нелюбовь", ["Drama"], ["Non-Stop Productions"],
     [("RU", "Russia"), ("FR", "France")], "ru", [("ru", "Pусский")],
     "2017-06-01", 0, 0, 128),
    (346648, "tt4468740", "Paddington 2", "Paddington 2", ["Adventure", "Comedy", "Family"],
     ["Heyday Films", "StudioCanal"], [("GB", "United Kingdom"), ("FR", "France")], "en",
     [("en", "English")], "2017-11-09", 40000000, 227900000, 103),
    (1, "tt9999999", "Only in Kaggle", "Only in Kaggle", ["Horror"], [], [US], "en",
     [("en", "English")], "2000-01-01", 1000000, 2000000, 90),
]  # fmt: skip

RATINGS = [
    (1, 9548, 3.0), (2, 9548, 2.0), (1, 10164, 4.0), (3, 11795, 3.5),
    (2, 346648, 4.5), (3, 346648, 5.0), (4, 346648, 4.0),
]  # fmt: skip

IMDB = [
    ("tt0098987", "The Adventures of Ford Fairlane", 6.3, "Renny Harlin"),
    ("tt6304162", "Nelyubov", 7.6, "Andrey Zvyagintsev"),
]


def write_sample(target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    (target / "wikipedia-movies.json").write_text(
        json.dumps(WIKI, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    rows = []
    for (kid, imdb_id, title, orig, genres, comps, countries, lang, spoken,
         release, budget, revenue, runtime) in KAGGLE:  # fmt: skip
        rows.append(
            {
                "adult": "False",
                "budget": budget,
                "genres": _named(genres),
                "id": kid,
                "imdb_id": imdb_id,
                "original_language": lang,
                "original_title": orig,
                "popularity": 1.0,
                "production_companies": _named(comps),
                "production_countries": _countries(countries),
                "release_date": release,
                "revenue": revenue,
                "runtime": runtime,
                "spoken_languages": _languages(spoken),
                "title": title,
                "video": "False",
                "vote_average": 6.0,
                "vote_count": 10,
            }
        )
    # ligne corrompue typique du fichier Kaggle (colonnes décalées)
    rows.append({"adult": " - Written by Ørnås", "id": "1997-08-20", "imdb_id": None})
    pd.DataFrame(rows).to_csv(target / "movies_metadata.csv", index=False)

    pd.DataFrame(
        [(u, m, r, 1_000_000_000 + i) for i, (u, m, r) in enumerate(RATINGS)],
        columns=["userId", "movieId", "rating", "timestamp"],
    ).to_csv(target / "ratings.csv", index=False)

    pd.DataFrame(IMDB, columns=["imdb_title_id", "title", "avg_vote", "director"]).to_csv(
        target / "IMDb movies.csv", index=False
    )
    return target


if __name__ == "__main__":
    out = write_sample(Path(sys.argv[1] if len(sys.argv) > 1 else "data/sample"))
    print(f"Jeu d'échantillon écrit dans {out}")
