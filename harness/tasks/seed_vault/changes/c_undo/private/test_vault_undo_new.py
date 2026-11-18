"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_vault_undo_new.py
"""

import pytest
from vault import NotEnoughSeeds, SeedVault, VaultError

VARIETIES = ["bean", "corn", "flax", "oat", "pea", "rye"]


@pytest.fixture
def vault():
    v = SeedVault()
    for name in ["A", "B", "C"]:
        v.add_drawer(name)
    v.deposit("A", "pea", 5)
    v.deposit("A", "bean", 2)
    v.deposit("A", "corn", 4)
    v.deposit("B", "rye", 3)
    return v


def state(v):
    return [(d, [v.get_count(d, s) for s in VARIETIES]) for d in v.get_drawers()]


# --- simple calls -------------------------------------------------------------


def test_undoing_a_deposit_of_a_new_variety(vault):
    before = state(vault)
    vault.deposit("C", "oat", 2)
    vault.undo()
    assert state(vault) == before
    assert vault.get_count("C", "oat") == 0


def test_undoing_a_deposit_of_more_of_a_variety(vault):
    vault.deposit("A", "bean", 6)
    vault.undo()
    assert vault.get_count("A", "bean") == 2


def test_undoing_a_transfer_restores_both_drawers(vault):
    before = state(vault)
    vault.transfer("pea", "A", "B", 3)
    vault.undo()
    assert state(vault) == before


def test_undoing_a_transfer_of_every_packet_of_a_variety(vault):
    before = state(vault)
    vault.transfer("bean", "A", "B", 2)
    vault.undo()
    assert vault.get_count("A", "bean") == 2
    assert vault.get_count("B", "bean") == 0
    assert state(vault) == before


# --- transfer_all ---------------------------------------------------------------


def test_undoing_a_transfer_all_restores_both_drawers(vault):
    before = state(vault)
    assert vault.transfer_all("A", "B") == 11
    vault.undo()
    assert state(vault) == before


def test_undone_transfer_all_leaves_what_the_receiver_had(vault):
    vault.deposit("B", "corn", 1)
    vault.deposit("B", "pea", 1)
    before = state(vault)
    vault.transfer_all("A", "B")
    vault.undo()
    assert vault.get_count("B", "corn") == 1
    assert vault.get_count("B", "pea") == 1
    assert vault.get_count("B", "rye") == 3
    assert vault.get_count("A", "corn") == 4
    assert state(vault) == before


def test_one_undo_takes_back_the_whole_transfer_all(vault):
    vault.deposit("C", "oat", 1)
    vault.transfer_all("A", "C")
    vault.undo()
    assert vault.get_count("C", "oat") == 1
    assert vault.get_count("A", "pea") == 5
    assert vault.get_count("A", "bean") == 2
    assert vault.get_count("A", "corn") == 4
    vault.undo()
    assert vault.get_count("C", "oat") == 0


# --- retire_drawer --------------------------------------------------------------


def test_undone_retire_brings_the_drawer_back_with_its_packets(vault):
    before = state(vault)
    assert vault.retire_drawer("A", "C") == 11
    vault.undo()
    assert state(vault) == before
    assert vault.get_drawers() == ["A", "B", "C"]
    assert vault.get_count("C", "pea") == 0


def test_undone_retire_puts_the_drawer_back_in_its_place(vault):
    vault.add_drawer("D")
    vault.deposit("D", "corn", 2)
    before = state(vault)
    vault.retire_drawer("B", "D")
    assert vault.get_drawers() == ["A", "C", "D"]
    vault.undo()
    assert vault.get_drawers() == ["A", "B", "C", "D"]
    assert vault.get_count("D", "corn") == 2
    assert vault.get_count("D", "rye") == 0
    assert state(vault) == before


def test_undone_retire_of_the_first_drawer_puts_it_first(vault):
    vault.retire_drawer("A", "B")
    vault.retire_drawer("B", "C")
    assert vault.get_drawers() == ["C"]
    vault.undo()
    assert vault.get_drawers() == ["B", "C"]
    vault.undo()
    assert vault.get_drawers() == ["A", "B", "C"]
    assert vault.get_count("A", "corn") == 4


def test_a_drawer_brought_back_is_in_use_again(vault):
    vault.retire_drawer("A", "C")
    vault.undo()
    vault.deposit("A", "pea", 1)
    assert vault.get_count("A", "pea") == 6
    with pytest.raises(VaultError):
        vault.add_drawer("A")
    assert vault.retire_drawer("A", "B") == 12
    assert vault.get_drawers() == ["B", "C"]


def test_undoing_add_drawer_removes_it_and_frees_the_name(vault):
    vault.add_drawer("D")
    vault.undo()
    assert vault.get_drawers() == ["A", "B", "C"]
    with pytest.raises(KeyError):
        vault.get_count("D", "pea")
    vault.add_drawer("D")
    assert vault.get_drawers() == ["A", "B", "C", "D"]
    assert vault.get_count("D", "pea") == 0


# --- calls that move nothing ----------------------------------------------------


def test_a_transfer_all_of_nothing_is_still_a_call(vault):
    vault.transfer("pea", "A", "B", 2)
    assert vault.transfer_all("C", "A") == 0
    vault.undo()  # the transfer_all, which changed nothing
    assert vault.get_count("B", "pea") == 2
    assert vault.get_drawers() == ["A", "B", "C"]
    vault.undo()  # the transfer
    assert vault.get_count("A", "pea") == 5
    assert vault.get_count("B", "pea") == 0


def test_retiring_an_empty_drawer_can_be_undone(vault):
    vault.deposit("B", "rye", 1)
    assert vault.retire_drawer("C", "B") == 0
    vault.undo()
    assert vault.get_drawers() == ["A", "B", "C"]
    assert vault.get_count("B", "rye") == 4
    vault.undo()
    assert vault.get_count("B", "rye") == 3


# --- what is and is not recorded ------------------------------------------------


def test_each_undo_goes_one_call_further_back():
    v = SeedVault()
    calls = [
        lambda: v.add_drawer("A"),
        lambda: v.add_drawer("B"),
        lambda: v.deposit("A", "pea", 5),
        lambda: v.deposit("A", "bean", 2),
        lambda: v.add_drawer("C"),
        lambda: v.deposit("B", "rye", 4),
        lambda: v.deposit("A", "corn", 3),
        lambda: v.transfer("pea", "A", "B", 5),
        lambda: v.transfer("pea", "B", "A", 2),
        lambda: v.transfer_all("A", "C"),
        lambda: v.retire_drawer("B", "C"),
        lambda: v.add_drawer("D"),
        lambda: v.deposit("D", "oat", 1),
        lambda: v.transfer_all("C", "D"),
        lambda: v.retire_drawer("D", "C"),
    ]
    states = [state(v)]
    for call in calls:
        call()
        states.append(state(v))
    assert v.get_drawers() == ["A", "C"]
    assert state(v)[1] == ("C", [2, 3, 0, 1, 5, 4])
    for expected in reversed(states[:-1]):
        v.undo()
        assert state(v) == expected
    with pytest.raises(VaultError):
        v.undo()
    assert v.get_drawers() == []


def test_failed_calls_are_not_recorded(vault):
    vault.deposit("C", "oat", 2)
    for call in (
        lambda: vault.transfer("pea", "A", "B", 99),
        lambda: vault.transfer("flax", "A", "B", 1),
        lambda: vault.transfer("pea", "A", "Z", 1),
        lambda: vault.transfer_all("A", "Z"),
        lambda: vault.retire_drawer("Z", "A"),
        lambda: vault.add_drawer("A"),
        lambda: vault.deposit("Z", "pea", 1),
        lambda: vault.deposit("A", "pea", 0),
    ):
        with pytest.raises((ValueError, KeyError, VaultError)):
            call()
    vault.undo()  # the oats
    assert vault.get_count("C", "oat") == 0
    assert vault.get_count("A", "pea") == 5


def test_get_calls_are_not_recorded(vault):
    vault.deposit("C", "oat", 2)
    vault.get_count("C", "oat")
    vault.get_drawers()
    vault.undo()
    assert vault.get_count("C", "oat") == 0
    assert vault.get_count("B", "rye") == 3


def test_there_is_no_redo():
    v = SeedVault()
    v.add_drawer("A")
    v.deposit("A", "pea", 3)
    v.undo()
    v.undo()
    assert v.get_drawers() == []
    with pytest.raises(VaultError):
        v.undo()


def test_new_calls_after_an_undo_are_undone_first(vault):
    vault.deposit("C", "oat", 2)
    vault.undo()
    vault.deposit("C", "flax", 1)
    vault.undo()
    assert vault.get_count("C", "flax") == 0
    assert vault.get_count("C", "oat") == 0
    vault.undo()  # the rye deposited in the fixture
    assert vault.get_count("B", "rye") == 0
    assert vault.get_count("A", "pea") == 5


def test_nothing_left_to_undo_raises_and_changes_nothing():
    v = SeedVault()
    with pytest.raises(VaultError):
        v.undo()
    v.add_drawer("A")
    v.undo()
    with pytest.raises(VaultError):
        v.undo()
    assert v.get_drawers() == []
    v.add_drawer("A")
    v.deposit("A", "pea", 1)
    assert v.get_count("A", "pea") == 1


def test_the_whole_fixture_can_be_undone(vault):
    for _ in range(7):
        vault.undo()
    assert vault.get_drawers() == []
    with pytest.raises(VaultError):
        vault.undo()


def test_undo_restores_counts_that_a_later_call_checks(vault):
    vault.transfer("pea", "A", "B", 5)
    vault.undo()
    vault.transfer("pea", "A", "C", 5)
    assert vault.get_count("C", "pea") == 5
    with pytest.raises(NotEnoughSeeds):
        vault.transfer("pea", "A", "B", 1)
