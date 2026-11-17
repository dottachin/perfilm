import pandas as pd
import pytest
from sqlalchemy import text

from perfilm.config import Sources
from perfilm.load import get_engine
from perfilm.pipeline import run
from perfilm.sample_data import write_sample


@pytest.fixture(scope="module")
def loaded(tmp_path_factory):
    data_dir = write_sample(tmp_path_factory.mktemp("raw"))
    db = tmp_path_factory.mktemp("db") / "movies.db"
    url = f"sqlite:///{db}"
    star = run(Sources(data_dir=data_dir), url)
    return star, get_engine(url)


def test_only_matching_movies_survive_merge(loaded):
    star, _ = loaded
    assert set(star.movie["id_movie"]) == {
        "tt0098987", "tt0099005", "tt0099012", "tt6304162", "tt4468740",
    }  # fmt: skip


def test_dimensions_have_unique_labels_and_ids(loaded):
    star, _ = loaded
    for name, df in star.dimensions().items():
        id_col = df.columns[0]
        assert df[id_col].is_unique, name


def test_fact_weights_sum_to_one_per_movie(loaded):
    star, _ = loaded
    weights = star.fact_movies.groupby("id_movie")["poids"].sum()
    assert weights.round(9).eq(1).all()


def test_harmonisation_rules(loaded):
    star, _ = loaded
    movie = star.movie.set_index("id_movie")
    fact = star.fact_movies.drop_duplicates("id_movie").set_index("id_movie")
    # budget Kaggle prioritaire, revenu Kaggle prioritaire
    assert fact.loc["tt0098987", "budget"] == 49_000_000
    # budget Kaggle à 0 -> repli sur Wikipedia ($12 million)
    assert fact.loc["tt0099012", "budget"] == 12_000_000
    # intervalle « $2–3 million » -> borne haute
    assert fact.loc["tt6304162", "budget"] == 3_000_000
    # titre original non latin conservé, note MovieLens puis IMDb/2
    assert movie.loc["tt6304162", "titre_original"] == "Нелюбовь"
    assert movie.loc["tt6304162", "rating"] == pytest.approx(3.8)
    assert movie.loc["tt0098987", "rating"] == pytest.approx(2.5)


def test_country_aliases_and_language_names(loaded):
    star, _ = loaded
    assert {"USA", "UK", "France", "Russia"} <= set(star.pays["pays"])
    langues = dict(zip(star.langue["langue"], star.langue["langue_complete"], strict=True))
    assert langues["en"] == "English"


def test_date_dimension_labels_in_french(loaded):
    star, _ = loaded
    row = star.date[star.date["id_date"] == 19900711].iloc[0]
    assert (row["annee"], row["libelle_trimestre"], row["libelle_mois"]) == (1990, "Q3", "juillet")
    assert row["libelle_jour_semaine"] == "mercredi"


def test_load_respects_foreign_keys(loaded):
    star, engine = loaded
    with engine.connect() as conn:
        n_fact = conn.execute(text("select count(*) from fact_movies")).scalar()
        orphans = conn.execute(
            text(
                "select count(*) from fact_movies f "
                "left join genre g on g.id_genre = f.id_genre "
                "left join movie m on m.id_movie = f.id_movie "
                "left join date d on d.id_date = f.id_date "
                "where g.id_genre is null or m.id_movie is null or d.id_date is null"
            )
        ).scalar()
    assert n_fact == len(star.fact_movies)
    assert orphans == 0


def test_weighted_budget_is_not_double_counted(loaded):
    _, engine = loaded
    df = pd.read_sql("select id_movie, sum(budget * poids) as b from fact_movies "
                     "group by id_movie", engine)  # fmt: skip
    assert df.set_index("id_movie").loc["tt0098987", "b"] == pytest.approx(49_000_000)
