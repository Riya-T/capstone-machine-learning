"""Public checks for freezers.py.

Usage (with freezers.py importable, e.g. in the sandbox):
    python -m pytest public/test_freezers_public.py
"""

import pytest
from freezers import FreezerError, Freezers


@pytest.fixture
def lab():
    lab = Freezers()
    lab.add_freezer("A")
    lab.add_freezer("B")
    return lab


def test_stored_samples_can_be_found_and_moved(lab):
    lab.store("A", "s1")
    lab.store("A", "s2")
    assert lab.find("s1") == "A"
    assert lab.get_samples("A") == ["s1", "s2"]
    lab.move("s1", "B")
    assert lab.find("s1") == "B"
    assert lab.get_samples("A") == ["s2"]
    assert lab.get_samples("B") == ["s1"]
    assert lab.get_freezers() == ["A", "B"]


def test_move_all_keeps_the_order_and_goes_after_the_samples_there(lab):
    for sample_id in ["s1", "s2", "s3"]:
        lab.store("A", sample_id)
    lab.store("B", "s4")
    assert lab.move_all("A", "B") == 3
    assert lab.get_samples("B") == ["s4", "s1", "s2", "s3"]
    assert lab.get_samples("A") == []
    assert lab.find("s1") == "B"
    assert lab.get_freezers() == ["A", "B"]


def test_remove_freezer_moves_its_samples_then_removes_it(lab):
    lab.store("A", "s1")
    lab.store("A", "s2")
    lab.store("B", "s3")
    assert lab.remove_freezer("A", "B") == 2
    assert lab.get_freezers() == ["B"]
    assert lab.get_samples("B") == ["s3", "s1", "s2"]
    with pytest.raises(KeyError):
        lab.get_samples("A")


def test_an_empty_freezer_is_removed_too_and_its_id_can_come_back(lab):
    assert lab.remove_freezer("A", "B") == 0
    assert lab.get_freezers() == ["B"]
    lab.add_freezer("A")
    assert lab.get_freezers() == ["B", "A"]
    assert lab.get_samples("A") == []


def test_a_sample_id_can_only_be_stored_once(lab):
    lab.store("A", "s1")
    with pytest.raises(FreezerError):
        lab.store("B", "s1")
    assert lab.find("s1") == "A"
    assert lab.get_samples("B") == []


def test_a_freezer_not_in_use_raises_key_error(lab):
    with pytest.raises(KeyError):
        lab.get_samples("Z")
    with pytest.raises(KeyError):
        lab.store("Z", "s1")
    assert lab.get_samples("A") == []
