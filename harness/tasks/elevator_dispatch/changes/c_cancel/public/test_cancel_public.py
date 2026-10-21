"""Public checks for the c_cancel change (cancelling a call).
Shown to the editor, never to the writer.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
"""

from elevators import Building


def test_cancel_a_waiting_passenger_is_not_picked_up():
    b = Building(5)
    b.add_car("east")
    b.call("ann", 2, 4)
    b.call("ben", 2, 5)
    b.cancel_call("ann")
    assert b.get_waiting(2) == ["ben"]
    b.move_car("east", 2)
    assert b.get_riders("east") == ["ben"]
    assert b.get_cancelled() == ["ann"]


def test_cancel_frees_the_id_for_a_new_call():
    b = Building(5)
    b.add_car("east")
    b.call("ann", 2, 4)
    b.cancel_call("ann")
    b.call("ann", 3, 1)
    assert b.get_waiting(3) == ["ann"]
    assert b.get_waiting(2) == []
