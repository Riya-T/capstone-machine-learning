Mission control wants to know where each rover has been. Add path queries
to `rovers.py`.

- Add `RoverFleet.get_path(rover_id) -> list[tuple[int, int]]`: every cell
  the rover has stood on, as `(x, y)`, oldest first. It starts with the
  landing cell and gets one more entry for every move that was carried
  out, so a cell appears again each time the rover comes back to it.
  Turns and blocked moves add nothing.
- Add `RoverFleet.get_visitors(x, y) -> list[str]`: the ids of every rover
  that has ever stood on the cell, by landing or by moving, each listed
  once, in the order the rovers landed. An `x` or `y` that is not an `int`
  on the plateau raises `ValueError`. A cell no rover has visited gives an
  empty list.
- Add `RoverFleet.get_explored(rover_id) -> int`: how many different cells
  the rover has stood on, its landing cell included.
- `get_path` and `get_explored` raise `KeyError` for an unknown rover.

All existing behavior must keep working.
