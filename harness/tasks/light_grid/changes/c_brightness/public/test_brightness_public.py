"""Public checks for the c_brightness change (brightness levels).
Shown to the editor, never to the writer.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_brightness/public/test_brightness_public.py
"""

from lights import LightGrid


def test_brightness_default_is_on_or_off():
    grid = LightGrid(3, 3)
    grid.turn_on(0, 0, 0, 0)
    grid.turn_on(0, 0, 0, 0)
    assert grid.get_brightness(0, 0) == 1
    assert grid.get_total_brightness() == 1


def test_brightness_turn_on_climbs_to_the_maximum():
    grid = LightGrid(3, 3, max_brightness=3)
    levels = []
    for _ in range(4):
        grid.turn_on(1, 1, 1, 1)
        levels.append(grid.get_brightness(1, 1))
    assert levels == [1, 2, 3, 3]


def test_brightness_toggle_goes_to_the_maximum_or_to_zero():
    grid = LightGrid(3, 3, max_brightness=5)
    grid.toggle(0, 0, 1, 0)
    assert grid.get_brightness(0, 0) == 5
    grid.turn_off(0, 0, 0, 0, step=2)
    grid.toggle(0, 0, 1, 0)
    assert grid.get_brightness(0, 0) == 0
    assert grid.get_brightness(1, 0) == 0
