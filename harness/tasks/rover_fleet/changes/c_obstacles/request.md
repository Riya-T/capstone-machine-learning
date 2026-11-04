Orbital photos show rocks on the plateau. Let `rovers.py` mark them as
obstacles that rovers must not land on or drive into.

- Add `RoverFleet.add_obstacle(x, y)`, which marks the cell as an obstacle.
  An `x` or `y` off the plateau raises `ValueError`.
  A cell that is already an obstacle, or where a rover stands, raises
  `RoverError`. Which of the two is raised when both apply is unspecified,
  and a failed call marks nothing.
- Add `RoverFleet.get_obstacles() -> list[tuple[int, int]]`: every
  obstacle cell as `(x, y)`, in the order they were added.
- Landing on an obstacle raises `RoverError` and no rover lands. When such
  a call also has another problem (an invalid argument or a rover id in
  use), which error is raised is unspecified.
- A move onto an obstacle is blocked in the same way as a move onto
  another rover: the rover stays, and that move and the rest of the string
  are not carried out. This also holds for a move that wraps around an
  edge onto an obstacle.
- `get_rover_at` returns `None` for an obstacle cell.

All existing behavior must keep working.
