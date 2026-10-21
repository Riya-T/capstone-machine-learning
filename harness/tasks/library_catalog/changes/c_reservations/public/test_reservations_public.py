"""Public checks for the c_reservations change (a first-come queue for books
with no copy on the shelf). Shown to the editor, never to the writer.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reservations/public/test_reservations_public.py
"""

import pytest
from library import Library, LibraryError


def test_a_returned_copy_goes_to_the_first_reserver():
    lib = Library()
    lib.add_book("978-1")
    lib.check_out("978-1", "ana")
    lib.reserve("978-1", "ben")
    lib.reserve("978-1", "cy")
    assert lib.get_reservations("978-1") == ["ben", "cy"]
    lib.return_book("978-1", "ana")
    assert lib.get_loans("ben") == ["978-1"]
    assert lib.get_reservations("978-1") == ["cy"]
    assert lib.get_available("978-1") == 0


def test_reserving_while_a_copy_is_on_the_shelf_raises():
    lib = Library()
    lib.add_book("978-1")
    with pytest.raises(LibraryError):
        lib.reserve("978-1", "ben")
    assert lib.get_reservations("978-1") == []
