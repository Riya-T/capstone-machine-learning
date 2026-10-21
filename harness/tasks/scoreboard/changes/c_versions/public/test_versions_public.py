"""Public checks for the c_versions change (version numbers per team). Shown
to the editor, never to the writer.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from scoreboard import Scoreboard, VersionConflict


def test_versions_count_up_with_each_score():
    sb = Scoreboard()
    sb.add_team("lions")
    assert sb.get_version("lions") == 1
    sb.score("lions", "try")
    sb.score("lions", "conversion", expected_version=2)
    assert sb.get_version("lions") == 3


def test_versions_a_stale_version_is_refused():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.score("lions", "try")
    with pytest.raises(VersionConflict):
        sb.score("lions", "try", expected_version=1)
    assert sb.get_score("lions") == 5
    assert sb.get_version("lions") == 2
