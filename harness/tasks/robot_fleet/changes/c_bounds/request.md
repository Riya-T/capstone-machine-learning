Give the fleet in `fleet.py` optional grid bounds, so robots cannot be
driven off the edge of the grid.

- `RobotFleet` takes two new keyword arguments, `width=None` and
  `height=None`. Each is either `None` (no edge in that direction) or an
  `int` of 1 or more; anything else raises `ValueError`.
  With a width, a robot's x must stay between 0 and `width - 1`; with a
  height, its y must stay between 0 and `height - 1`.
- Add `RobotFleet.get_bounds() -> tuple`, returning `(width, height)` as
  given to the constructor.
- `add_robot` raises `ValueError` for a start position outside the grid.
- `run(name, commands)`: if executing the commands would take the robot
  outside the grid at any step, raise `FleetError`. This holds even when
  later commands would bring the robot back inside.
- `run_all(commands)`: if any robot would leave the grid, raise
  `FleetError`, and no robot moves, not even the ones that would stay
  inside. For example, with `width=3`, robot `"a"` at `(0, 0)` and robot
  `"b"` at `(2, 0)`, both facing `"E"`, `run_all("M")` raises `FleetError`
  because `"b"` would leave, and `"a"` is still at `(0, 0)` afterwards.
- From now on, `run` and `run_all` either execute all their commands or
  change nothing. Whenever they raise (`FleetError` for leaving the grid, or
  `KeyError` and `ValueError` as before), no robot moves or turns and no
  command count changes, not even for robots that could have completed the
  commands. This includes a command string with an invalid character late in
  the string: the valid commands before it are not executed either.
- When commands have an invalid character and would also take a robot off
  the grid, whether `ValueError` or `FleetError` is raised is unspecified.
  So is which error `add_robot` raises for a start position outside the
  grid when another argument is also wrong, such as a name already in use.
- Without bounds, robots can go anywhere, as before.

All existing behavior must keep working.
