"""Hidden tests for the c_loan_log change (a library-wide, searchable log of
loans). Never shown to the writer or the editor.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest changes/c_loan_log/private/test_loan_log_new.py
"""

import pytest
from library import Library, LibraryError


@pytest.fixture
def library():
    lib = Library()
    lib.add_book("978-1", copies=2)
    lib.add_book("978-2")
    lib.add_book("978-3")
    return lib


@pytest.fixture
def busy(library):
    library.check_out("978-1", "ana")
    library.check_out("978-2", "ben")
    library.return_book("978-1", "ana")
    library.check_out("978-1", "ben")
    library.check_out("978-3", "ana")
    library.return_book("978-2", "ben")
    library.check_out("978-1", "cy")
    return library


def test_the_log_interleaves_books_in_the_order_of_the_calls(busy):
    assert busy.get_log() == [
        ("check_out", "978-1", "ana"),
        ("check_out", "978-2", "ben"),
        ("return", "978-1", "ana"),
        ("check_out", "978-1", "ben"),
        ("check_out", "978-3", "ana"),
        ("return", "978-2", "ben"),
        ("check_out", "978-1", "cy"),
    ]


def test_a_library_without_loans_has_an_empty_log(library):
    assert library.get_log() == []
    assert Library().get_log() == []


def test_searching_by_borrower_covers_every_book_and_past_loans(busy):
    assert busy.get_log(borrower="ana") == [
        ("check_out", "978-1", "ana"),
        ("return", "978-1", "ana"),
        ("check_out", "978-3", "ana"),
    ]
    assert busy.get_log(borrower="ben") == [
        ("check_out", "978-2", "ben"),
        ("check_out", "978-1", "ben"),
        ("return", "978-2", "ben"),
    ]
    assert busy.get_log(borrower="zed") == []


def test_searching_by_isbn_gives_that_book_only(busy):
    assert busy.get_log(isbn="978-1") == [
        ("check_out", "978-1", "ana"),
        ("return", "978-1", "ana"),
        ("check_out", "978-1", "ben"),
        ("check_out", "978-1", "cy"),
    ]
    for isbn in busy.get_books():
        entries = busy.get_log(isbn=isbn)
        assert [(action, who) for action, _, who in entries] == busy.get_history(isbn)


def test_both_filters_together_match_both(busy):
    assert busy.get_log(borrower="ben", isbn="978-2") == [
        ("check_out", "978-2", "ben"),
        ("return", "978-2", "ben"),
    ]
    assert busy.get_log(isbn="978-1", borrower="ana") == [
        ("check_out", "978-1", "ana"),
        ("return", "978-1", "ana"),
    ]
    assert busy.get_log(borrower="cy", isbn="978-3") == []


def test_added_copies_and_failed_calls_add_nothing_to_the_log(library):
    library.check_out("978-2", "ana")
    for call in (
        lambda: library.check_out("978-2", "ben"),
        lambda: library.return_book("978-2", "ben"),
        lambda: library.return_book("978-1", "ana"),
        lambda: library.check_out("978-9", "ana"),
        lambda: library.check_out("978-1", ""),
        lambda: library.add_book("978-1", copies=0),
    ):
        with pytest.raises((KeyError, ValueError, LibraryError)):
            call()
    library.add_book("978-2", copies=2)
    library.add_book("978-4")
    assert library.get_log() == [("check_out", "978-2", "ana")]


@pytest.mark.parametrize("isbn", ["978-9", "", 1])
def test_an_isbn_filter_not_in_the_catalog_raises_key_error(busy, isbn):
    with pytest.raises(KeyError):
        busy.get_log(isbn=isbn)


@pytest.mark.parametrize("borrower", ["", 5])
def test_an_invalid_borrower_filter_raises_value_error(busy, borrower):
    with pytest.raises(ValueError):
        busy.get_log(borrower=borrower)
    with pytest.raises(ValueError):
        busy.get_log(borrower=borrower, isbn="978-1")


def test_an_isbn_filter_not_in_the_catalog_is_reported_before_a_bad_borrower(busy):
    with pytest.raises(KeyError):
        busy.get_log(borrower="", isbn="978-9")


def test_reading_the_log_changes_nothing(busy):
    first = busy.get_log()
    busy.get_log(borrower="ana")
    busy.get_log(isbn="978-1")
    assert busy.get_log() == first
    assert busy.get_loans("ben") == ["978-1"]
    assert busy.get_available("978-1") == 0
