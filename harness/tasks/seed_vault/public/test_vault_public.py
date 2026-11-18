"""Public checks for vault.py.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest public/test_vault_public.py
"""

import pytest
from vault import NotEnoughSeeds, SeedVault


@pytest.fixture
def vault():
    v = SeedVault()
    v.add_drawer("A")
    v.add_drawer("B")
    return v


def test_deposits_and_transfers_change_the_counts(vault):
    vault.deposit("A", "bean", 5)
    vault.deposit("A", "bean", 2)
    vault.transfer("bean", "A", "B", 3)
    assert vault.get_count("A", "bean") == 4
    assert vault.get_count("B", "bean") == 3
    assert vault.get_count("A", "corn") == 0


def test_transferring_more_than_there_are_raises(vault):
    vault.deposit("A", "bean", 5)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer("bean", "A", "B", 6)
    assert vault.get_count("A", "bean") == 5
    assert vault.get_count("B", "bean") == 0


def test_transfer_all_moves_every_variety_and_returns_how_many(vault):
    vault.deposit("A", "pea", 5)
    vault.deposit("A", "bean", 2)
    vault.deposit("B", "pea", 1)
    assert vault.transfer_all("A", "B") == 7
    assert vault.get_count("A", "pea") == 0
    assert vault.get_count("A", "bean") == 0
    assert vault.get_count("B", "pea") == 6
    assert vault.get_count("B", "bean") == 2
    assert vault.get_drawers() == ["A", "B"]


def test_a_retired_drawer_is_gone(vault):
    vault.add_drawer("C")
    vault.deposit("A", "pea", 5)
    vault.deposit("A", "bean", 1)
    assert vault.retire_drawer("A", "C") == 6
    assert vault.get_drawers() == ["B", "C"]
    assert vault.get_count("C", "pea") == 5
    with pytest.raises(KeyError):
        vault.get_count("A", "pea")
    with pytest.raises(KeyError):
        vault.deposit("A", "pea", 1)


def test_retiring_an_empty_drawer_returns_0_and_removes_it(vault):
    assert vault.retire_drawer("B", "A") == 0
    assert vault.get_drawers() == ["A"]
    with pytest.raises(KeyError):
        vault.get_count("B", "pea")
