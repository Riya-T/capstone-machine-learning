"""Public checks for the c_versioned_commands change (version checks on
driving). Shown to the editor, never to the writer.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versioned_commands/public/test_versioned_commands_public.py
"""

import pytest
from rovers import RoverFleet, VersionConflict


def test_version_goes_up_once_per_drive():
    f = RoverFleet()
    f.land("scout", 0, 0, "north")
    assert f.get_version("scout") == 1
    f.drive("scout", "FFRF")
    assert f.get_version("scout") == 2
    f.drive("scout", "F", expected_version=2)
    assert f.get_version("scout") == 3


def test_version_outdated_drive_is_refused():
    f = RoverFleet()
    f.land("scout", 0, 0, "north")
    f.drive("scout", "F")
    with pytest.raises(VersionConflict):
        f.drive("scout", "F", expected_version=1)
    assert f.get_location("scout") == (0, 1, "north")
