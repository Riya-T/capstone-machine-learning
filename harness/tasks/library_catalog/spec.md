# Library catalog

Write a module `library.py` that keeps track of a library's books: how many
copies of each book are on the shelf, which borrowers have copies checked
out, and the history of every book's loans.

## Interface

```python
class LibraryError(Exception): ...


class NoCopyAvailable(LibraryError): ...


class Library:
    def __init__(self): ...
    def add_book(self, isbn: str, copies: int = 1) -> None: ...
    def check_out(self, isbn: str, borrower: str) -> None: ...
    def return_book(self, isbn: str, borrower: str) -> None: ...
    def get_available(self, isbn: str) -> int: ...
    def get_loans(self, borrower: str) -> list[str]: ...
    def get_history(self, isbn: str) -> list[tuple[str, str]]: ...
    def get_books(self) -> list[str]: ...
```

A book is identified by its ISBN and a borrower by an id; both are
non-empty strings. Borrowers are not registered anywhere: any valid id may
check out a book.

## Books

- `add_book(isbn, copies=1)` puts `copies` new copies of the book on the
  shelf. The first call for an ISBN adds the book to the catalog; a later
  call for the same ISBN adds more copies of that book.
- An empty `isbn` raises `ValueError`. `copies` must be an `int` greater
  than 0, or `ValueError` is raised.
- `get_books()` returns the ISBNs in the catalog, in the order they were
  first added.
- `get_available(isbn)` returns the number of copies on the shelf: every
  copy added, minus the copies that are checked out right now.
- Every other method that takes an `isbn` raises `KeyError` for an ISBN that
  is not in the catalog, including values that are not strings at all, such
  as `None` or `1`.

## Loans

- `check_out(isbn, borrower)` lends one copy from the shelf to the borrower.
  If no copy is on the shelf, it raises `NoCopyAvailable`.
- `return_book(isbn, borrower)` puts a copy the borrower has checked out
  back on the shelf. If the borrower has no copy of that book checked out,
  it raises `LibraryError`.
- `get_loans(borrower)` returns the ISBNs the borrower has checked out and
  not returned yet, oldest check-out first. A borrower with nothing checked
  out gets `[]`.
- Every method that takes a `borrower` raises `ValueError` when it is an
  empty string.

## History

`get_history(isbn)` returns every check-out and return of the book, oldest
first, as `(action, borrower)` tuples:

- `("check_out", borrower)` for a check-out;
- `("return", borrower)` for a return.

Adding copies adds nothing to the history.

A failed call has no effect: if a method raises, every shelf count, every
borrower's loans and every history are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes a borrower checking out a second copy of a book they already have
checked out (and what `get_loans` and `return_book` do after that), which
error is raised when a call has several problems, borrowers that are not
strings, ISBNs that are not strings passed to `add_book`, `bool` copy
counts, what happens if a returned list is changed, the text of error
messages, saving the catalog to a file, and use from several threads.
