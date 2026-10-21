# Light grid

Write a module `lights.py` that controls a rectangular grid of lights, where
commands switch whole rectangles of lights at once.

## Interface

```python
class LightGrid:
    def __init__(self, width: int, height: int): ...
    def turn_on(self, x1: int, y1: int, x2: int, y2: int) -> None: ...
    def turn_off(self, x1: int, y1: int, x2: int, y2: int) -> None: ...
    def toggle(self, x1: int, y1: int, x2: int, y2: int) -> None: ...
    def is_on(self, x: int, y: int) -> bool: ...
    def get_lit_count(self) -> int: ...
```

## The grid

- `LightGrid(width, height)` makes a grid `width` lights wide and `height`
  lights high. Both must be `int`s that are 1 or more, or `ValueError` is
  raised. Every light starts off.
- A light is named by its column `x` and its row `y`, counting from 0:
  `x` goes from 0 to `width - 1` and `y` from 0 to `height - 1`.
- `is_on(x, y)` returns `True` if that light is on and `False` if it is
  off.
- `get_lit_count()` returns how many lights are on.

## Commands

`turn_on`, `turn_off` and `toggle` each act on the rectangle with corners
`(x1, y1)` and `(x2, y2)`, both corners included. So `turn_on(0, 0, 2, 1)`
acts on 6 lights: columns 0 to 2 of rows 0 and 1, and `turn_on(3, 4, 3, 4)`
acts on the single light `(3, 4)`.

- `turn_on` switches every light in the rectangle on (lights already on
  stay on).
- `turn_off` switches every light in the rectangle off (lights already off
  stay off).
- `toggle` switches every light in the rectangle to the opposite state: on
  lights go off and off lights go on.

## Errors

Every coordinate passed to any method must be an `int` inside the grid, and
for a rectangle `x1` must not be more than `x2` and `y1` must not be more
than `y2`. Anything else raises `ValueError`.

A failed call has no effect: if a method raises, every light is as it was.
Grids do not share lights.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` values passed as sizes or coordinates, the text of error
messages, how the grid is printed, saving the grid to a file, and use from
several threads.
