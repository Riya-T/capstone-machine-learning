"""Hidden tests for the initial library_catalog spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest private/test_library_initial.py
"""

import pytest
from library import Library, LibraryError, NoCopyAvailable

BORROWERS = ("ana", "ben", "cy")
BAD_COPIES = [0, -2, 1.5, "3", None]
BAD_BORROWERS = [""]  # non-string borrowers are unspecified


@pytest.fixture
def library():
    lib = Library()
    lib.add_book("978-1", copies=2)
    lib.add_book("978-2")
    return lib


def state(lib):
    """Every shelf count, history and loan list, to check that a failed call
    changed nothing."""
    books = {isbn: (lib.get_available(isbn), lib.get_history(isbn)) for isbn in lib.get_books()}
    loans = {b: lib.get_loans(b) for b in BORROWERS}
    return books, loans


# --- books ------------------------------------------------------------------


def test_a_new_book_has_every_copy_on_the_shelf_and_no_history(library):
    assert library.get_available("978-1") == 2
    assert library.get_available("978-2") == 1
    assert library.get_history("978-1") == []


def test_books_are_listed_in_the_order_first_added():
    lib = Library()
    for isbn in ["978-3", "978-1", "978-2"]:
        lib.add_book(isbn)
    lib.add_book("978-3", copies=4)
    assert lib.get_books() == ["978-3", "978-1", "978-2"]


def test_added_copies_join_the_copies_already_there(library):
    library.check_out("978-1", "ana")
    library.add_book("978-1", copies=3)
    assert library.get_available("978-1") == 4
    assert library.get_loans("ana") == ["978-1"]


def test_adding_copies_leaves_the_history_alone(library):
    library.check_out("978-1", "ana")
    library.return_book("978-1", "ana")
    library.add_book("978-1")
    assert library.get_history("978-1") == [("check_out", "ana"), ("return", "ana")]
    assert library.get_available("978-1") == 3


def test_an_empty_isbn_is_rejected():
    lib = Library()
    with pytest.raises(ValueError):
        lib.add_book("")
    assert lib.get_books() == []


@pytest.mark.parametrize("copies", BAD_COPIES)
def test_invalid_copy_counts_are_rejected(library, copies):
    library.check_out("978-1", "ana")
    before = state(library)
    with pytest.raises(ValueError):
        library.add_book("978-1", copies=copies)
    with pytest.raises(ValueError):
        library.add_book("978-3", copies=copies)
    assert state(library) == before
    assert library.get_books() == ["978-1", "978-2"]


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.check_out("978-9", "ana"),
        lambda lib: lib.return_book("978-9", "ana"),
        lambda lib: lib.get_available("978-9"),
        lambda lib: lib.get_history("978-9"),
        lambda lib: lib.check_out(None, "ana"),
        lambda lib: lib.return_book(1, "ana"),
        lambda lib: lib.get_available(None),
        lambda lib: lib.get_history(1),
    ],
)
def test_isbns_not_in_the_catalog_raise_key_error(library, call):
    library.check_out("978-1", "ana")
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before


@pytest.mark.parametrize("borrower", BAD_BORROWERS)
@pytest.mark.parametrize(
    "call",
    [
        lambda lib, b: lib.check_out("978-1", b),
        lambda lib, b: lib.return_book("978-1", b),
        lambda lib, b: lib.get_loans(b),
    ],
    ids=["check_out", "return_book", "get_loans"],
)
def test_invalid_borrowers_are_rejected(library, call, borrower):
    library.check_out("978-1", "ana")
    before = state(library)
    with pytest.raises(ValueError):
        call(library, borrower)
    assert state(library) == before


# --- loans ------------------------------------------------------------------


def test_check_out_takes_one_copy_off_the_shelf(library):
    library.check_out("978-1", "ana")
    assert library.get_available("978-1") == 1
    assert library.get_available("978-2") == 1
    assert library.get_loans("ana") == ["978-1"]


def test_the_last_copy_can_go_out_and_then_none_is_left(library):
    library.check_out("978-1", "ana")
    library.check_out("978-1", "ben")
    assert library.get_available("978-1") == 0
    before = state(library)
    with pytest.raises(NoCopyAvailable):
        library.check_out("978-1", "cy")
    assert state(library) == before


def test_returning_puts_the_copy_back_on_the_shelf(library):
    library.check_out("978-2", "ana")
    library.return_book("978-2", "ana")
    assert library.get_available("978-2") == 1
    assert library.get_loans("ana") == []
    library.check_out("978-2", "ben")
    assert library.get_loans("ben") == ["978-2"]


def test_returning_a_book_the_borrower_does_not_have_is_rejected(library):
    library.check_out("978-1", "ana")
    before = state(library)
    with pytest.raises(LibraryError):
        library.return_book("978-1", "ben")  # ana has it, not ben
    with pytest.raises(LibraryError):
        library.return_book("978-2", "ana")  # ana has a different book
    assert state(library) == before


def test_a_copy_cannot_be_returned_twice(library):
    library.check_out("978-1", "ana")
    library.return_book("978-1", "ana")
    before = state(library)
    with pytest.raises(LibraryError):
        library.return_book("978-1", "ana")
    assert state(library) == before


def test_loans_are_listed_oldest_check_out_first():
    lib = Library()
    for isbn in ["978-1", "978-2", "978-3"]:
        lib.add_book(isbn)
    lib.check_out("978-2", "ana")
    lib.check_out("978-1", "ana")
    lib.check_out("978-3", "ana")
    lib.return_book("978-2", "ana")
    lib.check_out("978-2", "ana")
    assert lib.get_loans("ana") == ["978-1", "978-3", "978-2"]


def test_each_borrower_has_their_own_loans(library):
    library.check_out("978-1", "ana")
    library.check_out("978-2", "ben")
    library.check_out("978-1", "ben")
    assert library.get_loans("ana") == ["978-1"]
    assert library.get_loans("ben") == ["978-2", "978-1"]
    assert library.get_loans("zed") == []


# --- history ----------------------------------------------------------------


def test_history_lists_every_check_out_and_return_oldest_first(library):
    library.check_out("978-1", "ana")
    library.check_out("978-2", "cy")
    library.check_out("978-1", "ben")
    library.return_book("978-1", "ana")
    library.return_book("978-1", "ben")
    library.check_out("978-1", "cy")
    assert library.get_history("978-1") == [
        ("check_out", "ana"),
        ("check_out", "ben"),
        ("return", "ana"),
        ("return", "ben"),
        ("check_out", "cy"),
    ]
    assert library.get_history("978-2") == [("check_out", "cy")]


def test_failed_calls_add_nothing_to_history(library):
    library.check_out("978-2", "ana")
    for call in (
        lambda: library.check_out("978-2", "ben"),
        lambda: library.return_book("978-2", "ben"),
        lambda: library.return_book("978-1", "ana"),
        lambda: library.check_out("978-1", ""),
    ):
        with pytest.raises((ValueError, LibraryError)):
            call()
    assert library.get_history("978-2") == [("check_out", "ana")]
    assert library.get_history("978-1") == []


# --- errors -----------------------------------------------------------------


def test_no_copy_available_is_a_library_error():
    assert issubclass(NoCopyAvailable, LibraryError)


def test_libraries_do_not_share_books():
    first, second = Library(), Library()
    first.add_book("978-1")
    first.check_out("978-1", "ana")
    assert second.get_books() == []
    assert second.get_loans("ana") == []
    second.add_book("978-1")
    assert second.get_available("978-1") == 1
