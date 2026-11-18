"""Public checks for the c_many change (several transfers in one call).
Shown to the editor, never to the writer.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest changes/c_many/public/test_vault_many_public.py
"""

import pytest
from vault import NotEnoughSeeds, SeedVault


@pytest.fixture
def vault():
    v = SeedVault()
    for name in ["A", "B", "C"]:
        v.add_drawer(name)
    v.deposit("A", "pea", 5)
    v.deposit("B", "bean", 3)
    return v


def test_transfer_many_makes_every_transfer(vault):
    moved = vault.transfer_many([("pea", "A", "C", 2), ("bean", "B", "C", 3)])
    assert moved == 5
    assert vault.get_count("A", "pea") == 3
    assert vault.get_count("C", "pea") == 2
    assert vault.get_count("C", "bean") == 3


def test_one_failing_transfer_cancels_the_whole_call(vault):
    with pytest.raises(NotEnoughSeeds):
        vault.transfer_many([("pea", "A", "C", 2), ("bean", "B", "C", 9)])
    assert vault.get_count("A", "pea") == 5
    assert vault.get_count("C", "pea") == 0
