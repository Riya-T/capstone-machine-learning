"""Library catalog where a borrower may hold only one copy of each book.

Correct solution for library_catalog after c_one_copy.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from library import Library
    library = Library()
    library.add_book("978-1", copies=2)
    library.check_out("978-1", "ana")
    library.check_out("978-1", "ana")  # raises AlreadyBorrowed
"""


class LibraryError(Exception):
    pass


class NoCopyAvailable(LibraryError):
    pass


class AlreadyBorrowed(LibraryError):
    pass


def check_borrower(borrower):
    if not isinstance(borrower, str) or not borrower:
        raise ValueError(f"borrower must be a non-empty str, got {borrower!r}")


class Library:
    def __init__(self):
        self._available = {}  # isbn -> copies on the shelf, in the order first added
        self._history = {}  # isbn -> list of (action, borrower), oldest first
        self._loans = {}  # borrower -> isbns checked out, oldest first

    def add_book(self, isbn, copies=1):
        if not isinstance(isbn, str) or not isbn:
            raise ValueError("isbn must be a non-empty str")
        if isinstance(copies, bool) or not isinstance(copies, int) or copies <= 0:
            raise ValueError(f"copies must be a positive int, got {copies!r}")
        if isbn not in self._available:
            self._available[isbn] = 0
            self._history[isbn] = []
        self._available[isbn] += copies

    def check_out(self, isbn, borrower):
        self._require(isbn)
        check_borrower(borrower)
        if self._has_copy(borrower, isbn):
            raise AlreadyBorrowed(f"{borrower!r} already has a copy of {isbn!r}")
        if self._available[isbn] == 0:
            raise NoCopyAvailable(f"no copy of {isbn!r} is on the shelf")
        self._available[isbn] -= 1
        self._loans.setdefault(borrower, []).append(isbn)
        self._history[isbn].append(("check_out", borrower))

    def return_book(self, isbn, borrower):
        self._require(isbn)
        check_borrower(borrower)
        if not self._has_copy(borrower, isbn):
            raise LibraryError(f"{borrower!r} has no copy of {isbn!r} checked out")
        self._loans[borrower].remove(isbn)
        self._available[isbn] += 1
        self._history[isbn].append(("return", borrower))

    def get_available(self, isbn):
        self._require(isbn)
        return self._available[isbn]

    def get_loans(self, borrower):
        check_borrower(borrower)
        return list(self._loans.get(borrower, []))

    def get_history(self, isbn):
        self._require(isbn)
        return list(self._history[isbn])

    def get_books(self):
        return list(self._available)

    def _has_copy(self, borrower, isbn):
        return isbn in self._loans.get(borrower, [])

    def _require(self, isbn):
        # Non-str isbns are never stored, so they count as "not in the catalog" too.
        if not isinstance(isbn, str) or isbn not in self._available:
            raise KeyError(isbn)
