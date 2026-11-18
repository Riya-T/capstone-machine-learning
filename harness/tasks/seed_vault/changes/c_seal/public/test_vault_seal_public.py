"""Public checks for the c_seal change (sealed drawers). Shown to the editor,
never to the writer.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seal/public/test_vault_seal_public.py
"""

import pytest
from vault import DrawerSealed, SeedVault


@pytest.fixture
def vault():
    v = SeedVault()
    v.add_drawer("A")
    v.add_drawer("B")
    return v


def test_a_sealed_drawer_refuses_deposits(vault):
    assert vault.get_sealed() == []
    vault.seal("A")
    assert vault.get_sealed() == ["A"]
    with pytest.raises(DrawerSealed):
        vault.deposit("A", "pea", 1)
    assert vault.get_count("A", "pea") == 0
    vault.unseal("A")
    vault.deposit("A", "pea", 1)
    assert vault.get_count("A", "pea") == 1


def test_nothing_can_be_transferred_out_of_a_sealed_drawer(vault):
    vault.deposit("A", "bean", 4)
    vault.seal("A")
    with pytest.raises(DrawerSealed):
        vault.transfer("bean", "A", "B", 2)
    assert vault.get_count("A", "bean") == 4
    assert vault.get_count("B", "bean") == 0
