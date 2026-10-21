Make the 70 % fill rule in `seats.py` adjustable, for the whole planner and
for single coaches. Some operators allow fuller coaches on short trips, and
some coaches must keep more seats free.

- `SeatPlanner` takes a new keyword argument `fill_percent=70`. It must be
  an `int` from 1 to 100 (not a `bool`); anything else raises `ValueError`.
- `add_coach` takes a new keyword argument `fill_percent=None`. `None`
  means the coach uses the planner's percentage. Any other value must be an
  `int` from 1 to 100 (not a `bool`); anything else raises `ValueError` and
  no coach is added.
- A coach's limit is now `seats * fill_percent // 100`, using that coach's
  percentage. A coach with 10 seats and a percentage of 100 takes 10
  passengers; with 25 it takes 2. `reserve`, `move` and `get_available` all
  use this limit.
- Add `SeatPlanner.get_fill_percent(coach_id) -> int`, which returns the
  coach's current percentage.
- Add `SeatPlanner.set_fill_percent(coach_id, fill_percent)`, which replaces
  the coach's percentage. It raises `KeyError` for a coach that was not
  added, then `ValueError` for an invalid percentage, then
  `ReservationError` if the coach already has more reserved seats than the
  new limit allows. In each case nothing changes. Lowering the limit to
  exactly the number of reserved seats is allowed.
- `get_fill_percent` raises `KeyError` for a coach that was not added.

For `add_coach`, every `ValueError` (id, seats or percentage, in any order)
comes before the `ReservationError` for a coach id that was already added.
All existing behavior must keep working.
