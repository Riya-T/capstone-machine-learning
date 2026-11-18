"""Public checks for the c_herb_query change (looking up a herb across
racks). Shown to the editor, never to the writer.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest changes/c_herb_query/public/test_herb_query_public.py
"""

import pytest
from drying import DryingRoom


@pytest.fixture
def room():
    r = DryingRoom()
    for name in ["north", "south", "east"]:
        r.add_rack(name)
    r.hang("east", "sage", 2)
    r.hang("north", "sage", 3)
    r.hang("south", "mint", 1)
    return r


def test_get_total_adds_up_every_rack(room):
    assert room.get_total("sage") == 5
    assert room.get_total("mint") == 1


def test_get_racks_with_follows_the_rack_order(room):
    assert room.get_racks_with("sage") == ["north", "east"]
    assert room.get_racks_with("dill") == []
