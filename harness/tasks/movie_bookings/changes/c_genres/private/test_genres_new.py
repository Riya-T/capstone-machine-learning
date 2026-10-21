"""Hidden tests for the c_genres change (movie genres). Never shown to the
writer or the editor.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest changes/c_genres/private/test_genres_new.py
"""

import pytest
from bookings import BookingError, BoxOffice


@pytest.fixture
def office():
    bo = BoxOffice()
    bo.add_movie("Dune", genre="scifi")
    bo.add_movie("Heat", genre="crime")
    bo.add_movie("Alien", genre="scifi")
    bo.add_showing("d1", "Dune", 600, 10)
    bo.add_showing("h1", "Heat", 540, 4)
    bo.add_showing("a1", "Alien", 700, 20)
    return bo


def test_each_movie_remembers_its_genre(office):
    assert office.get_genre("Dune") == "scifi"
    assert office.get_genre("Heat") == "crime"
    assert office.get_genre("Alien") == "scifi"


def test_movies_without_a_genre_are_general(office):
    office.add_movie("Up")
    assert office.get_genre("Up") == "general"
    assert office.get_genres() == ["scifi", "crime", "general"]
    assert office.get_movies_in_genre("general") == ["Up"]


def test_genres_are_listed_in_first_use_order_without_repeats(office):
    office.add_movie("Up", genre="family")
    office.add_movie("Se7en", genre="crime")
    assert office.get_genres() == ["scifi", "crime", "family"]


def test_movies_in_a_genre_keep_added_order(office):
    office.add_movie("Se7en", genre="crime")
    assert office.get_movies_in_genre("scifi") == ["Dune", "Alien"]
    assert office.get_movies_in_genre("crime") == ["Heat", "Se7en"]


def test_an_unused_genre_has_no_movies_and_no_seats(office):
    assert office.get_movies_in_genre("comedy") == []
    assert office.get_genre_seats_booked("comedy") == 0
    assert office.get_genres() == ["scifi", "crime"]


def test_seats_booked_are_summed_over_the_genre(office):
    office.book("d1", "ann", 3)
    office.book("a1", "bob", 5)
    office.book("a1", "ann", 2)
    office.book("h1", "cat", 4)
    assert office.get_genre_seats_booked("scifi") == 10
    assert office.get_genre_seats_booked("crime") == 4
    assert office.get_genre_seats_booked("general") == 0


def test_seats_booked_starts_at_zero(office):
    assert office.get_genre_seats_booked("scifi") == 0


def test_a_failed_booking_adds_nothing_to_the_genre_total(office):
    office.book("h1", "ann", 3)
    with pytest.raises(BookingError):
        office.book("h1", "bob", 2)
    assert office.get_genre_seats_booked("crime") == 3


@pytest.mark.parametrize("genre", ["", None, 5])
def test_invalid_genres_are_rejected(office, genre):
    with pytest.raises(ValueError):
        office.add_movie("Up", genre=genre)
    assert office.get_movies() == ["Dune", "Heat", "Alien"]
    assert office.get_genres() == ["scifi", "crime"]


def test_get_genre_of_an_unknown_title_raises_key_error(office):
    with pytest.raises(KeyError):
        office.get_genre("Up")
    with pytest.raises(KeyError):
        office.get_genre(None)


def test_a_bad_title_is_reported_before_a_bad_genre(office):
    with pytest.raises(ValueError):
        office.add_movie("", genre=None)
    assert office.get_genres() == ["scifi", "crime"]


def test_a_bad_genre_is_reported_before_a_repeated_title(office):
    with pytest.raises(ValueError):
        office.add_movie("Dune", genre="")
    assert office.get_genre("Dune") == "scifi"
    with pytest.raises(BookingError):
        office.add_movie("Dune", genre="crime")
    assert office.get_genre("Dune") == "scifi"
    assert office.get_movies_in_genre("crime") == ["Heat"]
