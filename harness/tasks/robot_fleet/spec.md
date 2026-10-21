# Robot fleet

Write a module `fleet.py` that keeps track of robots on a grid: where each
robot is, which way it faces, and how to drive it with command strings.

## Interface

```python
class FleetError(Exception): ...


class RobotFleet:
    def __init__(self): ...
    def add_robot(self, name: str, x: int, y: int, heading: str) -> None: ...
    def run(self, name: str, commands: str) -> None: ...
    def run_all(self, commands: str) -> None: ...
    def get_position(self, name: str) -> tuple[int, int]: ...
    def get_heading(self, name: str) -> str: ...
    def get_robots(self) -> list[str]: ...
    def get_command_count(self, name: str) -> int: ...
```

Coordinates are `int` and may be negative; the grid has no edges.

## Robots

- `add_robot(name, x, y, heading)` places a new robot at `(x, y)` facing
  `heading`, which is one of the four letters `"N"`, `"E"`, `"S"` and `"W"`.
  An empty name raises `ValueError`, and a name that is already in use raises
  `FleetError`. An `x` or `y` that is not an `int`, or a heading that is not
  one of the four letters, raises `ValueError`. The name is checked before
  the position and the heading. If `add_robot` raises, no robot is added.
- `get_robots()` returns the names of all robots, in the order they were
  added.
- `get_position(name)` returns the robot's `(x, y)` and `get_heading(name)`
  its heading letter.
- Every method that takes a name raises `KeyError` when the name is not a
  robot, including values that are not strings at all, such as `None` or `1`.
- Several robots may stand on the same cell.

## Commands

A command string is a `str` made of zero or more of these letters:

- `"L"`: turn left (counterclockwise) by 90 degrees: `N → W → S → E → N`.
- `"R"`: turn right (clockwise) by 90 degrees: `N → E → S → W → N`.
- `"A"`: advance one cell in the direction the robot faces: facing `N`
  adds 1 to `y`, `S` subtracts 1 from `y`, `E` adds 1 to `x`, `W` subtracts 1
  from `x`.

- `run(name, commands)` executes the commands on that robot, in order.
- `run_all(commands)` executes the same commands on every robot, in the order
  the robots were added. With no robots it does nothing.
- A command string that is not a `str`, or that contains any other character
  (a lowercase letter, a space, a digit, ...), raises `ValueError`. Nothing
  then changes: no robot moves or turns, and no command count changes, even if
  the string starts with valid letters. An empty string is valid and does
  nothing.
- `get_command_count(name)` returns how many commands have been executed on
  that robot so far. Every letter counts as one command, whether it came
  through `run` or `run_all`.

When `run` has several problems, `KeyError` for an unknown robot is raised
before `ValueError` for the commands.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_robot`, `bool`
coordinates, what happens if a returned list is changed, the text of error
messages, saving the fleet to a file, and use from several threads.
