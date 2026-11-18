"""Public checks for the c_transfer change (moving several runners at once).
Shown to the editor, never to the writer.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/public/test_transfer_public.py
"""

import pytest
from relay import RelayMeet


@pytest.fixture
def meet():
    m = RelayMeet()
    m.add_team("hawks")
    m.add_team("owls")
    for runner in ["ana", "ben", "cy"]:
        m.add_runner("hawks", runner)
    return m


def test_move_runners_moves_them_in_list_order(meet):
    assert meet.move_runners(["cy", "ana"], "owls") == 2
    assert meet.get_lineup("owls") == ["cy", "ana"]
    assert meet.get_lineup("hawks") == ["ben"]


def test_a_list_with_an_unknown_runner_moves_nobody(meet):
    with pytest.raises(KeyError):
        meet.move_runners(["ana", "zed"], "owls")
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]
    assert meet.get_lineup("owls") == []
