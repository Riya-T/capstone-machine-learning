"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from relay import RelayError, RelayMeet


@pytest.fixture
def meet():
    m = RelayMeet()
    m.add_team("hawks")
    m.add_team("owls")
    return m


def test_undo_takes_back_the_last_runner_added(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    meet.undo()
    assert meet.get_lineup("hawks") == ["ana"]
    meet.undo()
    assert meet.get_lineup("hawks") == []


def test_undo_takes_back_a_move(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    meet.move_runner("ben", "owls")
    meet.undo()
    assert meet.get_lineup("hawks") == ["ana", "ben"]
    assert meet.get_lineup("owls") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(RelayError):
        RelayMeet().undo()
