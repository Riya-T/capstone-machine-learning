Let `roster.py` move students between grades, several at a time, and cap
how many students a grade can hold.

- `Roster` takes a new keyword argument `cap=None`. When it is not `None`
  it must be an `int` of at least 1 (not a `bool`); anything else raises
  `ValueError`. No grade may ever hold more than `cap` students; `None`
  means no limit. Add `Roster.get_cap() -> int | None`, which returns it.
- Add `class GradeFull(RosterError)` to `roster.py`. `add_student` raises
  it, after its existing checks, when the grade already holds `cap`
  students.
- Add `Roster.move_students(names, grade)`, where `names` is a list of names
  on the roster. Every listed student leaves their current grade and joins
  `grade`. They join at the end of that grade's order, in the order listed,
  so `get_students(grade)` lists them after the students already there and
  `get_all_students()` follows suit. A student listed who is already in
  `grade` keeps their place and is not counted as arriving. An empty list
  is allowed and changes nothing.
- The move is all or nothing. Errors are raised in this order, and in each
  case no student moves: `ValueError` for a grade that is not an `int` from
  1 to 12; `KeyError` for the first listed name that is not on the roster;
  `ValueError` if a name is listed more than once; `GradeFull` if the
  arriving students would take the grade above `cap`.

All existing behavior must keep working.
