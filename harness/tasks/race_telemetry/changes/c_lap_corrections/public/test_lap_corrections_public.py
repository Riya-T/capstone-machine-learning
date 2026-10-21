"""Public checks for the c_lap_corrections change (versioned lap
corrections). Shown to the editor, never to the writer.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lap_corrections/public/test_lap_corrections_public.py
"""

import pytest
from telemetry import RaceTelemetry, VersionConflict


@pytest.fixture
def tel():
    t = RaceTelemetry()
    t.add_car("red")
    t.add_race("spa", 2)
    return t


def test_correction_replaces_a_lap_and_bumps_the_version(tel):
    assert tel.get_version("spa") == 1
    tel.record_lap("spa", "red", 90000)
    tel.record_lap("spa", "red", 95000)
    tel.correct_lap("spa", "red", 2, 91000)
    assert tel.get_lap_times("spa", "red") == [90000, 91000]
    assert tel.get_version("spa") == 4


def test_correction_with_an_outdated_version_is_refused(tel):
    tel.record_lap("spa", "red", 90000, expected_version=1)
    with pytest.raises(VersionConflict):
        tel.correct_lap("spa", "red", 1, 89000, expected_version=1)
    assert tel.get_lap_times("spa", "red") == [90000]
    assert tel.get_version("spa") == 2
