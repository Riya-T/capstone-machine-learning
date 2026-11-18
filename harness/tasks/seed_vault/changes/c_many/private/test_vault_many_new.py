"""Hidden tests for the c_many change (several transfers in one call). Never
shown to the writer or the editor.

Usage (with vault.py importable, e.g. in the sandbox):
    python -m pytest changes/c_many/private/test_vault_many_new.py
"""

import pytest
from vault import NotEnoughSeeds, SeedVault

VARIETIES = ["bean", "corn", "oat", "pea", "rye"]


def make_vault():
    v = SeedVault()
    for name in ["A", "B", "C"]:
        v.add_drawer(name)
    v.deposit("A", "pea", 5)
    v.deposit("A", "bean", 2)
    v.deposit("A", "corn", 4)
    v.deposit("B", "rye", 3)
    return v


@pytest.fixture
def vault():
    return make_vault()


def state(v):
    return [(d, [v.get_count(d, s) for s in VARIETIES]) for d in v.get_drawers()]


# --- successful calls -----------------------------------------------------------


def test_every_transfer_is_made_and_the_total_returned(vault):
    moved = vault.transfer_many(
        [("pea", "A", "B", 2), ("corn", "A", "C", 4), ("rye", "B", "C", 1)]
    )
    assert moved == 7
    assert state(vault) == [
        ("A", [2, 0, 0, 3, 0]),
        ("B", [0, 0, 0, 2, 2]),
        ("C", [0, 4, 0, 0, 1]),
    ]


def test_a_single_transfer_works_like_transfer(vault):
    other = make_vault()
    assert vault.transfer_many([("bean", "A", "B", 2)]) == 2
    other.transfer("bean", "A", "B", 2)
    assert state(vault) == state(other)


def test_the_result_matches_one_transfer_at_a_time(vault):
    transfers = [("bean", "A", "C", 2), ("pea", "A", "C", 1), ("bean", "C", "B", 1)]
    other = make_vault()
    assert vault.transfer_many(transfers) == 4
    for t in transfers:
        other.transfer(*t)
    assert state(vault) == state(other)


def test_a_drawer_may_pass_on_packets_it_just_received(vault):
    assert vault.transfer_many([("pea", "A", "C", 5), ("pea", "C", "B", 3)]) == 8
    assert vault.get_count("A", "pea") == 0
    assert vault.get_count("C", "pea") == 2
    assert vault.get_count("B", "pea") == 3


def test_the_same_variety_can_be_moved_more_than_once(vault):
    assert vault.transfer_many([("corn", "A", "B", 1), ("corn", "A", "B", 3)]) == 4
    assert vault.get_count("B", "corn") == 4
    assert vault.get_count("A", "corn") == 0


def test_an_empty_list_changes_nothing(vault):
    before = state(vault)
    assert vault.transfer_many([]) == 0
    assert state(vault) == before


def test_other_calls_work_after_transfer_many(vault):
    vault.transfer_many([("pea", "A", "B", 5)])
    vault.deposit("A", "pea", 1)
    assert vault.get_count("A", "pea") == 1
    assert vault.retire_drawer("B", "C") == 8
    assert vault.get_count("C", "pea") == 5
    assert vault.get_drawers() == ["A", "C"]


# --- failed calls ---------------------------------------------------------------


@pytest.mark.parametrize(
    "bad, error",
    [
        (("pea", "A", "B", 9), NotEnoughSeeds),
        (("oat", "A", "B", 1), NotEnoughSeeds),
        (("pea", "A", "Z", 1), KeyError),
    ],
    ids=["too_many", "absent_variety", "unknown_drawer"],
)
def test_a_failing_last_transfer_cancels_every_transfer(vault, bad, error):
    before = state(vault)
    with pytest.raises(error):
        vault.transfer_many([("bean", "A", "C", 2), ("rye", "B", "A", 3), bad])
    assert state(vault) == before


def test_a_failing_first_transfer_changes_nothing(vault):
    before = state(vault)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer_many([("rye", "C", "A", 1), ("pea", "A", "B", 1)])
    assert state(vault) == before


def test_packets_can_only_be_passed_on_after_they_arrive(vault):
    before = state(vault)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer_many([("pea", "C", "B", 3), ("pea", "A", "C", 5)])
    assert state(vault) == before


def test_a_transfer_cannot_use_packets_an_earlier_one_took_away(vault):
    before = state(vault)
    with pytest.raises(NotEnoughSeeds):
        vault.transfer_many([("corn", "A", "B", 3), ("corn", "A", "C", 2)])
    assert state(vault) == before


def test_the_first_failing_transfer_decides_the_error(vault):
    with pytest.raises(KeyError):
        vault.transfer_many([("pea", "A", "B", 1), ("pea", "A", "Z", 1), ("pea", "A", "B", 99)])
    with pytest.raises(NotEnoughSeeds):
        vault.transfer_many([("pea", "A", "B", 99), ("pea", "A", "Z", 1)])
    assert vault.get_count("A", "pea") == 5


def test_a_cancelled_call_can_be_retried(vault):
    with pytest.raises(NotEnoughSeeds):
        vault.transfer_many([("bean", "A", "B", 2), ("oat", "C", "A", 1)])
    vault.deposit("C", "oat", 1)
    assert vault.transfer_many([("bean", "A", "B", 2), ("oat", "C", "A", 1)]) == 3
    assert vault.get_count("A", "oat") == 1
    assert vault.get_count("B", "bean") == 2
    assert vault.get_count("A", "bean") == 0
