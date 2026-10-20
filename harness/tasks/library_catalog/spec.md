# Library catalog

Write a module `library.py` that tracks a library's books, available copies,
and active loans.

## Interface

```python
class Book:
    isbn: str
    title: str
    author: str
    total_copies: int
    available_copies: int


class LibraryCatalog:
    def __init__(self): ...
    def add_book(self, isbn: str, title: str, author: str, copies: int = 1) -> None: ...
    def checkout(self, isbn: str, borrower_id: str) -> bool: ...
    def return_book(self, isbn: str, borrower_id: str) -> bool: ...
```

## Books

- `add_book` creates a new book with the given metadata and copy counts.
- `copies` must be a positive integer. Otherwise, raise `ValueError` and
  leave the catalog unchanged.
- Adding an ISBN already in the catalog adds the copies to both its
  `total_copies` and `available_copies`; it does not replace the original
  title or author.

## Loans

- `checkout` returns `False` if the ISBN is unknown or has no available copies.
- A successful checkout decreases `available_copies` by one and records the
  borrower as having an active loan.
- `return_book` succeeds only for an active loan matching both the ISBN and
  borrower. It removes that loan and increases `available_copies` by one.
  Otherwise it returns `False` and changes nothing.
- `available_copies` never exceeds `total_copies` or falls below zero.

## Unspecified behavior

Behavior not described here is unspecified. This includes ISBN and borrower
identifier validation, the order of loans, whether callers may modify public
attributes, and thread safety.
