# Reward Wallet

Implement Wallet in wallet.py. Wallet() starts empty. All state is in memory.
Identifiers are nonempty strings and are compared as written. Amounts are
positive integers (booleans are invalid). Raise ValueError for a bad value,
a duplicate identifier where uniqueness is required, or insufficient credits.
Raise KeyError when a syntactically valid identifier is required to exist
but is absent. Failed calls leave all state unchanged. Exact error text is
unimportant. All return values below are required.

- open_member(member) -> None creates a new member with zero credits.
- balance(member) -> int reads an existing member's balance.
- post(op_id, member, kind, amount) -> None records a credit or debit.
  kind must be "credit" or "debit". op_id is unique across all members.
  Reject any debit that would make the balance negative.
- history(member) -> list[tuple] returns (op_id, kind, amount) for this
  member in posting order, as a fresh list. The tuples contain only values.

For example, open "lee", post ("p1", "lee", "credit", 10) and
("p2", "lee", "debit", 3). Balance is 7 and history is
[("p1", "credit", 10), ("p2", "debit", 3)]. Posting a debit of 8 fails.
