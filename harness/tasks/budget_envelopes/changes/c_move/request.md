Add moving money between envelopes to `envelopes.py`, one move at a time
and several allocations at once.

- Add `Budget.move(from_name, to_name, amount)`: takes `amount` out of
  `from_name` and puts it into `to_name`. It raises `KeyError` when either
  name is not an envelope, `ValueError` for an amount that is not an `int`
  greater than 0, `ValueError` when both names are the same, and
  `NotEnoughMoney` when `from_name` holds less than `amount`. A move does
  not touch the unassigned money.
- Add `Budget.allocate_many(amounts)`: `amounts` maps envelope names to
  amounts, and every amount is taken from the unassigned money in one step.
  Either every envelope receives its amount or none does. The whole mapping
  is checked before anything changes. It raises `KeyError` when any name is
  not an envelope, `ValueError` when any amount is not an `int` greater
  than 0, and `NotEnoughMoney` when the amounts add up to more than the
  unassigned money. An empty mapping is allowed and changes nothing.
- When a call has several of these problems, which error is raised is
  unspecified.
- When a call raises, every balance and the unassigned money are unchanged.

All existing behavior must keep working.
