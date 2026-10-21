Add spending totals to `envelopes.py`, so the household can see where the
money went.

- Add `Budget.get_spent(name) -> int`: everything spent from the envelope
  so far. Raises `KeyError` for an envelope that does not exist.
- Add `Budget.get_total_spent() -> int`: the sum of `get_spent` over every
  envelope.
- Add `Budget.get_total_income() -> int`: everything added with
  `add_income` so far.
- Add `Budget.get_top_spenders() -> list[str]`: every envelope, the one with
  the most spent first. Envelopes with the same total keep the order they
  were created in. Envelopes that spent nothing are included.
- Only `spend` counts as spending: allocating money, or moving it from one
  envelope to another, does not. A call that raises counts for nothing.

All existing behavior must keep working.
