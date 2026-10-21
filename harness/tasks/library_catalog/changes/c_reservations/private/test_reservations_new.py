"""Hidden tests for the c_reservations change (a first-come queue for books
with no copy on the shelf). Never shown to the writer or the editor.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reservations/private/test_reservations_new.py
"""

import pytest
from library import AlreadyBorrowed, Library, LibraryError, NoCopyAvailable

BORROWERS = ("ana", "ben", "cy", "dee")


@pytest.fixture
def library():
    lib = Library()
    lib.add_book("978-1")  # its only copy is lent to ana
    lib.add_book("978-2", copies=2)
    lib.check_out("978-1", "ana")
    return lib


def state(lib):
    books = {
        isbn: (lib.get_available(isbn), lib.get_history(isbn), lib.get_reservations(isbn))
        for isbn in lib.get_books()
    }
    loans = {b: lib.get_loans(b) for b in BORROWERS}
    return books, loans


def test_borrowers_wait_in_the_order_they_reserved(library):
    library.reserve("978-1", "ben")
    library.reserve("978-1", "cy")
    assert library.get_reservations("978-1") == ["ben", "cy"]
    assert library.get_reservations("978-2") == []
    assert library.get_available("978-1") == 0
    assert library.get_loans("ben") == []


def test_a_returned_copy_goes_straight_to_the_first_in_line(library):
    library.reserve("978-1", "ben")
    library.reserve("978-1", "cy")
    library.return_book("978-1", "ana")
    assert library.get_loans("ana") == []
    assert library.get_loans("ben") == ["978-1"]
    assert library.get_reservations("978-1") == ["cy"]
    assert library.get_available("978-1") == 0
    assert library.get_history("978-1") == [
        ("check_out", "ana"),
        ("return", "ana"),
        ("check_out", "ben"),
    ]


def test_copies_reach_the_shelf_only_once_the_queue_is_empty(library):
    library.reserve("978-1", "ben")
    library.reserve("978-1", "cy")
    library.return_book("978-1", "ana")
    library.return_book("978-1", "ben")
    assert library.get_loans("cy") == ["978-1"]
    assert library.get_available("978-1") == 0
    library.return_book("978-1", "cy")
    assert library.get_available("978-1") == 1
    assert library.get_reservations("978-1") == []
    assert [library.get_loans(b) for b in BORROWERS] == [[], [], [], []]


def test_added_copies_go_to_waiting_borrowers_first(library):
    for borrower in ("ben", "cy", "dee"):
        library.reserve("978-1", borrower)
    library.add_book("978-1", copies=2)
    assert library.get_loans("ben") == ["978-1"]
    assert library.get_loans("cy") == ["978-1"]
    assert library.get_reservations("978-1") == ["dee"]
    assert library.get_available("978-1") == 0
    library.add_book("978-1", copies=2)
    assert library.get_loans("dee") == ["978-1"]
    assert library.get_reservations("978-1") == []
    assert library.get_available("978-1") == 1
    assert library.get_history("978-1") == [
        ("check_out", "ana"),
        ("check_out", "ben"),
        ("check_out", "cy"),
        ("check_out", "dee"),
    ]


def test_reserving_while_a_copy_is_on_the_shelf_is_refused(library):
    library.check_out("978-2", "ben")  # one copy of 978-2 is still on the shelf
    before = state(library)
    with pytest.raises(LibraryError):
        library.reserve("978-2", "cy")
    assert state(library) == before


def test_reserving_a_book_twice_is_refused(library):
    library.reserve("978-1", "ben")
    before = state(library)
    with pytest.raises(LibraryError):
        library.reserve("978-1", "ben")
    assert state(library) == before


def test_a_borrower_cannot_reserve_a_book_they_have(library):
    library.check_out("978-2", "ben")  # the other copy of 978-2 stays on the shelf
    before = state(library)
    with pytest.raises(AlreadyBorrowed):
        library.reserve("978-1", "ana")
    with pytest.raises(AlreadyBorrowed):  # reported before the copy on the shelf
        library.reserve("978-2", "ben")
    assert state(library) == before


@pytest.mark.parametrize("borrower", ["", None, 7])
def test_invalid_borrowers_cannot_reserve(library, borrower):
    before = state(library)
    with pytest.raises(ValueError):
        library.reserve("978-1", borrower)
    with pytest.raises(ValueError):
        library.reserve("978-2", borrower)  # a copy is on the shelf too
    assert state(library) == before


def test_isbns_not_in_the_catalog_are_reported_first(library):
    with pytest.raises(KeyError):
        library.reserve("978-9", "")
    with pytest.raises(KeyError):
        library.reserve(None, "ben")
    with pytest.raises(KeyError):
        library.get_reservations("978-9")


def test_waiting_borrowers_cannot_jump_the_queue(library):
    library.reserve("978-1", "ben")
    before = state(library)
    with pytest.raises(NoCopyAvailable):
        library.check_out("978-1", "ben")
    with pytest.raises(NoCopyAvailable):
        library.check_out("978-1", "cy")
    assert state(library) == before


def test_a_failed_call_hands_nothing_over(library):
    library.reserve("978-1", "ben")
    before = state(library)
    with pytest.raises(LibraryError):
        library.return_book("978-1", "cy")
    with pytest.raises(ValueError):
        library.return_book("978-1", "")
    with pytest.raises(ValueError):
        library.add_book("978-1", copies=0)
    assert state(library) == before


def test_the_returner_may_queue_again_behind_the_others(library):
    library.reserve("978-1", "ben")
    library.return_book("978-1", "ana")
    library.reserve("978-1", "ana")
    library.reserve("978-1", "cy")
    assert library.get_reservations("978-1") == ["ana", "cy"]
    library.return_book("978-1", "ben")
    assert library.get_loans("ana") == ["978-1"]
    assert library.get_reservations("978-1") == ["cy"]
