"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_vault_undo_public.py
"""

import pytest
from vault import SeedVault, VaultError


@pytest.fixture
def vault():
    v = SeedVault()
    v.add_drawer("A")
    v.add_drawer("B")
    return v


def test_undo_takes_back_the_last_deposit(vault):
    vault.deposit("A", "pea", 5)
    vault.deposit("A", "pea", 2)
    vault.undo()
    assert vault.get_count("A", "pea") == 5
    vault.undo()
    assert vault.get_count("A", "pea") == 0


def test_undo_takes_back_a_transfer(vault):
    vault.deposit("A", "bean", 4)
    vault.transfer("bean", "A", "B", 3)
    vault.undo()
    assert vault.get_count("A", "bean") == 4
    assert vault.get_count("B", "bean") == 0


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(VaultError):
        SeedVault().undo()
