Several operators now send commands to the same rovers, and an operator
who plans a drive from an outdated picture of a rover can crash it. Add
version checks to driving in `rovers.py`.

- Add `class VersionConflict(RoverError)` to `rovers.py`.
- Every rover has a version number. It is 1 when the rover lands and goes
  up by 1 with every `drive` call that carries out at least one command.
  A `drive` that carries out nothing (an empty string, or a string whose
  first command is a blocked move) leaves the version as it is, and so
  does a call that raises. Add `RoverFleet.get_version(rover_id) -> int`,
  which raises `KeyError` for an unknown rover.
- `drive` takes a new keyword argument `expected_version=None`. When it is
  not `None` and differs from the rover's current version, `drive` raises
  `VersionConflict` and nothing happens: the rover does not move or turn,
  and its odometer and version stay the same. With `None` no version check
  is done.
- When `drive` has several problems, the first of these is raised:
  `KeyError` for an unknown rover, then `ValueError` for invalid commands,
  then `VersionConflict`.

All existing behavior must keep working.
