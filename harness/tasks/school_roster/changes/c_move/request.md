Let `roster.py` move students between grades, several at a time, and cap
how many students a grade can hold.

- `Roster` takes a new keyword argument `cap=None`. When it is not `None`
  it must be an `int` of at least 1; anything else raises `ValueError`. No
  grade may ever hold more than `cap` students; `None` means no limit. Add
  `Roster.get_cap() -> int | None`, which returns it.
- Add `class GradeFull(RosterError)` to `roster.py`. `add_student` raises
  it when the grade already holds `cap` students.
- Add `Roster.move_students(names, grade)`, where `names` is a list of names
  on the roster. Every listed student leaves their current grade and joins
  `grade`. They join at the end of that grade's order, in the order listed,
  so `get_students(grade)` lists them after the students already there, and
  `get_all_students()` lists that grade in the same order. A student listed
  who is already in `grade` keeps their place and is not counted as
  arriving. An empty list is allowed and changes nothing.
- For example, if grade 3 holds `ana` then `cleo`, and `ben` is in grade 5,
  `move_students(["ben", "ana"], 3)` leaves grade 3 as
  `["ana", "cleo", "ben"]`: `ana` keeps her place and only `ben` arrives, so
  the move is allowed even with `cap=3`.
- The move is all or nothing. In each of these cases no student moves:
  `ValueError` for a grade that is not an `int` from 1 to 12; `KeyError`
  for a listed name that is not on the roster (a value that is not a
  string, such as `None`, is not on the roster either); `ValueError` if a
  name is listed more than once; `GradeFull` if the arriving students would
  take the grade above `cap`.
- When one call has several problems and at least one of them comes from
  this change (a full grade, or any problem in `move_students`), which
  error it raises is unspecified.

All existing behavior must keep working.
