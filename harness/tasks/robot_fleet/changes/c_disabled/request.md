Let robots in `fleet.py` be disabled, for example while they are charging.

- Add `RobotFleet.disable(name)`, `RobotFleet.enable(name)` and
  `RobotFleet.is_enabled(name) -> bool`. All three raise `KeyError` for a
  name that is not a robot. New robots are enabled. Disabling a disabled
  robot, or enabling an enabled one, does nothing.
- Add `class RobotDisabled(FleetError)` to `fleet.py`.
- `run(name, commands)` on a disabled robot raises `RobotDisabled` and
  changes nothing. It is checked after `KeyError` and `ValueError` and before
  any other `FleetError`.
- `run_all(commands)` drives only the enabled robots; disabled robots keep
  their position, heading and command count. Whether `run_all` raises is
  decided by looking at the enabled robots alone: a disabled robot never
  makes it raise a `FleetError`. Invalid commands still raise `ValueError`,
  even when every robot is disabled.
- Add `RobotFleet.get_enabled_robots() -> list[str]`: the enabled robots in
  the order they were added. `get_robots()` still lists every robot.
- A disabled robot still reports its position, heading and command count,
  and disabling or enabling does not count as a command.

All existing behavior must keep working.
