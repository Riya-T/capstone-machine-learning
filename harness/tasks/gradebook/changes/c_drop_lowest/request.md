Let `gradebook.py` compute totals that leave out a student's lowest scores,
the way a course that "drops the lowest quiz" does.

- Add `Gradebook.get_total_dropping(name, count) -> int`: the student's
  total with their `count` lowest recorded scores left out. `count` must be
  an `int` that is 0 or more (not a `bool`), or `ValueError` is raised. With
  `count=0` the result equals `get_total(name)`. If the student has `count`
  or fewer recorded scores, every score is dropped and the result is 0.
- Add `Gradebook.get_dropped(name, count) -> list[str]`: the titles of the
  assignments that `get_total_dropping(name, count)` leaves out, in the
  order the assignments were added. Only assignments with a recorded score
  can be dropped. The lowest scores are dropped first; among equal scores,
  the assignment that was added earlier is dropped first.
- "Lowest" means the points as they count toward `get_total`, so anything
  that changes how a score counts also changes which scores are dropped.
- Both methods raise `KeyError` for a name that is not a student, then
  `ValueError` for an invalid `count`.

All existing behavior must keep working.
