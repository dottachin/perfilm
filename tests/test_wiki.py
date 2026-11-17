import math

import pandas as pd
import pytest

from perfilm.transform.wiki import (
    clean_movie,
    is_relevant,
    parse_dollars,
    parse_money_column,
    parse_running_time,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("$123.4 million", 123.4e6),
        ("$ 5 millon", 5e6),
        ("$1.2 billion", 1.2e9),
        ("$57,718,089", 57_718_089.0),
        ("$1.234.567", 1_234_567.0),
    ],
)
def test_parse_dollars(raw, expected):
    assert parse_dollars(raw) == pytest.approx(expected)


@pytest.mark.parametrize("raw", [None, 12, "Unknown", "£6,000,000", "19 crore"])
def test_parse_dollars_returns_nan(raw):
    assert math.isnan(parse_dollars(raw))


def test_parse_money_column_handles_ranges_citations_and_lists():
    s = pd.Series(["$2–3 million", "$40 million [3] [4]", ["$34", "million"], None, "HBO"])
    out = parse_money_column(s)
    assert out.iloc[0] == pytest.approx(3e6)
    assert out.iloc[1] == pytest.approx(40e6)
    assert out.iloc[2] == pytest.approx(34e6)
    assert math.isnan(out.iloc[3]) and math.isnan(out.iloc[4])


def test_parse_running_time():
    out = parse_running_time(pd.Series(["102 minutes", "1 hr 42 min", "2h", None]))
    assert out.tolist()[:3] == [102, 102, 120]
    assert math.isnan(out.iloc[3])


def test_clean_movie_pivots_alt_titles_and_renames():
    movie = clean_movie(
        {"title": "X", "Russian": "Икс", "Directed by": "A", "Productioncompany ": "S"}
    )
    assert movie["alt_titles"] == {"Russian": "Икс"}
    assert movie["Director"] == "A"
    assert movie["Production company(s)"] == "S"
    assert "Russian" not in movie and "Directed by" not in movie


def test_is_relevant():
    assert is_relevant({"Directed by": "A", "imdb_link": "x"})
    assert not is_relevant({"Directed by": "A"})
    assert not is_relevant({"Director": "A", "imdb_link": "x", "No. of episodes": 3})
