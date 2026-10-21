"""Public checks for the c_one_copy change (one copy of a book per borrower).
Shown to the editor, never to the writer.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest changes/c_one_copy/public/test_one_copy_public.py
"""

import pytest
from library import AlreadyBorrowed, Library


def test_checking_out_a_book_already_held_raises():
    lib = Library()
    lib.add_book("978-1", copies=2)
    lib.check_out("978-1", "ana")
    with pytest.raises(AlreadyBorrowed):
        lib.check_out("978-1", "ana")
    assert lib.get_available("978-1") == 1
    assert lib.get_loans("ana") == ["978-1"]


def test_a_returned_book_may_be_checked_out_again():
    lib = Library()
    lib.add_book("978-1")
    lib.check_out("978-1", "ana")
    lib.return_book("978-1", "ana")
    lib.check_out("978-1", "ana")
    assert lib.get_loans("ana") == ["978-1"]
