"""Public checks for the c_injuries change (injured list). Shown to the
editor, never to the writer.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_injuries/public/test_injury_public.py
"""

from roster import Roster


def test_an_injured_salary_is_off_the_cap():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 60)
    roster.place_on_injured_list("Ada")
    assert roster.is_injured("Ada")
    assert (roster.get_payroll(), roster.get_cap_hit(), roster.get_cap_space()) == (60, 0, 100)


def test_activating_puts_the_salary_back():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 60)
    roster.place_on_injured_list("Ada")
    roster.activate("Ada")
    assert not roster.is_injured("Ada")
    assert roster.get_cap_hit() == 60
