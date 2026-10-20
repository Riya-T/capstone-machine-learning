Prevent a borrower from checking out multiple active copies of the same ISBN.

- A borrower with an active loan for an ISBN cannot check out another copy of
  that ISBN. `checkout` returns `False` and changes no copy or loan counts.
- Different borrowers may each borrow a copy of the same ISBN when copies
  remain available.
- Once the borrower returns their copy, they may check out that ISBN again.

All existing behavior must keep working.
