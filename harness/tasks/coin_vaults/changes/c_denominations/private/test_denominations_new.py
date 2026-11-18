"""Hidden tests for the c_denominations change (configuration). Never shown to
the writer or the editor.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_denominations/private/test_denominations_new.py
"""

import pytest
from vaults import NotEnoughCoins, Vaults

STANDARD = [1, 2, 5, 10, 20, 50, 100, 200]


def state(v):
    return [(n, [(d, v.get_count(n, d)) for d in v.get_denominations(n)]) for n in v.get_vaults()]


@pytest.fixture
def dollars():
    v = Vaults(denominations=[100, 1, 25, 5, 10])
    v.add_vault("till")
    v.add_vault("safe")
    v.deposit("till", 25, 8)
    v.deposit("till", 1, 3)
    return v


# --- the setting -------------------------------------------------------------


def test_the_default_is_the_standard_list():
    assert Vaults().get_accepted() == STANDARD
    assert Vaults(denominations=None).get_accepted() == STANDARD


def test_the_default_accepts_every_standard_denomination():
    v = Vaults(denominations=None)
    v.add_vault("till")
    for d in STANDARD:
        v.deposit("till", d, 1)
    assert v.get_denominations("till") == STANDARD
    with pytest.raises(ValueError):
        v.deposit("till", 25, 1)


def test_accepted_denominations_are_listed_smallest_first(dollars):
    assert dollars.get_accepted() == [1, 5, 10, 25, 100]


def test_a_single_denomination_is_enough():
    v = Vaults(denominations=[3])
    v.add_vault("jar")
    v.deposit("jar", 3, 7)
    assert v.get_accepted() == [3]
    assert v.get_count("jar", 3) == 7


@pytest.mark.parametrize("bad", [[], [5, 5], [5, 0], [10, -1], [25, 10, 25]])
def test_invalid_settings_are_rejected(bad):
    with pytest.raises(ValueError):
        Vaults(denominations=bad)


def test_objects_keep_their_own_setting(dollars):
    euros = Vaults()
    euros.add_vault("till")
    euros.deposit("till", 2, 1)
    with pytest.raises(ValueError):
        dollars.deposit("till", 2, 1)
    with pytest.raises(ValueError):
        euros.deposit("till", 25, 1)
    assert dollars.get_accepted() == [1, 5, 10, 25, 100]
    assert euros.get_accepted() == STANDARD


# --- deposits follow the setting ---------------------------------------------


def test_configured_denominations_can_be_deposited(dollars):
    dollars.deposit("safe", 100, 2)
    dollars.deposit("safe", 5, 1)
    assert dollars.get_denominations("safe") == [5, 100]
    assert dollars.get_count("till", 25) == 8


@pytest.mark.parametrize("denomination", [2, 20, 50, 200, 7])
def test_denominations_outside_the_setting_are_rejected(dollars, denomination):
    before = state(dollars)
    with pytest.raises(ValueError):
        dollars.deposit("till", denomination, 1)
    assert state(dollars) == before


def test_counts_must_still_be_greater_than_0(dollars):
    with pytest.raises(ValueError):
        dollars.deposit("till", 25, 0)


# --- everything else works as before -----------------------------------------


def test_withdraw_works_with_configured_denominations(dollars):
    dollars.withdraw("till", 25, 5)
    assert dollars.get_count("till", 25) == 3
    with pytest.raises(NotEnoughCoins):
        dollars.withdraw("till", 1, 4)


def test_consolidate_and_close_work_with_configured_denominations(dollars):
    dollars.add_vault("bank")
    dollars.deposit("bank", 100, 1)
    assert dollars.consolidate("till", "safe") == 11
    assert dollars.get_denominations("safe") == [1, 25]
    assert dollars.close_vault("safe", "bank") == 11
    assert dollars.get_vaults() == ["till", "bank"]
    assert state(dollars) == [("till", []), ("bank", [(1, 3), (25, 8), (100, 1)])]
