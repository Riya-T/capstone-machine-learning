Add a library-wide audit log of loans to `library.py`, which staff can
search by borrower and by book.

- Add `Library.get_log(borrower=None, isbn=None) -> list[tuple[str, str, str]]`.
- Called with no arguments, it returns every successful check-out and return
  in the whole library, oldest first, as `("check_out", isbn, borrower)` and
  `("return", isbn, borrower)` tuples. Entries for different books are
  interleaved in the order the calls were made.
- `get_log(borrower=b)` returns only the entries for borrower `b`, including
  books they have since returned. `get_log(isbn=i)` returns only the entries
  for book `i`. With both, it returns the entries that match both. The
  entries stay oldest first. A borrower who has never checked anything out
  gets `[]`.
- `None` means "no filter". `get_log` raises `KeyError` for an `isbn` that is
  not in the catalog, then `ValueError` for a `borrower` that is not a
  non-empty string.
- Adding copies adds nothing to the log, and neither does a call that
  raises.

All existing behavior must keep working.
