"""Public checks for the c_service change (cars out of service).
Shown to the editor, never to the writer.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_service/public/test_service_public.py
"""

import pytest
from elevators import Building, CarOutOfService


def test_service_a_car_out_of_service_cannot_move():
    b = Building(5)
    b.add_car("east")
    b.take_out_of_service("east")
    assert not b.is_in_service("east")
    with pytest.raises(CarOutOfService):
        b.move_car("east", 3)
    assert b.get_car_floor("east") == 0


def test_service_a_returned_car_moves_again():
    b = Building(5)
    b.add_car("east")
    b.add_car("west")
    b.take_out_of_service("east")
    assert b.get_cars_in_service() == ["west"]
    b.return_to_service("east")
    b.move_car("east", 3)
    assert b.get_car_floor("east") == 3
    assert b.get_cars_in_service() == ["east", "west"]
