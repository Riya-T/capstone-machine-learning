"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from freezers import FreezerError, Freezers


def test_undo_takes_back_a_store():
    lab = Freezers()
    lab.add_freezer("A")
    lab.store("A", "s1")
    lab.store("A", "s2")
    lab.undo()
    assert lab.get_samples("A") == ["s1"]
    with pytest.raises(KeyError):
        lab.find("s2")


def test_undoing_a_discard_puts_the_sample_back_in_its_place():
    lab = Freezers()
    lab.add_freezer("A")
    for sample_id in ["s1", "s2", "s3"]:
        lab.store("A", sample_id)
    lab.discard("s2")
    lab.undo()
    assert lab.get_samples("A") == ["s1", "s2", "s3"]
    assert lab.find("s2") == "A"


def test_undo_with_nothing_to_undo_raises_freezer_error():
    lab = Freezers()
    with pytest.raises(FreezerError):
        lab.undo()
