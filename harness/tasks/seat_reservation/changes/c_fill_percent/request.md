Make the 70 % fill rule in `seats.py` adjustable, for the whole planner and
for single coaches. Some operators allow fuller coaches on short trips, and
some coaches must keep more seats free.

- `SeatPlanner` takes a new keyword argument `fill_percent=70`. It must be
  an `int` from 1 to 100; anything else raises `ValueError`.
- `add_coach` takes a new keyword argument `fill_percent=None`. `None`
  means the coach uses the planner's percentage. Any other value must be an
  `int` from 1 to 100; anything else raises `ValueError` and no coach is
  added.
- A coach's limit is now `seats * fill_percent // 100`, using that coach's
  percentage. A coach with 10 seats and a percentage of 100 takes 10
  passengers; with 25 it takes 2. `reserve`, `move` and `get_available` all
  use this limit.
- Add `SeatPlanner.get_fill_percent(coach_id) -> int`, which returns the
  coach's current percentage.
- Add `SeatPlanner.set_fill_percent(coach_id, fill_percent)`, which replaces
  the coach's percentage. It raises `KeyError` for a coach that was not
  added, `ValueError` for an invalid percentage, and `ReservationError` if
  the percentage is valid but the coach already has more reserved seats
  than the new limit allows. In each case nothing changes. Lowering the
  limit to exactly the number of reserved seats is allowed.
- `get_fill_percent` raises `KeyError` for a coach that was not added.

Which error is raised when one call has several of these problems (for
example a coach that was not added and an invalid percentage, or an
invalid percentage for a coach id that was already added) is
unspecified. All existing behavior must keep working.
