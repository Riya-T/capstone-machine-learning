"""Public checks for library.py.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest public/test_library_public.py
"""

import pytest
from library import Library, NoCopyAvailable


@pytest.fixture
def library():
    lib = Library()
    lib.add_book("978-1", copies=2)
    lib.add_book("978-2")
    return lib


def test_check_out_and_return_move_a_copy_off_and_back_on_the_shelf(library):
    library.check_out("978-1", "ana")
    assert library.get_available("978-1") == 1
    library.return_book("978-1", "ana")
    assert library.get_available("978-1") == 2


def test_checking_out_with_no_copy_on_the_shelf_raises(library):
    library.check_out("978-2", "ana")
    with pytest.raises(NoCopyAvailable):
        library.check_out("978-2", "ben")
    assert library.get_available("978-2") == 0
    assert library.get_loans("ben") == []


def test_loans_list_the_books_a_borrower_has_out(library):
    library.check_out("978-2", "ana")
    library.check_out("978-1", "ana")
    assert library.get_loans("ana") == ["978-2", "978-1"]
    assert library.get_loans("ben") == []


def test_history_records_check_outs_and_returns(library):
    library.check_out("978-1", "ana")
    library.check_out("978-1", "ben")
    library.return_book("978-1", "ana")
    assert library.get_history("978-1") == [
        ("check_out", "ana"),
        ("check_out", "ben"),
        ("return", "ana"),
    ]
    assert library.get_history("978-2") == []


def test_adding_copies_again_adds_to_the_same_book(library):
    library.add_book("978-1", copies=3)
    assert library.get_books() == ["978-1", "978-2"]
    assert library.get_available("978-1") == 5


def test_an_isbn_not_in_the_catalog_raises_key_error(library):
    with pytest.raises(KeyError):
        library.get_available("978-9")
