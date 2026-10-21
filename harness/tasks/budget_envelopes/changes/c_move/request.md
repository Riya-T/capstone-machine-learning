Add moving money between envelopes to `envelopes.py`, one move at a time
and several allocations at once.

- Add `Budget.move(from_name, to_name, amount)`: takes `amount` out of
  `from_name` and puts it into `to_name`. Errors, in this order: `KeyError`
  for `from_name`, `KeyError` for `to_name`, `ValueError` for an amount that
  is not an `int` greater than 0, `ValueError` when both names are the
  same, `NotEnoughMoney` when `from_name` holds less than `amount`. A move
  does not touch the unassigned money.
- Add `Budget.allocate_many(amounts)`: `amounts` maps envelope names to
  amounts, and every amount is taken from the unassigned money in one step.
  Either every envelope receives its amount or none does. The whole mapping
  is checked before anything changes: `KeyError` for the first name, in
  mapping order, that is not an envelope; then `ValueError` for the first
  amount that is not an `int` greater than 0; then `NotEnoughMoney` when the
  amounts add up to more than the unassigned money. An empty mapping is
  allowed and changes nothing.
- When a call raises, every balance and the unassigned money are unchanged.

All existing behavior must keep working.
