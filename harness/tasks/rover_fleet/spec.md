# Rover fleet

Write a module `rovers.py` that controls a fleet of rovers exploring a
square plateau. It knows where every rover stands and which way it faces,
drives rovers with strings of commands, and stops a rover before it runs
into another one.

## Interface

```python
class RoverError(Exception): ...


class RoverFleet:
    def __init__(self): ...
    def land(self, rover_id: str, x: int, y: int, facing: str) -> None: ...
    def drive(self, rover_id: str, commands: str) -> None: ...
    def get_location(self, rover_id: str) -> tuple[int, int, str]: ...
    def get_rover_at(self, x: int, y: int) -> str | None: ...
    def get_odometer(self, rover_id: str) -> int: ...
    def get_rovers(self) -> list[str]: ...
```

## The plateau

The plateau is a grid of 10 by 10 cells. A cell is given by two `int`s
`x` and `y`, each from 0 to 9. `x` grows towards the east and `y` towards
the north. The plateau wraps around at its edges: a rover that leaves it
on one side comes back on the opposite side. Moving east from `x = 9`
leads to `x = 0`, moving west from `x = 0` leads to `x = 9`, and the same
holds for `y` going north from 9 or south from 0.

At most one rover stands on a cell.

## Rovers

- `land(rover_id, x, y, facing)` puts a new rover on cell `(x, y)`, facing
  one of the words `"north"`, `"east"`, `"south"` or `"west"`.
- `get_rovers()` returns the ids of all rovers, in the order they landed.
- `get_location(rover_id)` returns `(x, y, facing)` for the rover.
- `get_rover_at(x, y)` returns the id of the rover standing on that cell,
  or `None` if the cell is empty. An `x` or `y` outside 0 to 9 raises
  `ValueError`.
- `get_odometer(rover_id)` returns how many moves (`"F"` and `"B"`
  commands) the rover has carried out since it landed: each move adds 1,
  and turns and blocked moves add nothing. It is not the distance from the
  landing cell: driving `"FFB"` adds 3, although the rover ends one cell
  from where it started.
- Every method that takes a rover id raises `KeyError` when it is not the
  id of a rover, including values that are not strings at all, such as
  `None` or `1`.

When `land` has several problems, the first of these is raised:

1. `ValueError` for an empty rover id;
2. `RoverError` for a rover id that is already in use;
3. `ValueError` for an `x` or `y` outside 0 to 9, or a `facing` that is not
   one of the four words;
4. `RoverError` if another rover already stands on the cell.

## Driving

`drive(rover_id, commands)` carries out the commands in the string one by
one, from left to right. There are four commands:

- `"F"`: move forward one cell, in the direction the rover faces.
- `"B"`: move backward one cell, away from the direction the rover faces.
  The rover keeps facing the same way.
- `"L"`: turn left by a quarter turn (`north` becomes `west`, `west`
  becomes `south`, and so on).
- `"R"`: turn right by a quarter turn (`north` becomes `east`, `east`
  becomes `south`, and so on).

A turn changes only the facing, and the rover keeps its new facing after
the call, also when no move follows. An empty string does nothing.

A move onto a cell where another rover stands is blocked. The rover stays
on the cell it has reached, and that move and every later command in the
same string are skipped. The commands before the blocked move stay done:
the rover does not go back to where it was when the call started. A
blocked move is not an error, so `drive` does not raise. Turns are never
blocked.

A string that holds any character other than `"F"`, `"B"`, `"L"` and `"R"`
(a lowercase letter, a space, a digit, ...) raises `ValueError`. `KeyError`
for an unknown rover is raised before this `ValueError`.

For example:

```python
fleet = RoverFleet()
fleet.land("scout", 2, 2, "north")
fleet.land("digger", 2, 5, "south")

fleet.drive("scout", "FFB")    # to (2, 3), to (2, 4), back to (2, 3)
fleet.get_location("scout")    # (2, 3, "north")
fleet.get_odometer("scout")    # 3: one per move

fleet.drive("scout", "FFRF")   # to (2, 4); the next "F" would go onto digger
fleet.get_location("scout")    # (2, 4, "north"): the first "F" stays done
fleet.get_odometer("scout")    # 4
fleet.get_rover_at(2, 4)       # "scout"
fleet.get_rover_at(2, 3)       # None

fleet.drive("scout", "L")      # a turn on its own
fleet.get_location("scout")    # (2, 4, "west")

fleet.drive("scout", "FFx")    # ValueError: "x" is not a command
```

Apart from the invalid strings above, a failed call has no effect: if a
method raises, every rover's location, facing and odometer is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes:

- what `drive` returns;
- how much of a command string with an invalid character is carried out
  before the `ValueError`;
- commands that are not a `str`, such as `None`, `3` or a list;
- coordinates that are not `int`s, such as `1.0`, `"3"`, `None` or `bool`
  values, and rover ids that are not strings passed to `land`;
- what happens if a returned list is changed, the text of error messages,
  saving the fleet to a file, and use from several threads.
