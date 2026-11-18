"""Public checks for the c_lookup change (one species across the garden).
Shown to the editor, never to the writer.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/public/test_lookup_public.py
"""

import pytest
from garden import Garden


@pytest.fixture
def garden():
    g = Garden()
    g.add_bed("north")
    g.add_bed("south")
    g.plant("north", "rose", 3)
    g.plant("south", "rose", 2)
    g.plant("south", "fern", 1)
    return g


def test_get_beds_with_lists_the_beds_in_bed_order(garden):
    assert garden.get_beds_with("rose") == ["north", "south"]
    assert garden.get_beds_with("fern") == ["south"]
    assert garden.get_beds_with("mint") == []


def test_get_total_adds_up_every_bed(garden):
    assert garden.get_total("rose") == 5
    assert garden.get_total("mint") == 0
