"""Hidden tests for the c_one_copy change (one copy of a book per borrower).
Never shown to the writer or the editor.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest changes/c_one_copy/private/test_one_copy_new.py
"""

import pytest
from library import AlreadyBorrowed, Library, LibraryError, NoCopyAvailable

BORROWERS = ("ana", "ben", "cy")


@pytest.fixture
def library():
    lib = Library()
    lib.add_book("978-1", copies=3)
    lib.add_book("978-2")
    lib.check_out("978-1", "ana")
    return lib


def state(lib):
    books = {isbn: (lib.get_available(isbn), lib.get_history(isbn)) for isbn in lib.get_books()}
    loans = {b: lib.get_loans(b) for b in BORROWERS}
    return books, loans


def test_a_second_copy_of_a_held_book_is_refused(library):
    before = state(library)
    with pytest.raises(AlreadyBorrowed):
        library.check_out("978-1", "ana")
    assert state(library) == before
    assert library.get_available("978-1") == 2


def test_holding_the_only_copy_is_reported_before_no_copy(library):
    library.check_out("978-2", "ben")
    before = state(library)
    with pytest.raises(AlreadyBorrowed):
        library.check_out("978-2", "ben")
    assert state(library) == before
    with pytest.raises(NoCopyAvailable):
        library.check_out("978-2", "ana")


def test_other_borrowers_may_still_take_copies(library):
    library.check_out("978-1", "ben")
    library.check_out("978-1", "cy")
    assert library.get_available("978-1") == 0
    assert [library.get_loans(b) for b in BORROWERS] == [["978-1"], ["978-1"], ["978-1"]]


def test_the_rule_is_per_book(library):
    library.check_out("978-2", "ana")
    assert library.get_loans("ana") == ["978-1", "978-2"]
    with pytest.raises(AlreadyBorrowed):
        library.check_out("978-2", "ana")


def test_the_book_may_be_borrowed_again_once_returned(library):
    library.return_book("978-1", "ana")
    library.check_out("978-1", "ana")
    assert library.get_loans("ana") == ["978-1"]
    assert library.get_history("978-1") == [
        ("check_out", "ana"),
        ("return", "ana"),
        ("check_out", "ana"),
    ]
    with pytest.raises(AlreadyBorrowed):
        library.check_out("978-1", "ana")


def test_a_refused_check_out_records_no_second_loan(library):
    with pytest.raises(AlreadyBorrowed):
        library.check_out("978-1", "ana")
    library.return_book("978-1", "ana")
    assert library.get_loans("ana") == []
    assert library.get_available("978-1") == 3
    with pytest.raises(LibraryError):
        library.return_book("978-1", "ana")


def test_repeated_refusals_change_nothing(library):
    library.check_out("978-1", "ben")
    before = state(library)
    for _ in range(3):
        with pytest.raises(AlreadyBorrowed):
            library.check_out("978-1", "ana")
        with pytest.raises(AlreadyBorrowed):
            library.check_out("978-1", "ben")
    assert state(library) == before


def test_bad_input_still_comes_first(library):
    with pytest.raises(KeyError):
        library.check_out("978-9", "ana")
    with pytest.raises(ValueError):
        library.check_out("978-1", "")


def test_already_borrowed_is_a_library_error_but_not_no_copy_available():
    assert issubclass(AlreadyBorrowed, LibraryError)
    assert not issubclass(AlreadyBorrowed, NoCopyAvailable)
