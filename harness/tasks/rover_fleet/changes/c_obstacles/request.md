Orbital photos show rocks on the plateau. Let `rovers.py` mark them as
obstacles that rovers must not land on or drive into.

- Add `RoverFleet.add_obstacle(x, y)`, which marks the cell as an obstacle.
  An `x` or `y` that is not an `int` on the plateau raises `ValueError`.
  A cell that is already an obstacle, or where a rover stands, raises
  `RoverError`. `ValueError` comes before `RoverError`, and a failed call
  marks nothing.
- Add `RoverFleet.get_obstacles() -> list[tuple[int, int]]`: every
  obstacle cell as `(x, y)`, in the order they were added.
- Landing on an obstacle raises `RoverError` and no rover lands. It is
  checked at the same point as landing on another rover: after every
  `ValueError` and after the check for a rover id in use.
- A move onto an obstacle is blocked in the same way as a move onto
  another rover: the rover stays, and that move and the rest of the string
  are not carried out. This also holds for a move that wraps around an
  edge onto an obstacle.
- `get_rover_at` returns `None` for an obstacle cell.

All existing behavior must keep working.
