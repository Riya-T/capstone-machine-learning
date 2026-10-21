"""Public checks for the c_genres change (movie genres). Shown to the editor,
never to the writer.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest changes/c_genres/public/test_genres_public.py
"""

import pytest
from bookings import BoxOffice


def test_movies_are_grouped_by_genre():
    bo = BoxOffice()
    bo.add_movie("Dune", genre="scifi")
    bo.add_movie("Heat", genre="crime")
    bo.add_movie("Alien", genre="scifi")
    assert bo.get_genre("Dune") == "scifi"
    assert bo.get_genres() == ["scifi", "crime"]
    assert bo.get_movies_in_genre("scifi") == ["Dune", "Alien"]
    assert bo.get_movies_in_genre("comedy") == []


def test_booked_seats_add_up_per_genre():
    bo = BoxOffice()
    bo.add_movie("Dune", genre="scifi")
    bo.add_movie("Alien", genre="scifi")
    bo.add_showing("d1", "Dune", 600, 10)
    bo.add_showing("a1", "Alien", 700, 10)
    bo.book("d1", "ann", 3)
    bo.book("a1", "bob", 4)
    assert bo.get_genre_seats_booked("scifi") == 7


def test_the_default_genre_is_general():
    bo = BoxOffice()
    bo.add_movie("Dune")
    assert bo.get_genre("Dune") == "general"
    with pytest.raises(ValueError):
        bo.add_movie("Heat", genre="")
