# Robot fleet

Write a module `fleet.py` that keeps track of robots on a grid: where each
robot is, which way it faces, and how it moves and turns when it is driven
with command strings.

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
  `FleetError`. An `x` or `y` that is not an `int` raises `ValueError`, and
  so does a heading that is any other letter, such as `"n"` or `"X"`. If
  `add_robot` raises, no robot is added.
- `get_robots()` returns the names of all robots, in the order they were
  added.
- `get_position(name)` returns the robot's `(x, y)` and `get_heading(name)`
  its heading letter.
- Every method that takes a name raises `KeyError` when the name is not a
  robot, including values that are not strings at all, such as `None` or `1`.
- Several robots may stand on the same cell.

## Commands

A command string is a `str` in which every letter is one command. There are
three commands:

- `"M"`: move forward one cell, in the direction the robot faces. Facing
  `"N"` adds 1 to `y`, facing `"S"` subtracts 1 from `y`, facing `"E"` adds
  1 to `x` and facing `"W"` subtracts 1 from `x`. The heading stays the same.
- `"L"`: turn left (counterclockwise) by 90 degrees and stay on the same
  cell: `N → W → S → E → N`.
- `"R"`: turn right (clockwise) by 90 degrees and stay on the same cell:
  `N → E → S → W → N`.

Driving the robots:

- `run(name, commands)` executes the commands on that robot, in order.
- `run_all(commands)` executes the same commands on every robot. With no
  robots it does nothing.
- A command string with any character other than `"M"`, `"L"` and `"R"`,
  such as `"X"`, a lowercase `"m"`, a space or a digit, raises `ValueError`.
  The empty string is valid and does nothing.
- `get_command_count(name)` returns how many commands have been executed on
  that robot so far: one for each letter, whether it came through `run` or
  `run_all`.
- When `run` gets both an unknown robot and invalid commands, it raises
  `KeyError`.

For example:

```python
fleet = RobotFleet()
fleet.add_robot("rover", 0, 0, "N")
fleet.add_robot("scout", 5, -2, "E")

fleet.run("rover", "MMRM")        # move, move, turn right, move
fleet.get_position("rover")       # (1, 2)
fleet.get_heading("rover")        # "E"

fleet.run_all("ML")               # each robot moves, then turns left
fleet.get_position("rover")       # (2, 2), now facing "N"
fleet.get_position("scout")       # (6, -2), now facing "N"
fleet.get_command_count("rover")  # 6
fleet.get_command_count("scout")  # 2
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes:

- names that are not strings passed to `add_robot`, `bool` coordinates, and
  headings that are not a single letter, such as `""`, `"NE"` or `None`;
- which error `add_robot` raises when more than one argument is wrong;
- commands that are not a `str`, such as `None`, `5` or a list;
- how much of a command string with an invalid character is executed before
  the `ValueError`, and whether `run_all` with no robots checks its commands;
- what happens if a returned list is changed, the text of error messages,
  saving the fleet to a file, and use from several threads.
