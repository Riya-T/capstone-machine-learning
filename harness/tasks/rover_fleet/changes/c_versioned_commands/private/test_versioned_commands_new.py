"""Hidden tests for the c_versioned_commands change (version checks on
driving). Never shown to the writer or the editor.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versioned_commands/private/test_versioned_commands_new.py
"""

import pytest
from rovers import RoverError, RoverFleet, VersionConflict


@pytest.fixture
def fleet():
    f = RoverFleet()
    f.land("scout", 2, 2, "north")
    f.land("mole", 2, 4, "south")
    return f


def state(f):
    return [
        (r, f.get_location(r), f.get_odometer(r), f.get_version(r)) for r in f.get_rovers()
    ]


def test_version_starts_at_one_for_every_rover(fleet):
    assert fleet.get_version("scout") == 1
    assert fleet.get_version("mole") == 1


def test_version_counts_drive_calls_not_commands(fleet):
    fleet.drive("scout", "RFFFLF")
    fleet.drive("scout", "B")
    assert fleet.get_version("scout") == 3
    assert fleet.get_version("mole") == 1


def test_version_goes_up_for_a_drive_of_only_turns(fleet):
    fleet.drive("mole", "LL")
    assert fleet.get_version("mole") == 2


def test_version_stays_when_nothing_is_carried_out(fleet):
    assert fleet.drive("scout", "") == 0
    assert fleet.drive("scout", "FF") == 1  # mole blocks the second move
    assert fleet.get_version("scout") == 2
    assert fleet.drive("scout", "FL") == 0  # blocked at once
    assert fleet.get_version("scout") == 2
    assert fleet.drive("mole", "FR") == 0
    assert fleet.get_version("mole") == 1


def test_version_matching_expected_version_drives(fleet):
    assert fleet.drive("scout", "R", expected_version=1) == 1
    assert fleet.drive("scout", "F", expected_version=2) == 1
    assert fleet.get_location("scout") == (3, 2, "east")
    assert fleet.get_version("scout") == 3


@pytest.mark.parametrize("version", [0, 2, 5])
def test_version_conflict_changes_nothing(fleet, version):
    before = state(fleet)
    with pytest.raises(VersionConflict):
        fleet.drive("scout", "RF", expected_version=version)
    assert state(fleet) == before


def test_version_conflict_on_an_empty_drive(fleet):
    with pytest.raises(VersionConflict):
        fleet.drive("scout", "", expected_version=7)


def test_version_conflict_is_a_rover_error():
    assert issubclass(VersionConflict, RoverError)


def test_version_after_a_conflict_is_still_usable(fleet):
    fleet.drive("scout", "L")
    with pytest.raises(VersionConflict):
        fleet.drive("scout", "F", expected_version=1)
    fleet.drive("scout", "F", expected_version=2)
    assert fleet.get_location("scout") == (1, 2, "west")


def test_version_error_order(fleet):
    with pytest.raises(KeyError):
        fleet.drive("digger", "x", expected_version=9)
    with pytest.raises(ValueError):
        fleet.drive("scout", "x", expected_version=9)
    assert state(fleet)[0] == ("scout", (2, 2, "north"), 0, 1)


def test_version_of_an_unknown_rover_raises_key_error(fleet):
    with pytest.raises(KeyError):
        fleet.get_version("digger")
    with pytest.raises(KeyError):
        fleet.get_version(None)


def test_version_stays_after_invalid_commands(fleet):
    with pytest.raises(ValueError):
        fleet.drive("scout", "FFz")
    assert fleet.get_version("scout") == 1
