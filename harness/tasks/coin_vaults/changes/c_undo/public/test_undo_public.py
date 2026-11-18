"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from vaults import VaultError, Vaults


@pytest.fixture
def vaults():
    v = Vaults()
    v.add_vault("till")
    v.add_vault("safe")
    return v


def test_undo_takes_back_the_last_deposit(vaults):
    vaults.deposit("till", 50, 5)
    vaults.deposit("till", 50, 2)
    vaults.undo()
    assert vaults.get_count("till", 50) == 5
    vaults.undo()
    assert vaults.get_denominations("till") == []


def test_undo_takes_back_a_consolidate(vaults):
    vaults.deposit("till", 20, 4)
    assert vaults.consolidate("till", "safe") == 4
    vaults.undo()
    assert vaults.get_count("till", 20) == 4
    assert vaults.get_count("safe", 20) == 0


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(VaultError):
        Vaults().undo()
