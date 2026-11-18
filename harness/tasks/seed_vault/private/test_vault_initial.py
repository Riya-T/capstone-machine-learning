"""Hidden tests for the initial seed_vault spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest private/test_vault_initial.py
"""

import pytest
from vault import NotEnoughSeeds, SeedVault, VaultError

VARIETIES = ["bean", "corn", "oat", "pea", "rye"]


@pytest.fixture
def vault():
    v = SeedVault()
    for name in ["A", "B", "C"]:
        v.add_drawer(name)
    v.deposit("A", "pea", 5)
    v.deposit("A", "bean", 2)
    v.deposit("A", "corn", 4)
    return v


def state(v):
    """Every drawer in order with the count of each variety, to check that a
    failed call changed nothing."""
    return [(d, [v.get_count(d, s) for s in VARIETIES]) for d in v.get_drawers()]


# --- drawers ------------------------------------------------------------------


def test_a_new_drawer_is_empty():
    v = SeedVault()
    v.add_drawer("A")
    assert v.get_count("A", "pea") == 0
    assert v.get_drawers() == ["A"]


def test_drawers_are_listed_in_the_order_added():
    v = SeedVault()
    for name in ["top", "middle", "bottom"]:
        v.add_drawer(name)
    assert v.get_drawers() == ["top", "middle", "bottom"]


def test_adding_a_name_in_use_is_rejected(vault):
    before = state(vault)
    with pytest.raises(VaultError):
        vault.add_drawer("A")
    assert state(vault) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda v: v.deposit("Z", "pea", 1),
        lambda v: v.transfer("pea", "A", "Z", 1),
        lambda v: v.transfer_all("Z", "B"),
        lambda v: v.transfer_all("A", "Z"),
        lambda v: v.retire_drawer("Z", "B"),
        lambda v: v.retire_drawer("A", "Z"),
        lambda v: v.get_count("Z", "pea"),
    ],
)
def test_drawers_that_were_never_added_raise_key_error(vault, call):
    before = state(vault)
    with pytest.raises(KeyError):
        call(vault)
    assert state(vault) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda v: v.deposit("C", "pea", 1),
        lambda v: v.transfer("pea", "A", "C", 1),
        lambda v: v.transfer_all("C", "A"),
        lambda v: v.transfer_all("A", "C"),
        lambda v: v.retire_drawer("C", "A"),
        lambda v: v.retire_drawer("A", "C"),
        lambda v: v.get_count("C", "pea"),
    ],
)
def test_a_retired_drawer_is_not_in_use(vault, call):
    vault.retire_drawer("C", "B")  # C is empty
    before = state(vault)
    with pytest.raises(KeyError):
        call(vault)
    assert state(vault) == before


# --- deposit and transfer -----------------------------------------------------


def test_deposits_add_up(vault):
    vault.deposit("A", "pea", 3)
    vault.deposit("B", "pea", 1)
    assert vault.get_count("A", "pea") == 8
    assert vault.get_count("B", "pea") == 1
    assert vault.get_count("A", "bean") == 2


@pytest.mark.parametrize("count", [0, -3])
def test_deposits_of_0_or_less_are_rejected(vault, count):
    before = state(vault)
    with pytest.raises(ValueError):
        vault.deposit("A", "pea", count)
    assert state(vault) == before


def test_transfer_moves_packets_of_one_variety(vault):
    vault.deposit("B", "pea", 1)
    vault.transfer("pea", "A", "B", 4)
    assert vault.get_count("A", "pea") == 1
    assert vault.get_count("B", "pea") == 5
    assert vault.get_count("A", "bean") == 2
    assert vault.get_count("B", "bean") == 0


def test_every_packet_of_a_variety_can_be_transferred(vault):
    vault.transfer("bean", "A", "C", 2)
    assert vault.get_count("A", "bean") == 0
    assert vault.get_count("C", "bean") == 2
    vault.transfer("bean", "C", "A", 2)
    assert vault.get_count("A", "bean") == 2
    assert vault.get_count("C", "bean") == 0


def test_transferring_more_than_there_are_raises_and_changes_nothing(vault):
    before = state(vault)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer("bean", "A", "B", 3)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer("pea", "B", "A", 1)
    assert state(vault) == before


def test_transferring_a_variety_the_drawer_never_had_raises(vault):
    before = state(vault)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer("rye", "A", "B", 1)
    assert state(vault) == before


# --- transfer_all ---------------------------------------------------------------


def test_transfer_all_moves_every_variety(vault):
    vault.deposit("B", "corn", 1)
    vault.deposit("B", "rye", 3)
    assert vault.transfer_all("A", "B") == 11
    assert state(vault) == [
        ("A", [0, 0, 0, 0, 0]),
        ("B", [2, 5, 0, 5, 3]),
        ("C", [0, 0, 0, 0, 0]),
    ]


def test_transfer_all_into_an_empty_drawer(vault):
    assert vault.transfer_all("A", "C") == 11
    assert vault.get_count("C", "pea") == 5
    assert vault.get_count("C", "corn") == 4
    assert vault.get_count("A", "pea") == 0


def test_transfer_all_from_an_empty_drawer_moves_nothing(vault):
    before = state(vault)
    assert vault.transfer_all("C", "A") == 0
    assert state(vault) == before


def test_a_drawer_emptied_by_transfer_all_can_be_used_again(vault):
    vault.transfer_all("A", "B")
    vault.deposit("A", "oat", 2)
    vault.transfer("pea", "B", "A", 1)
    assert vault.get_count("A", "oat") == 2
    assert vault.get_count("A", "pea") == 1
    assert vault.get_drawers() == ["A", "B", "C"]


# --- retire_drawer --------------------------------------------------------------


def test_retire_drawer_moves_every_packet_and_removes_it(vault):
    vault.deposit("C", "bean", 1)
    assert vault.retire_drawer("A", "C") == 11
    assert vault.get_drawers() == ["B", "C"]
    assert vault.get_count("C", "bean") == 3
    assert vault.get_count("C", "pea") == 5
    assert vault.get_count("C", "corn") == 4


def test_retiring_an_empty_drawer_moves_nothing(vault):
    assert vault.retire_drawer("B", "A") == 0
    assert vault.get_drawers() == ["A", "C"]
    assert vault.get_count("A", "pea") == 5


def test_the_other_drawers_keep_their_order_after_a_retire(vault):
    vault.add_drawer("D")
    vault.retire_drawer("B", "D")
    assert vault.get_drawers() == ["A", "C", "D"]
    vault.retire_drawer("A", "D")
    assert vault.get_drawers() == ["C", "D"]
    assert vault.get_count("D", "pea") == 5


def test_a_drawer_that_received_a_retired_drawer_works_as_before(vault):
    vault.retire_drawer("A", "B")
    vault.transfer("pea", "B", "C", 3)
    assert vault.transfer_all("B", "C") == 8
    assert vault.get_count("C", "pea") == 5
    assert vault.get_count("B", "corn") == 0


# --- general ------------------------------------------------------------------


def test_not_enough_seeds_is_a_vault_error():
    assert issubclass(NotEnoughSeeds, VaultError)


def test_vaults_do_not_share_drawers():
    first, second = SeedVault(), SeedVault()
    first.add_drawer("A")
    first.deposit("A", "pea", 3)
    assert second.get_drawers() == []
    second.add_drawer("A")
    assert second.get_count("A", "pea") == 0
