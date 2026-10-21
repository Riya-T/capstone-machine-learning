Group the dishes in `orders.py` into courses, so the kitchen can see what a
table has ordered for each course.

- `add_dish` takes a new keyword argument `course="main"`. It must be a
  non-empty string, or `ValueError` is raised and the dish is not added.
  Like the other `ValueError` checks, this comes before the duplicate check.
- Add `Restaurant.get_courses() -> list[str]`: every course that at least
  one dish on the menu belongs to, each listed once, in the order the
  courses first appeared on the menu.
- Add `Restaurant.get_course_order(table, course) -> list[tuple[str, int]]`:
  the part of the table's order that belongs to that course, in the same
  form and the same dish order as `get_order`. Dishes of other courses are
  left out; an empty list means nothing of that course is ordered.
- Add `Restaurant.get_course_bill(table, course) -> int`: the sum of
  quantity times price over the dishes of that course in the table's
  order.
- Both new table methods raise `KeyError` for a table that is not open,
  then `KeyError` for a course that no dish on the menu belongs to.

All existing behavior must keep working.
