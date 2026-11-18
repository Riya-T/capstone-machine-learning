Let `blood_bank.py` fill a hospital's order in one call: an order takes
units from several fridges, and either all of it goes out or none of it.

- Add `BloodBank.dispatch(order) -> int`. `order` is a non-empty list of
  `(fridge, blood_type, count)` tuples. `dispatch` takes the units of each
  tuple out of its fridge, as `take(fridge, blood_type, count)` would, one
  tuple after another in the order given, and returns the total number of
  units it took.
- The order succeeds or fails as a whole: if any tuple would make `take`
  raise (a fridge that is not in use, a count of 0 or less, or not enough
  units), `dispatch` raises that same error and changes nothing at all,
  not even for the tuples before it.
- Each tuple sees what the tuples before it took. The same fridge and blood
  type may appear in several tuples: two tuples that each take 3 units of
  `"O-"` from a fridge holding 5 raise `NotEnoughUnits`, while a fridge
  holding 6 gives both and is left with none.
- When several tuples would raise, which error is raised is unspecified. An
  empty order is unspecified.

All existing behavior must keep working.
