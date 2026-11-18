"""Hidden tests for the c_seal change (sealed drawers). Never shown to the
writer or the editor.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seal/private/test_vault_seal_new.py
"""

import pytest
from vault import DrawerSealed, NotEnoughSeeds, SeedVault, VaultError

VARIETIES = ["bean", "oat", "pea", "rye"]


@pytest.fixture
def vault():
    v = SeedVault()
    for name in ["A", "B", "C"]:
        v.add_drawer(name)
    v.deposit("A", "pea", 5)
    v.deposit("A", "bean", 2)
    v.deposit("B", "rye", 3)
    return v


def state(v):
    return [(d, [v.get_count(d, s) for s in VARIETIES]) for d in v.get_drawers()]


# --- the seal itself ------------------------------------------------------------


def test_new_drawers_are_not_sealed(vault):
    assert vault.get_sealed() == []
    vault.add_drawer("D")
    assert vault.get_sealed() == []
    vault.deposit("D", "oat", 1)
    assert vault.get_count("D", "oat") == 1


def test_sealed_drawers_are_listed_in_drawer_order(vault):
    vault.seal("C")
    vault.seal("A")
    assert vault.get_sealed() == ["A", "C"]
    vault.unseal("A")
    assert vault.get_sealed() == ["C"]


def test_sealing_twice_or_unsealing_an_open_drawer_does_nothing(vault):
    vault.seal("A")
    vault.seal("A")
    assert vault.get_sealed() == ["A"]
    vault.unseal("B")
    assert vault.get_sealed() == ["A"]
    vault.unseal("A")
    assert vault.get_sealed() == []


def test_seal_and_unseal_change_no_counts(vault):
    before = state(vault)
    vault.seal("A")
    vault.seal("B")
    vault.unseal("B")
    assert state(vault) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda v: v.seal("Z"),
        lambda v: v.unseal("Z"),
        lambda v: v.seal("C"),  # retired below
        lambda v: v.unseal("C"),
    ],
)
def test_drawers_not_in_use_raise_key_error(vault, call):
    vault.retire_drawer("C", "A")
    with pytest.raises(KeyError):
        call(vault)


def test_a_retired_drawer_is_no_longer_listed_as_sealed(vault):
    vault.seal("C")
    vault.unseal("C")
    vault.retire_drawer("C", "B")
    vault.seal("B")
    assert vault.get_sealed() == ["B"]


# --- calls refused on a sealed drawer -------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda v: v.deposit("A", "pea", 1),
        lambda v: v.deposit("A", "oat", 1),
        lambda v: v.transfer("pea", "A", "B", 1),
        lambda v: v.transfer("rye", "B", "A", 1),
        lambda v: v.transfer_all("A", "B"),
        lambda v: v.transfer_all("B", "A"),
        lambda v: v.retire_drawer("A", "B"),
        lambda v: v.retire_drawer("B", "A"),
    ],
    ids=[
        "deposit",
        "deposit_new_variety",
        "transfer_out",
        "transfer_in",
        "transfer_all_out",
        "transfer_all_in",
        "retire_sealed",
        "retire_into_sealed",
    ],
)
def test_calls_touching_a_sealed_drawer_raise_and_change_nothing(vault, call):
    vault.seal("A")
    before = state(vault)
    with pytest.raises(DrawerSealed):
        call(vault)
    assert state(vault) == before
    assert vault.get_drawers() == ["A", "B", "C"]
    assert vault.get_sealed() == ["A"]


def test_calls_that_would_move_nothing_are_refused_too(vault):
    vault.seal("C")  # C is empty
    before = state(vault)
    with pytest.raises(DrawerSealed):
        vault.transfer_all("C", "A")
    with pytest.raises(DrawerSealed):
        vault.retire_drawer("C", "A")
    assert state(vault) == before
    assert vault.get_drawers() == ["A", "B", "C"]


def test_a_sealed_drawer_does_not_stop_calls_on_other_drawers(vault):
    vault.seal("C")
    vault.deposit("A", "oat", 1)
    vault.transfer("pea", "A", "B", 2)
    assert vault.transfer_all("B", "A") == 5
    vault.add_drawer("D")
    assert vault.retire_drawer("D", "B") == 0
    assert vault.get_drawers() == ["A", "B", "C"]
    assert state(vault) == [("A", [2, 1, 5, 3]), ("B", [0, 0, 0, 0]), ("C", [0, 0, 0, 0])]


# --- what still works on a sealed drawer ---------------------------------------


def test_getters_and_add_drawer_work_with_sealed_drawers(vault):
    vault.seal("A")
    vault.seal("B")
    assert vault.get_count("A", "pea") == 5
    assert vault.get_count("B", "rye") == 3
    vault.add_drawer("D")
    assert vault.get_drawers() == ["A", "B", "C", "D"]
    assert vault.get_sealed() == ["A", "B"]


def test_unseal_lets_packets_move_again(vault):
    vault.seal("A")
    with pytest.raises(DrawerSealed):
        vault.transfer_all("A", "C")
    vault.unseal("A")
    assert vault.transfer_all("A", "C") == 7
    assert vault.get_count("C", "pea") == 5
    assert vault.get_count("C", "bean") == 2


def test_a_refused_retire_can_be_retried_after_unsealing(vault):
    vault.seal("B")
    with pytest.raises(DrawerSealed):
        vault.retire_drawer("A", "B")
    vault.unseal("B")
    assert vault.retire_drawer("A", "B") == 7
    assert vault.get_drawers() == ["B", "C"]
    assert state(vault)[0] == ("B", [2, 0, 5, 3])


# --- other errors still work ----------------------------------------------------


def test_other_errors_still_come_from_unsealed_drawers(vault):
    vault.seal("C")
    before = state(vault)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer("pea", "A", "B", 6)
    with pytest.raises(ValueError):
        vault.deposit("A", "pea", 0)
    with pytest.raises(KeyError):
        vault.deposit("Z", "pea", 1)
    assert state(vault) == before


def test_drawer_sealed_is_a_vault_error_but_not_not_enough_seeds():
    assert issubclass(DrawerSealed, VaultError)
    assert not issubclass(DrawerSealed, NotEnoughSeeds)
