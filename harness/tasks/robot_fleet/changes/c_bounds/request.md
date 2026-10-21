Give the fleet in `fleet.py` optional grid bounds, so robots cannot be
driven off the edge of the grid.

- `RobotFleet` takes two new keyword arguments, `width=None` and
  `height=None`. Each is either `None` (no edge in that direction) or an
  `int` of 1 or more (not a `bool`); anything else raises `ValueError`.
  With a width, a robot's x must stay between 0 and `width - 1`; with a
  height, its y must stay between 0 and `height - 1`.
- Add `RobotFleet.get_bounds() -> tuple`, returning `(width, height)` as
  given to the constructor.
- `add_robot` raises `ValueError` for a start position outside the grid.
  This is checked after all the existing checks.
- `run(name, commands)`: if executing the commands would take the robot
  outside the grid at any step, raise `FleetError`. The robot then does not
  move or turn at all and its command count is unchanged, as if `run` had
  not been called. This holds even when later commands would bring the robot
  back inside.
- `run_all(commands)`: if any robot would leave the grid, raise `FleetError`
  and change nothing: no robot moves or turns and no command count changes,
  not even for robots earlier in the order that could have completed the
  commands.
- In `run` and `run_all`, `KeyError` for an unknown robot and `ValueError`
  for invalid commands are raised before `FleetError` for leaving the grid.
- A fleet created without bounds behaves exactly as before.

All existing behavior must keep working.
