Add ways in `lights.py` to ask which lights are on in part of the grid.

- Add `LightGrid.get_count_in(x1, y1, x2, y2) -> int`: how many lights are
  on in the rectangle (corners included, as for the commands).
- Add `LightGrid.get_lit_in(x1, y1, x2, y2) -> list[tuple[int, int]]`: the
  `(x, y)` of every light that is on in the rectangle, row by row: smallest
  `y` first, and within a row smallest `x` first.
- Add `LightGrid.get_row_counts() -> list[int]`: for each row, from row 0 to
  the last row, how many lights in it are on.
- The rectangle follows the same rules as for the commands; anything else
  raises `ValueError`. None of these methods change any light.

All existing behavior must keep working.
