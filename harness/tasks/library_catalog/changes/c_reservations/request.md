Let borrowers in `library.py` reserve a book when no copy of it is on the
shelf. A copy that comes back goes straight to the borrower who has waited
longest.

- Add `Library.reserve(isbn, borrower)`, which puts the borrower at the back
  of the book's queue, and `Library.get_reservations(isbn) -> list[str]`,
  which returns the borrowers waiting for the book, first in line first. A
  book nobody is waiting for has an empty queue. `get_reservations` raises
  `KeyError` for an ISBN that is not in the catalog.
- `reserve` raises the first of these that applies, and then changes
  nothing:
  1. `KeyError` when the ISBN is not in the catalog;
  2. `ValueError` when the borrower is not a valid id;
  3. `AlreadyBorrowed` if the borrower has a copy of the book checked out;
  4. `LibraryError` if the borrower is already waiting for the book, or if
     a copy of it is on the shelf (they should check it out instead).
- When `return_book` takes back a copy while borrowers are waiting, the
  copy is lent to the first of them in the same call and never reaches the
  shelf. As one step: the returner's loan ends, the waiting borrower gets
  the book added to their loans and leaves the queue, and `get_available`
  stays the same. The book's history gets `("return", returner)` followed
  by `("check_out", waiting_borrower)`.
- When `add_book` adds copies of a book that borrowers are waiting for, the
  new copies are lent the same way, one to each waiting borrower in queue
  order, each with its `("check_out", borrower)` history entry. Copies left
  over go on the shelf.
- So while anyone is waiting for a book, no copy of it is on the shelf, and
  `check_out` of that book raises `NoCopyAvailable`, also for the borrowers
  in the queue.
- A call that raises hands nothing over. Reserving adds nothing to the
  history.

All existing behavior must keep working.
