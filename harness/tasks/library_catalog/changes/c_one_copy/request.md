Stop a borrower in `library.py` from holding two copies of the same book at
once.

- Add `class AlreadyBorrowed(LibraryError)` to `library.py`.
- `check_out(isbn, borrower)` raises `AlreadyBorrowed` when the borrower
  already has a copy of that ISBN checked out and has not returned it.
  Nothing changes: the shelf count, the borrower's loans and the book's
  history stay as they were.
- Other borrowers can still check out copies of that book, the borrower can
  still check out other books, and once the borrower has returned their
  copy they may check the book out again.
- `AlreadyBorrowed` is checked after every `KeyError` and `ValueError` check
  and before `NoCopyAvailable`: a borrower who holds the only copy and asks
  for another one gets `AlreadyBorrowed`.

All existing behavior must keep working.
