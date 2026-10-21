Report how far each robot in `fleet.py` has travelled.

- Add `RobotFleet.get_distance_travelled(name) -> int`: the number of
  advance commands executed on the robot so far, each of which moved it one
  cell. Turns add nothing.
- Add `RobotFleet.get_displacement(name) -> int`: the Manhattan distance
  between the robot's current position and the position it was added at,
  `abs(x - start_x) + abs(y - start_y)`.
- Add `RobotFleet.get_visited_cells(name) -> list[tuple[int, int]]`: every
  cell the robot has stood on, in the order it first entered them, starting
  with the cell it was added at. A cell entered again is not listed twice.
- All three raise `KeyError` for a name that is not a robot.
- Only commands that were actually executed count, whether through `run` or
  `run_all`. A call that raised adds nothing.
- A robot that has executed no commands has a distance of 0, a displacement
  of 0 and a visited list holding only its start cell.

All existing behavior must keep working.
