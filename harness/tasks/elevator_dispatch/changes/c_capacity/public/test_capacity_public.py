"""Public checks for the c_capacity change (adjustable car capacities).
Shown to the editor, never to the writer.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

from elevators import Building


def test_capacity_set_for_the_building_applies_to_its_cars():
    b = Building(5, capacity=2)
    b.add_car("east")
    for name in ["ann", "ben", "cy"]:
        b.call(name, 1, 4)
    b.move_car("east", 1)
    assert b.get_capacity("east") == 2
    assert b.get_riders("east") == ["ann", "ben"]
    assert b.get_waiting(1) == ["cy"]


def test_capacity_of_a_single_car_overrides_the_building():
    b = Building(5)
    b.add_car("freight", capacity=6)
    b.add_car("east")
    for name in ["p1", "p2", "p3", "p4", "p5", "p6"]:
        b.call(name, 0, 3)
    b.move_car("freight", 0)
    assert b.get_riders("freight") == ["p1", "p2", "p3", "p4", "p5", "p6"]
    assert b.get_capacity("east") == 4
