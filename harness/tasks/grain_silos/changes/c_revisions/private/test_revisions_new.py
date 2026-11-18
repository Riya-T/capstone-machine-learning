"""Hidden tests for the c_revisions change (concurrency_control). Never shown
to the writer or the editor.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_revisions/private/test_revisions_new.py
"""

import pytest
from silos import RevisionConflict, SiloError, Silos


@pytest.fixture
def silos():
    s = Silos()
    for name in ["north", "south", "east"]:
        s.add_silo(name)
    s.load("north", "wheat", 30)
    s.load("north", "barley", 20)
    s.load("south", "rye", 40)
    return s  # revision 6


def state(s):
    return [(n, [(g, s.get_tonnes(n, g)) for g in s.get_grains(n)]) for n in s.get_silos()]


CHANGES = [
    lambda s, **kw: s.add_silo("west", **kw),
    lambda s, **kw: s.load("east", "corn", 5, **kw),
    lambda s, **kw: s.unload("north", "wheat", 10, **kw),
    lambda s, **kw: s.blend_into("north", "south", **kw),
    lambda s, **kw: s.demolish_silo("south", "east", **kw),
]
IDS = ["add_silo", "load", "unload", "blend_into", "demolish_silo"]


# --- counting -----------------------------------------------------------------


def test_a_new_object_is_at_revision_0():
    assert Silos().get_revision() == 0


def test_each_successful_change_adds_1(silos):
    assert silos.get_revision() == 6


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_every_kind_of_change_adds_exactly_1(silos, call):
    call(silos)
    assert silos.get_revision() == 7


def test_moving_several_grains_still_adds_1(silos):
    assert silos.blend_into("north", "east") == 50
    assert silos.get_revision() == 7
    assert silos.demolish_silo("east", "south") == 50
    assert silos.get_revision() == 8


def test_moving_no_grain_still_adds_1(silos):
    assert silos.blend_into("east", "north") == 0
    assert silos.get_revision() == 7
    assert silos.demolish_silo("east", "north") == 0
    assert silos.get_revision() == 8


def test_failed_calls_leave_the_revision_unchanged(silos):
    for call in (
        lambda: silos.add_silo("north"),
        lambda: silos.load("west", "wheat", 1),
        lambda: silos.load("north", "wheat", 0),
        lambda: silos.unload("north", "wheat", 99),
        lambda: silos.blend_into("north", "north"),
        lambda: silos.demolish_silo("west", "north"),
    ):
        with pytest.raises((KeyError, ValueError, SiloError)):
            call()
    assert silos.get_revision() == 6


def test_get_calls_leave_the_revision_unchanged(silos):
    silos.get_tonnes("north", "wheat")
    silos.get_grains("north")
    silos.get_silos()
    silos.get_revision()
    assert silos.get_revision() == 6


def test_objects_count_their_own_revisions(silos):
    other = Silos()
    other.add_silo("north")
    assert other.get_revision() == 1
    assert silos.get_revision() == 6


# --- expected_revision ------------------------------------------------------------


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_the_current_revision_is_accepted(silos, call):
    call(silos, expected_revision=6)
    assert silos.get_revision() == 7


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
@pytest.mark.parametrize("stale", [5, 7, 0])
def test_any_other_revision_is_rejected_and_changes_nothing(silos, call, stale):
    before = state(silos)
    with pytest.raises(RevisionConflict):
        call(silos, expected_revision=stale)
    assert state(silos) == before
    assert silos.get_revision() == 6


def test_none_means_no_check(silos):
    silos.load("east", "corn", 5, expected_revision=None)
    assert silos.get_tonnes("east", "corn") == 5
    assert silos.get_revision() == 7


def test_two_offices_editing_from_the_same_revision(silos):
    seen = silos.get_revision()
    silos.unload("north", "wheat", 10, expected_revision=seen)
    with pytest.raises(RevisionConflict):
        silos.blend_into("north", "east", expected_revision=seen)
    assert silos.get_grains("east") == []
    silos.blend_into("north", "east", expected_revision=silos.get_revision())
    assert silos.get_tonnes("east", "wheat") == 20
    assert silos.get_revision() == 8


def test_revision_conflict_is_a_silo_error():
    assert issubclass(RevisionConflict, SiloError)
