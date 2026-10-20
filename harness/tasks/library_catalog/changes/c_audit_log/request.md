Add an audit log to `LibraryCatalog`.

- Expose `audit_log` as a list of event strings, initially empty.
- A successful `add_book` appends `ADDED: <isbn> (+<copies>)`.
- A successful `checkout` appends `CHECKOUT: <isbn> by <borrower_id>`.
- A successful `return_book` appends `RETURN: <isbn> by <borrower_id>`.
- Failed operations do not add events. Events remain in chronological order.
- Adding copies to an existing ISBN records an `ADDED` event just like
  creating a new title.

All existing behavior must keep working.
