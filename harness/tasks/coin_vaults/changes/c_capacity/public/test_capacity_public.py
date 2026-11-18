"""Public checks for the c_capacity change (validation_rule). Shown to the
editor, never to the writer.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from vaults import VaultFull, Vaults


@pytest.fixture
def vaults():
    v = Vaults()
    v.add_vault("till", capacity=10)
    v.add_vault("safe")
    return v


def test_capacity_is_reported(vaults):
    assert vaults.get_capacity("till") == 10
    assert vaults.get_capacity("safe") is None


def test_a_deposit_may_fill_a_vault_exactly(vaults):
    vaults.deposit("till", 50, 6)
    vaults.deposit("till", 20, 4)
    assert vaults.get_count("till", 20) == 4


def test_a_deposit_over_the_capacity_raises(vaults):
    vaults.deposit("till", 50, 6)
    with pytest.raises(VaultFull):
        vaults.deposit("till", 20, 5)
    assert vaults.get_denominations("till") == [50]
