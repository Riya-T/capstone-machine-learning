"""Public checks for the c_loan_log change (a library-wide, searchable log of
loans). Shown to the editor, never to the writer.

Usage (with library.py importable, e.g. in the sandbox):
    python -m pytest changes/c_loan_log/public/test_loan_log_public.py
"""

from library import Library


def make_library():
    lib = Library()
    lib.add_book("978-1")
    lib.add_book("978-2")
    lib.check_out("978-1", "ana")
    lib.check_out("978-2", "ben")
    lib.return_book("978-1", "ana")
    return lib


def test_the_log_lists_loans_of_every_book_in_call_order():
    assert make_library().get_log() == [
        ("check_out", "978-1", "ana"),
        ("check_out", "978-2", "ben"),
        ("return", "978-1", "ana"),
    ]


def test_the_log_can_be_searched_by_borrower():
    lib = make_library()
    assert lib.get_log(borrower="ana") == [
        ("check_out", "978-1", "ana"),
        ("return", "978-1", "ana"),
    ]
    assert lib.get_log(borrower="cy") == []
