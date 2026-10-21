"""Light grid with brightness levels: each light has a brightness from 0 to
the grid's maximum, and turn_on / turn_off move it by a step.

Correct solution for light_grid after c_brightness.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from lights import LightGrid
    grid = LightGrid(10, 5, max_brightness=4)
    grid.turn_on(0, 0, 4, 1, step=2)
    grid.get_total_brightness()  # 20
"""


def check_at_least_one(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{what} must be an int >= 1, got {value!r}")


class LightGrid:
    def __init__(self, width, height, max_brightness=1):
        check_at_least_one(width, "width")
        check_at_least_one(height, "height")
        check_at_least_one(max_brightness, "max_brightness")
        self._width = width
        self._height = height
        self._max = max_brightness
        self._levels = {}  # (x, y) -> brightness, only for lights above 0

    def turn_on(self, x1, y1, x2, y2, step=1):
        lights = self._rect(x1, y1, x2, y2)
        check_at_least_one(step, "step")
        for light in lights:
            self._set(light, min(self._max, self._level(light) + step))

    def turn_off(self, x1, y1, x2, y2, step=1):
        lights = self._rect(x1, y1, x2, y2)
        check_at_least_one(step, "step")
        for light in lights:
            self._set(light, max(0, self._level(light) - step))

    def toggle(self, x1, y1, x2, y2):
        for light in self._rect(x1, y1, x2, y2):
            self._set(light, self._max if self._level(light) == 0 else 0)

    def is_on(self, x, y):
        self._check_point(x, y)
        return self._level((x, y)) > 0

    def get_lit_count(self):
        return len(self._levels)

    def get_brightness(self, x, y):
        self._check_point(x, y)
        return self._level((x, y))

    def get_total_brightness(self):
        return sum(self._levels.values())

    def _level(self, light):
        return self._levels.get(light, 0)

    def _set(self, light, level):
        if level > 0:
            self._levels[light] = level
        else:
            self._levels.pop(light, None)

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
