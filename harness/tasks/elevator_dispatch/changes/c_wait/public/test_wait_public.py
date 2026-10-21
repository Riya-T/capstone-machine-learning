"""Public checks for the c_wait change (wait statistics).
Shown to the editor, never to the writer.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_wait/public/test_wait_public.py
"""

from elevators import Building


def test_wait_getting_in_at_the_next_stop_is_a_wait_of_one():
    b = Building(5)
    b.add_car("east")
    b.call("ann", 2, 4)
    b.move_car("east", 2)
    assert b.get_clock() == 1
    assert b.get_wait("ann") == 1
    assert b.get_longest_wait() == 1
    assert b.get_total_wait("east") == 1


def test_wait_grows_with_every_move_before_boarding():
    b = Building(5)
    b.add_car("east")
    b.call("ann", 3, 0)
    b.move_car("east", 1)
    b.move_car("east", 2)
    b.move_car("east", 3)
    assert b.get_clock() == 3
    assert b.get_wait("ann") == 3
