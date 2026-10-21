"""Light grid: a rectangle of lights that commands switch on, off or over,
a whole rectangle of lights at a time.

Planted bug (initial version): is_on does not check its coordinates and
answers False for a light outside the grid. The public checks only pass
bad coordinates to commands, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from lights import LightGrid
    grid = LightGrid(10, 5)
    grid.turn_on(0, 0, 4, 1)
    grid.toggle(2, 0, 2, 4)
"""


def check_size(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{what} must be an int >= 1, got {value!r}")


class LightGrid:
    def __init__(self, width, height):
        check_size(width, "width")
        check_size(height, "height")
        self._width = width
        self._height = height
        self._lit = set()  # (x, y) of every light that is on

    def turn_on(self, x1, y1, x2, y2):
        for light in self._rect(x1, y1, x2, y2):
            self._lit.add(light)

    def turn_off(self, x1, y1, x2, y2):
        for light in self._rect(x1, y1, x2, y2):
            self._lit.discard(light)

    def toggle(self, x1, y1, x2, y2):
        for light in self._rect(x1, y1, x2, y2):
            if light in self._lit:
                self._lit.remove(light)
            else:
                self._lit.add(light)

    def is_on(self, x, y):
        return (x, y) in self._lit

    def get_lit_count(self):
        return len(self._lit)

    def _check_point(self, x, y):
        for value, limit, what in ((x, self._width, "x"), (y, self._height, "y")):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{what} must be an int, got {value!r}")
            if not 0 <= value < limit:
                raise ValueError(f"{what}={value} is outside the grid")

    def _rect(self, x1, y1, x2, y2):
        """Every light in the rectangle, row by row; checks everything first,
        so a bad rectangle changes nothing."""
        self._check_point(x1, y1)
        self._check_point(x2, y2)
        if x1 > x2 or y1 > y2:
            raise ValueError(f"corner ({x1}, {y1}) is past corner ({x2}, {y2})")
        return [(x, y) for y in range(y1, y2 + 1) for x in range(x1, x2 + 1)]
