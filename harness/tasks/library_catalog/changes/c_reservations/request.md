Add a FIFO reservation queue for books.

- When a known book has no available copies, `checkout` returns `False` and
  places the borrower in that ISBN's reservation queue.
- A borrower with an active loan or an existing reservation for the ISBN
  cannot be queued a second time.
- When a borrower returns a book, assign that copy to the first borrower in
  the queue, moving that borrower directly to an active loan. If no borrower
  is waiting, increase `available_copies` as usual.
- An unknown ISBN is not added to a reservation queue. A failed return does
  not change the queue or the copy count.

All existing behavior must keep working.
