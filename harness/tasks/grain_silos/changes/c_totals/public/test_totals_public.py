"""Public checks for the c_totals change (derived_value). Shown to the editor,
never to the writer.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_totals/public/test_totals_public.py
"""

from silos import Silos


def make():
    s = Silos()
    s.add_silo("north")
    s.add_silo("south")
    s.load("north", "wheat", 40)
    s.load("north", "barley", 15)
    s.load("south", "wheat", 5)
    return s


def test_get_total_adds_every_grain_in_a_silo():
    s = make()
    assert s.get_total("north") == 55
    assert s.get_total("south") == 5


def test_get_grain_total_adds_a_grain_over_every_silo():
    s = make()
    assert s.get_grain_total("wheat") == 45
    assert s.get_grain_total("barley") == 15
    assert s.get_grain_total("rye") == 0
